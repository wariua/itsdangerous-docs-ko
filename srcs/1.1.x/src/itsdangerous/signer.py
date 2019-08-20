import hashlib
import hmac

from ._compat import constant_time_compare
from .encoding import _base64_alphabet
from .encoding import base64_decode
from .encoding import base64_encode
from .encoding import want_bytes
from .exc import BadSignature


class SigningAlgorithm(object):
    """Subclasses must implement :meth:`get_signature` to provide
    signature generation functionality.
    """

    def get_signature(self, key, value):
        """Returns the signature for the given key and value."""
        raise NotImplementedError()

    def verify_signature(self, key, value, sig):
        """Verifies the given signature matches the expected
        signature.
        """
        return constant_time_compare(sig, self.get_signature(key, value))


class NoneAlgorithm(SigningAlgorithm):
    """어떤 서명도 수행하지 않고 빈 서명을 반환하는 알고리듬을
    제공한다.
    """

    def get_signature(self, key, value):
        return b""


class HMACAlgorithm(SigningAlgorithm):
    """HMAC을 이용하는 서명 생성 방식을 제공한다."""

    #: The digest method to use with the MAC algorithm. This defaults to
    #: SHA1, but can be changed to any other function in the hashlib
    #: module.
    default_digest_method = staticmethod(hashlib.sha1)

    def __init__(self, digest_method=None):
        if digest_method is None:
            digest_method = self.default_digest_method
        self.digest_method = digest_method

    def get_signature(self, key, value):
        mac = hmac.new(key, msg=value, digestmod=self.digest_method)
        return mac.digest()


class Signer(object):
    """이 클래스로 바이트들에 서명을 하거나 받은 서명을 검증할
    수 있다.

    솔트를 사용해 일종의 해시 네임스페이스를 만들어서 서명된 문자열이
    해당 네임스페이스에서만 유효하게 할 수 있다. 솔트를 기본값 그대로
    두거나 응용의 한 부분에서 서명한 값이 다른 부분에서 어떤 의미가
    있을 때 두 곳에서 같은 솔트 값을 재사용하는 건 보안 위험 요소다.

    솔트의 역할이 뭐고 어떻게 활용할 수 있는지에 대한 예시는
    :ref:`the-salt` 참고.

    .. versionadded:: 0.14
        클래스 생성자 인자로 ``key_derivation`` 및
        ``digest_method`` 추가됨.

    .. versionadded:: 0.18
        클래스 생성자 인자로 ``algorithm`` 추가됨.
    """

    #: 서명에 사용할 다이제스트 메소드. 기본은 SHA1이지만
    #: hashlib 모듈의 다른 함수로 바꿀 수 있다.
    #:
    #: .. versionadded:: 0.14
    default_digest_method = staticmethod(hashlib.sha1)

    #: 키 유도 방식을 지정. 기본은 장고 스타일 접합이다.
    #: 가능한 값으로 ``concat``, ``django-concat``, ``hmac``\이
    #: 있다. 비밀키에 솔트를 추가해서 키를 유도하는 데 쓰인다.
    #:
    #: .. versionadded:: 0.14
    default_key_derivation = "django-concat"

    def __init__(
        self,
        secret_key,
        salt=None,
        sep=".",
        key_derivation=None,
        digest_method=None,
        algorithm=None,
    ):
        self.secret_key = want_bytes(secret_key)
        self.sep = want_bytes(sep)
        if self.sep in _base64_alphabet:
            raise ValueError(
                "The given separator cannot be used because it may be"
                " contained in the signature itself. Alphanumeric"
                " characters and `-_=` must not be used."
            )
        self.salt = "itsdangerous.Signer" if salt is None else salt
        if key_derivation is None:
            key_derivation = self.default_key_derivation
        self.key_derivation = key_derivation
        if digest_method is None:
            digest_method = self.default_digest_method
        self.digest_method = digest_method
        if algorithm is None:
            algorithm = HMACAlgorithm(self.digest_method)
        self.algorithm = algorithm

    def derive_key(self):
        """이 메소드를 호출해서 키를 유도한다. 여기의 기본 키 유도
        방식을 바꿀 수 있다. 키 유도는 짧은 패스워드로 복잡한 키를
        만드는 보안 수단이 아니다. 보안을 위해선 긴 난수 비밀키를
        사용해야 한다.
        """
        salt = want_bytes(self.salt)
        if self.key_derivation == "concat":
            return self.digest_method(salt + self.secret_key).digest()
        elif self.key_derivation == "django-concat":
            return self.digest_method(salt + b"signer" + self.secret_key).digest()
        elif self.key_derivation == "hmac":
            mac = hmac.new(self.secret_key, digestmod=self.digest_method)
            mac.update(salt)
            return mac.digest()
        elif self.key_derivation == "none":
            return self.secret_key
        else:
            raise TypeError("Unknown key derivation method")

    def get_signature(self, value):
        """값을 받아서 서명을 반환한다."""
        value = want_bytes(value)
        key = self.derive_key()
        sig = self.algorithm.get_signature(key, value)
        return base64_encode(sig)

    def sign(self, value):
        """문자열을 받아서 서명을 한다."""
        return want_bytes(value) + want_bytes(self.sep) + self.get_signature(value)

    def verify_signature(self, value, sig):
        """값을 받아서 서명을 검증한다."""
        key = self.derive_key()
        try:
            sig = base64_decode(sig)
        except Exception:
            return False
        return self.algorithm.verify_signature(key, value, sig)

    def unsign(self, signed_value):
        """문자열을 받아서 검증하고 서명을 없앤다."""
        signed_value = want_bytes(signed_value)
        sep = want_bytes(self.sep)
        if sep not in signed_value:
            raise BadSignature("No %r found in value" % self.sep)
        value, sig = signed_value.rsplit(sep, 1)
        if self.verify_signature(value, sig):
            return value
        raise BadSignature("Signature %r does not match" % sig, payload=value)

    def validate(self, signed_value):
        """서명된 값을 받아서 검증만 한다. 서명이 존재하고 유효하면
        ``True``\를 반환한다.
        """
        try:
            self.unsign(signed_value)
            return True
        except BadSignature:
            return False
