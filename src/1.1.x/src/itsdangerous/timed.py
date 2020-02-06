import time
from datetime import datetime

from ._compat import text_type
from .encoding import base64_decode
from .encoding import base64_encode
from .encoding import bytes_to_int
from .encoding import int_to_bytes
from .encoding import want_bytes
from .exc import BadSignature
from .exc import BadTimeSignature
from .exc import SignatureExpired
from .serializer import Serializer
from .signer import Signer


class TimestampSigner(Signer):
    """기본 :class:`.Signer`\처럼 동작하되 서명 시간까지
    기록하므로 서명을 만료되게 할 수 있다. 서명이 만료돼서
    서명 검증에 실패하면 :meth:`unsign` 메소드에서
    :exc:`.SignatureExpired`\를 던질 수 있다.
    """

    def get_timestamp(self):
        """현재 타임스탬프를 반환한다. 반드시 정수를 반환해야
        한다.
        """
        return int(time.time())

    def timestamp_to_datetime(self, ts):
        """:meth:`get_timestamp`\에서 얻은 타임스탬프를
        datetime 객체로 변환하는 데 사용.
        """
        return datetime.utcfromtimestamp(ts)

    def sign(self, value):
        """문자열을 받아서 서명을 하고 시간 정보를 덧붙인다."""
        value = want_bytes(value)
        timestamp = base64_encode(int_to_bytes(self.get_timestamp()))
        sep = want_bytes(self.sep)
        value = value + sep + timestamp
        return value + sep + self.get_signature(value)

    def unsign(self, value, max_age=None, return_timestamp=False):
        """기본 :meth:`.Signer.unsign``\과 비슷하게 동작하되 시간도
        검사한다. 기본 동작 방식은 기반 클래스의 docstring을 보라.
        ``return_timestamp``\가 ``True``\면 서명의 타임스탬프를
        UTC로 된 :class:`datetime.datetime` 객체로 반환한다.
        """
        try:
            result = Signer.unsign(self, value)
            sig_error = None
        except BadSignature as e:
            sig_error = e
            result = e.payload or b""
        sep = want_bytes(self.sep)

        # If there is no timestamp in the result there is something
        # seriously wrong. In case there was a signature error, we raise
        # that one directly, otherwise we have a weird situation in
        # which we shouldn't have come except someone uses a time-based
        # serializer on non-timestamp data, so catch that.
        if sep not in result:
            if sig_error:
                raise sig_error
            raise BadTimeSignature("timestamp missing", payload=result)

        value, timestamp = result.rsplit(sep, 1)
        try:
            timestamp = bytes_to_int(base64_decode(timestamp))
        except Exception:
            timestamp = None

        # Signature is *not* okay. Raise a proper error now that we have
        # split the value and the timestamp.
        if sig_error is not None:
            raise BadTimeSignature(
                text_type(sig_error), payload=value, date_signed=timestamp
            )

        # Signature was okay but the timestamp is actually not there or
        # malformed. Should not happen, but we handle it anyway.
        if timestamp is None:
            raise BadTimeSignature("Malformed timestamp", payload=value)

        # Check timestamp is not older than max_age
        if max_age is not None:
            age = self.get_timestamp() - timestamp
            if age > max_age:
                raise SignatureExpired(
                    "Signature age %s > %s seconds" % (age, max_age),
                    payload=value,
                    date_signed=self.timestamp_to_datetime(timestamp),
                )

        if return_timestamp:
            return value, self.timestamp_to_datetime(timestamp)
        return value

    def validate(self, signed_value, max_age=None):
        """서명된 값을 받아서 검증만 한다. 서명이 존재하고 유효하면
        ``True``\를 반환한다."""
        try:
            self.unsign(signed_value, max_age=max_age)
            return True
        except BadSignature:
            return False


class TimedSerializer(Serializer):
    """기본으로 :class:`.Signer` 대신 :class:`TimestampSigner`\를
    쓴다.
    """

    default_signer = TimestampSigner

    def loads(self, s, max_age=None, return_timestamp=False, salt=None):
        """:meth:`dumps`\의 반대. 서명 검증이 실패하면
        :exc:`.BadSignature`\를 던진다. ``max_age``\를 주면 서명이
        그 초 수보다 오래됐는지 확인한다. 서명이 그보다 오래된 경우
        :exc:`.SignatureExpired`\를 던진다. 모든 인자들이 signer의
        :meth:`~TimestampSigner.unsign` 메소드로 전달된다.
        """
        s = want_bytes(s)
        last_exception = None
        for signer in self.iter_unsigners(salt):
            try:
                base64d, timestamp = signer.unsign(s, max_age, return_timestamp=True)
                payload = self.load_payload(base64d)
                if return_timestamp:
                    return payload, timestamp
                return payload
            # If we get a signature expired it means we could read the
            # signature but it's invalid.  In that case we do not want to
            # try the next signer.
            except SignatureExpired:
                raise
            except BadSignature as err:
                last_exception = err
        raise last_exception

    def loads_unsafe(self, s, max_age=None, salt=None):
        load_kwargs = {"max_age": max_age}
        load_payload_kwargs = {}
        return self._loads_unsafe_impl(s, salt, load_kwargs, load_payload_kwargs)
