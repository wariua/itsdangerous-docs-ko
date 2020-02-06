import hashlib

from ._compat import text_type
from ._json import json
from .encoding import want_bytes
from .exc import BadPayload
from .exc import BadSignature
from .signer import Signer


def is_text_serializer(serializer):
    """Checks whether a serializer generates text or binary."""
    return isinstance(serializer.dumps({}), text_type)


class Serializer(object):
    """이 클래스는 signer 위에서 직렬화 인터페이스를 제공한다.
    json/pickle이나 여타 모듈들과 비슷한 API를 제공하지만 내부
    구조는 다르게 돼 있다. 기반 파싱 및 적재 구현을 바꾸고
    싶다면 :meth:`load_payload` 및 :meth:`dump_payload` 함수를
    오버라이드 해야 한다.

    이 구현에서는 사용 가능한 경우 simplejson을 써서 dump와
    load를 한다. 사용 가능하지 않은 경우에는 표준 라이브러리의
    json 모듈로 대신한다.

    :class:`.Signer`\를 교체하거나 동작을 수정하려고 하는 경우에
    이 클래스의 서브클래스를 만들 필요가 없다. 생성자에 다른
    클래스를 주고 거기 전달할 키워드 인자들을 딕셔너리로
    주면 된다.

    .. code-block:: python

        s = Serializer(signer_kwargs={'key_derivation': 'hmac'})

    서명 매개변수를 업그레이드 하면서 사용 중인 기존 서명들이
    무효가 되지 않게 하고 싶을 수 있다. 현재 서명 방식으로
    서명 검증이 실패할 때 시도할 대체 서명 방식을 줄 수 있다.

    ``fallback_signers``\에 리스트를 줘서 대체 서명 방식들을
    지정할 수 있다. 각 항목은 (``signer_kwargs``, ``salt``,
    ``secret_key``\로 만든) signer 인스턴스거나, 튜플
    ``(signer_class, signer_kwargs)``\이거나,
    ``signer_kwargs``\의 딕셔너리일 수 있다.

    예를 들어 다음은 SHA-512로 서명하고 SHA-512나 SHA1 중 하나로
    서명을 없애는 직렬화 객체다.

    .. code-block:: python

        s = Serializer(
            signer_kwargs={"digest_method": hashlib.sha512},
            fallback_signers=[{"digest_method": hashlib.sha1}]
        )

    .. versionchanged:: 0.14:
        생성자에 매개변수 ``signer``\와 ``signer_kwargs``\가
        추가됨.

    .. versionchanged:: 1.1.0:
        ``fallback_signers`` 지원이 추가되고 실패 시 기본적으로
        SHA-512를 대신 쓰도록 구성됨. 이 대체 동작은 기본적으로
        SHA-512를 썼던 1.0.0 릴리스를 썼던 사용자들을 위한 것이다.
    """

    #: 생성자에 직렬화 모듈 내지 클래스를 주지 않으면
    #: 이걸 쓴다. 현재 기본은 :mod:`json`\이다.
    default_serializer = json

    #: 이 직렬화에서 사용 중인 기본 :class:`Signer` 클래스.
    #:
    #: .. versionadded:: 0.14
    default_signer = Signer

    #: 기본 대체 서명 방식.
    default_fallback_signers = [{"digest_method": hashlib.sha512}]

    def __init__(
        self,
        secret_key,
        salt=b"itsdangerous",
        serializer=None,
        serializer_kwargs=None,
        signer=None,
        signer_kwargs=None,
        fallback_signers=None,
    ):
        self.secret_key = want_bytes(secret_key)
        self.salt = want_bytes(salt)
        if serializer is None:
            serializer = self.default_serializer
        self.serializer = serializer
        self.is_text_serializer = is_text_serializer(serializer)
        if signer is None:
            signer = self.default_signer
        self.signer = signer
        self.signer_kwargs = signer_kwargs or {}
        if fallback_signers is None:
            fallback_signers = list(self.default_fallback_signers or ())
        self.fallback_signers = fallback_signers
        self.serializer_kwargs = serializer_kwargs or {}

    def load_payload(self, payload, serializer=None):
        """인코딩 된 객체를 적재한다. 페이로드가 유효하지 않으면
        함수에서 :class:`.BadPayload`\를 던진다. ``serializer``
        매개변수를 이용하면 클래스에 저장된 것과 다른 직렬화
        방식을 쓸 수 있다. 인코딩 된 ``payload``\는 항상
        bytes여야 한다.
        """
        if serializer is None:
            serializer = self.serializer
            is_text = self.is_text_serializer
        else:
            is_text = is_text_serializer(serializer)
        try:
            if is_text:
                payload = payload.decode("utf-8")
            return serializer.loads(payload)
        except Exception as e:
            raise BadPayload(
                "Could not load the payload because an exception"
                " occurred on unserializing the data.",
                original_error=e,
            )

    def dump_payload(self, obj):
        """인코딩 된 객체를 덤프 한다. 반환 값은 항상 bytes다.
        내부 직렬화 모듈에서 텍스트를 반환하면 UTF-8으로
        인코딩 된다.
        """
        return want_bytes(self.serializer.dumps(obj, **self.serializer_kwargs))

    def make_signer(self, salt=None):
        """사용할 signer 인스턴스를 새로 만든다. 기본 구현에서는
        기반 클래스 :class:`.Signer`\를 쓴다.
        """
        if salt is None:
            salt = self.salt
        return self.signer(self.secret_key, salt=salt, **self.signer_kwargs)

    def iter_unsigners(self, salt=None):
        """서명 검증에 시도할 서명 방식들을 모두 순회한다. 설정한
        서명 방식으로 시작해서 ``fallback_signers``\에 지정한
        서명 방식 각각을 만든다.
        """
        if salt is None:
            salt = self.salt
        yield self.make_signer(salt)
        for fallback in self.fallback_signers:
            if type(fallback) is dict:
                kwargs = fallback
                fallback = self.signer
            elif type(fallback) is tuple:
                fallback, kwargs = fallback
            else:
                kwargs = self.signer_kwargs
            yield fallback(self.secret_key, salt=salt, **kwargs)

    def dumps(self, obj, salt=None):
        """내부 직렬화 모듈로 직렬화 한 서명된 문자열을
        반환한다. 내부 직렬화 모듈의 형식에 따라서 반환 값이
        바이트열이나 유니코드열이다.
        """
        payload = want_bytes(self.dump_payload(obj))
        rv = self.make_signer(salt).sign(payload)
        if self.is_text_serializer:
            rv = rv.decode("utf-8")
        return rv

    def dump(self, obj, f, salt=None):
        """:meth:`dumps`\와 비슷하되 파일로 덤프 한다. 파일
        핸들이 내부 직렬화 모듈과 호환돼야 한다.
        """
        f.write(self.dumps(obj, salt))

    def loads(self, s, salt=None):
        """:meth:`dumps`\의 반대. 서명 검증이 실패하면
        :exc:`.BadSignature`\를 던진다.
        """
        s = want_bytes(s)
        last_exception = None
        for signer in self.iter_unsigners(salt):
            try:
                return self.load_payload(signer.unsign(s))
            except BadSignature as err:
                last_exception = err
        raise last_exception

    def load(self, f, salt=None):
        """:meth:`loads`\와 비슷하되 파일로부터 적재한다."""
        return self.loads(f.read(), salt)

    def loads_unsafe(self, s, salt=None):
        """:meth:`loads`\와 비슷하되 서명 검증이 빠져 있다.
        직렬화 모듈 동작 방식에 따라선 아주 위험한 동작일 수도
        있다. 반환 값이 단순 페이로드가 아니라 ``(signature_valid,
        payload)``\다. 첫 항목은 서명이 유효한지 여부를 나타내는
        불리언이다. 이 함수는 절대 실패하지 않는다.

        디버깅용으로만, 그리고 직렬화 모듈에 취약성이 없다는 게
        확실할 때만 써야 한다. (예를 들어 pickle 직렬화 모듈에는
        쓰지 말아야 한다.)

        .. versionadded:: 0.15
        """
        return self._loads_unsafe_impl(s, salt)

    def _loads_unsafe_impl(self, s, salt, load_kwargs=None, load_payload_kwargs=None):
        """Low level helper function to implement :meth:`loads_unsafe`
        in serializer subclasses.
        """
        try:
            return True, self.loads(s, salt=salt, **(load_kwargs or {}))
        except BadSignature as e:
            if e.payload is None:
                return False, None
            try:
                return (
                    False,
                    self.load_payload(e.payload, **(load_payload_kwargs or {})),
                )
            except BadPayload:
                return False, None

    def load_unsafe(self, f, *args, **kwargs):
        """:meth:`loads_unsafe`\와 비슷하되 파일로부터 적재한다.

        .. versionadded:: 0.15
        """
        return self.loads_unsafe(f.read(), *args, **kwargs)
