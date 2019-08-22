from ._compat import PY2
from ._compat import text_type


class BadData(Exception):
    """어떤 식으로든 잘못된 데이터를 만난 경우 던진다.
    itsdangerous에서 정의하는 모든 예외들의 기반 클래스다.

    .. versionadded:: 0.15
    """

    message = None

    def __init__(self, message):
        super(BadData, self).__init__(self, message)
        self.message = message

    def __str__(self):
        return text_type(self.message)

    if PY2:
        __unicode__ = __str__

        def __str__(self):
            return self.__unicode__().encode("utf-8")


class BadSignature(BadData):
    """서명이 일치하지 않는 경우 던진다."""

    def __init__(self, message, payload=None):
        BadData.__init__(self, message)

        #: 서명 검사에 실패한 페이로드. 때에 따라선 변조됐다는
        #: 걸 알고 있더라도 내용을 살펴보고 싶을 수 있다.
        #:
        #: .. versionadded:: 0.14
        self.payload = payload


class BadTimeSignature(BadSignature):
    """시간 기반 서명이 유효하지 않은 경우 던진다.
    :class:`BadSignature`\의 서브클래스다.
    """

    def __init__(self, message, payload=None, date_signed=None):
        BadSignature.__init__(self, message, payload)

        #: 서명이 만료된 경우 이 필드로 서명 생성 날짜를
        #: 내보인다. 얼마나 오래 연결 갱신이 안 됐는지
        #: 사용자에게 알려주는 데 도움이 될 수 있다.
        #:
        #: .. versionadded:: 0.14
        self.date_signed = date_signed


class SignatureExpired(BadTimeSignature):
    """서명 타임스탬프가 ``max_age``\보다 오래된 경우 던진다.
    :exc:`BadTimeSignature`\의 서브클래스다.
    """


class BadHeader(BadSignature):
    """서명 헤더가 어떤 형태로든 유효하지 않은 경우 던진다.
    서명과 함께 보내는 헤더가 있는 직렬화 방식에서만 발생한다.

    .. versionadded:: 0.24
    """

    def __init__(self, message, payload=None, header=None, original_error=None):
        BadSignature.__init__(self, message, payload)

        #: 헤더가 실제 있기는 한데 형식이 잘못된 경우에 여기에
        #: 그 헤더를 저장할 수도 있다.
        self.header = header

        #: 설정된 경우, 헤더가 유효하지 않은 이유를 나타내는
        #: 오류. ``None``\일 수도 있다.
        self.original_error = original_error


class BadPayload(BadData):
    """페이로드가 유효하지 않은 경우 던진다. 서명이 유효하지 않은데도
    페이로드를 적재하는 경우, 또는 직렬화 모듈과 역직렬화 모듈이
    일치하지 않는 경우에 발생할 수 있다. 적재 중 발생한 원래 예외가
    :attr:`original_error`\에 저장된다.

    .. versionadded:: 0.15
    """

    def __init__(self, message, original_error=None):
        BadData.__init__(self, message)

        #: 설정된 경우, 페이로드가 유효하지 않은 이유를 나타내는
        #: 오류. ``None``\일 수도 있다.
        self.original_error = original_error
