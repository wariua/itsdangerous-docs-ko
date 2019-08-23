import zlib

from ._json import _CompactJSON
from .encoding import base64_decode
from .encoding import base64_encode
from .exc import BadPayload
from .serializer import Serializer
from .timed import TimedSerializer


class URLSafeSerializerMixin(object):
    """Mixed in with a regular serializer it will attempt to zlib
    compress the string to make it shorter if necessary. It will also
    base64 encode the string so that it can safely be placed in a URL.
    """

    default_serializer = _CompactJSON

    def load_payload(self, payload, *args, **kwargs):
        decompress = False
        if payload.startswith(b"."):
            payload = payload[1:]
            decompress = True
        try:
            json = base64_decode(payload)
        except Exception as e:
            raise BadPayload(
                "Could not base64 decode the payload because of an exception",
                original_error=e,
            )
        if decompress:
            try:
                json = zlib.decompress(json)
            except Exception as e:
                raise BadPayload(
                    "Could not zlib decompress the payload before decoding the payload",
                    original_error=e,
                )
        return super(URLSafeSerializerMixin, self).load_payload(json, *args, **kwargs)

    def dump_payload(self, obj):
        json = super(URLSafeSerializerMixin, self).dump_payload(obj)
        is_compressed = False
        compressed = zlib.compress(json)
        if len(compressed) < (len(json) - 1):
            json = compressed
            is_compressed = True
        base64d = base64_encode(json)
        if is_compressed:
            base64d = b"." + base64d
        return base64d


class URLSafeSerializer(URLSafeSerializerMixin, Serializer):
    """:class:`.Serializer`\처럼 동작하되 알파벳 대소문자와
    ``'_'``, ``'-'``, ``'.'``\로 이뤄진 URL 안전 문자열을
    덤프 및 적재한다.
    """


class URLSafeTimedSerializer(URLSafeSerializerMixin, TimedSerializer):
    """:class:`.TimedSerializer`\처럼 동작하되 알파벳 대소문자와
    ``'_'``, ``'-'``, ``'.'``\로 이뤄진 URL 안전 문자열을
    덤프 및 적재한다.
    """
