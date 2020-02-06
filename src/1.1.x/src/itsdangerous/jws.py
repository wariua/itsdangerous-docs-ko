import hashlib
import time
from datetime import datetime

from ._compat import number_types
from ._json import _CompactJSON
from ._json import json
from .encoding import base64_decode
from .encoding import base64_encode
from .encoding import want_bytes
from .exc import BadData
from .exc import BadHeader
from .exc import BadPayload
from .exc import BadSignature
from .exc import SignatureExpired
from .serializer import Serializer
from .signer import HMACAlgorithm
from .signer import NoneAlgorithm


class JSONWebSignatureSerializer(Serializer):
    """이 직렬화 모듈에선 JSON 웹 서명(JWS) 지원을 구현하고 있다.
    JWS Compact Serialization만 지원한다.
    """

    jws_algorithms = {
        "HS256": HMACAlgorithm(hashlib.sha256),
        "HS384": HMACAlgorithm(hashlib.sha384),
        "HS512": HMACAlgorithm(hashlib.sha512),
        "none": NoneAlgorithm(),
    }

    #: 서명 생성에 사용할 기본 알고리듬
    default_algorithm = "HS512"

    default_serializer = _CompactJSON

    def __init__(
        self,
        secret_key,
        salt=None,
        serializer=None,
        serializer_kwargs=None,
        signer=None,
        signer_kwargs=None,
        algorithm_name=None,
    ):
        Serializer.__init__(
            self,
            secret_key=secret_key,
            salt=salt,
            serializer=serializer,
            serializer_kwargs=serializer_kwargs,
            signer=signer,
            signer_kwargs=signer_kwargs,
        )
        if algorithm_name is None:
            algorithm_name = self.default_algorithm
        self.algorithm_name = algorithm_name
        self.algorithm = self.make_algorithm(algorithm_name)

    def load_payload(self, payload, serializer=None, return_header=False):
        payload = want_bytes(payload)
        if b"." not in payload:
            raise BadPayload('No "." found in value')
        base64d_header, base64d_payload = payload.split(b".", 1)
        try:
            json_header = base64_decode(base64d_header)
        except Exception as e:
            raise BadHeader(
                "Could not base64 decode the header because of an exception",
                original_error=e,
            )
        try:
            json_payload = base64_decode(base64d_payload)
        except Exception as e:
            raise BadPayload(
                "Could not base64 decode the payload because of an exception",
                original_error=e,
            )
        try:
            header = Serializer.load_payload(self, json_header, serializer=json)
        except BadData as e:
            raise BadHeader(
                "Could not unserialize header because it was malformed",
                original_error=e,
            )
        if not isinstance(header, dict):
            raise BadHeader("Header payload is not a JSON object", header=header)
        payload = Serializer.load_payload(self, json_payload, serializer=serializer)
        if return_header:
            return payload, header
        return payload

    def dump_payload(self, header, obj):
        base64d_header = base64_encode(
            self.serializer.dumps(header, **self.serializer_kwargs)
        )
        base64d_payload = base64_encode(
            self.serializer.dumps(obj, **self.serializer_kwargs)
        )
        return base64d_header + b"." + base64d_payload

    def make_algorithm(self, algorithm_name):
        try:
            return self.jws_algorithms[algorithm_name]
        except KeyError:
            raise NotImplementedError("Algorithm not supported")

    def make_signer(self, salt=None, algorithm=None):
        if salt is None:
            salt = self.salt
        key_derivation = "none" if salt is None else None
        if algorithm is None:
            algorithm = self.algorithm
        return self.signer(
            self.secret_key,
            salt=salt,
            sep=".",
            key_derivation=key_derivation,
            algorithm=algorithm,
        )

    def make_header(self, header_fields):
        header = header_fields.copy() if header_fields else {}
        header["alg"] = self.algorithm_name
        return header

    def dumps(self, obj, salt=None, header_fields=None):
        """:meth:`.Serializer.dumps`\와 비슷하되 JSON 웹 서명을
        만들어 낸다. JWS 헤더에 추가로 포함시킬 필드를 지정하는 것도
        가능하다.
        """
        header = self.make_header(header_fields)
        signer = self.make_signer(salt, self.algorithm)
        return signer.sign(self.dump_payload(header, obj))

    def loads(self, s, salt=None, return_header=False):
        """:meth:`dumps`\의 반대. ``return_header``\를 설정해
        요청하면 페이로드와 헤더로 된 튜플을 반환한다.
        """
        payload, header = self.load_payload(
            self.make_signer(salt, self.algorithm).unsign(want_bytes(s)),
            return_header=True,
        )
        if header.get("alg") != self.algorithm_name:
            raise BadHeader("Algorithm mismatch", header=header, payload=payload)
        if return_header:
            return payload, header
        return payload

    def loads_unsafe(self, s, salt=None, return_header=False):
        kwargs = {"return_header": return_header}
        return self._loads_unsafe_impl(s, salt, kwargs, kwargs)


class TimedJSONWebSignatureSerializer(JSONWebSignatureSerializer):
    """기본 :class:`JSONWebSignatureSerializer`\처럼 동작하되
    서명 시간까지 기록하므로 서명이 만료되게 할 수 있다.

    JWS에서는 현재 이런 동작을 명세하고 있지 않지만 이런 확장이
    가능하다고 명세에서 언급하고 있다. `draft-ietf-oauth-json
    -web-token <http://self-issued.info/docs/draft-ietf-oauth-json
    -web-token.html#expDef>`_\에 명세된 것과 비슷한 방식으로
    만료 날짜를 헤더에 인코딩 한다.
    """

    DEFAULT_EXPIRES_IN = 3600

    def __init__(self, secret_key, expires_in=None, **kwargs):
        JSONWebSignatureSerializer.__init__(self, secret_key, **kwargs)
        if expires_in is None:
            expires_in = self.DEFAULT_EXPIRES_IN
        self.expires_in = expires_in

    def make_header(self, header_fields):
        header = JSONWebSignatureSerializer.make_header(self, header_fields)
        iat = self.now()
        exp = iat + self.expires_in
        header["iat"] = iat
        header["exp"] = exp
        return header

    def loads(self, s, salt=None, return_header=False):
        payload, header = JSONWebSignatureSerializer.loads(
            self, s, salt, return_header=True
        )

        if "exp" not in header:
            raise BadSignature("Missing expiry date", payload=payload)

        int_date_error = BadHeader("Expiry date is not an IntDate", payload=payload)
        try:
            header["exp"] = int(header["exp"])
        except ValueError:
            raise int_date_error
        if header["exp"] < 0:
            raise int_date_error

        if header["exp"] < self.now():
            raise SignatureExpired(
                "Signature expired",
                payload=payload,
                date_signed=self.get_issue_date(header),
            )

        if return_header:
            return payload, header
        return payload

    def get_issue_date(self, header):
        rv = header.get("iat")
        if isinstance(rv, number_types):
            return datetime.utcfromtimestamp(int(rv))

    def now(self):
        return int(time.time())
