.. module:: itsdangerous.serializer

직렬화 인터페이스
=================

:doc:`/signer` 는 문자열에만 서명을 한다. 다른 타입에도 서명을
할 수 있도록 :class:`Serializer` 클래스에는 파이썬 :mod:`json`
모듈과 비슷한 ``dumps``/``loads`` 인터페이스가 있어서 오브젝트를
문자열로 직렬화 한 다음 서명을 해 준다.

:meth:`~Serializer.dumps` 를 사용해 데이터를 직렬화 하고 서명 한다.

.. code-block:: python

    from itsdangerous.serializer import Serializer
    s = Serializer("secret-key")
    s.dumps([1, 2, 3, 4])
    b'[1, 2, 3, 4].r7R9RhGgDPvvWl3iNzLuIIfELmo'

:meth:`~Serializer.loads` 를 사용해 서명을 검증하고 데이터를
역직렬화 한다.

.. code-block:: python

    s.loads('[1, 2, 3, 4].r7R9RhGgDPvvWl3iNzLuIIfELmo')
    [1, 2, 3, 4]

기본적으로 데이터를 JSON으로 직렬화 한다. simplejson이 설치돼
있으면 내장 :mod:`json` 모듈 대신 사용한다. 서브클래스를 만들어서
그 내부 직렬화 모듈을 바꿀 수 있다.

서명의 유효 기간을 기록하고 검증하고 싶다면 :doc:`/timed` 를 보라.
URL에 쓰기 안전한 형식으로 직렬화 하고 싶다면
:doc:`/url_safe` 를 보라.


.. _the-salt:

솔트
----

모든 클래스들이 솔트 인자도 받는다. 이름이 오해를 유발할 수도 있을
것 같다. 일반적으로 암호학에서 솔트라고 하면 서명된 결과 문자열과
함께 저장해서 레인보 테이블 검색을 막는 뭔가를 기대할 것이기
때문이다. 그런 솔트는 일반적으로 공개된다.

itsdangerous에서는 원래 장고 구현에서처럼 솔트가 다른 역할을 한다.
일종의 네임스페이스라고 볼 수도 있다. 이 역시 공개돼도 크게 위험하지
않는데, 비밀키 없이는 공격자에게 도움이 안 되기 때문이다.

서명하려는 링크가 두 개 있다고 해 보자. 시스템 상에서 사용자 계정을
활성화할 수 있는 활성화 링크가 있고 사용자의 계정을 유료 계정으로
업그레이드 할 수 있는 업그레이드 링크가 있어서 이메일을 통해 보낸다.
두 경우 모두 사용자 ID에만 서명을 한다면 어느 사용자가 활성 링크
URL의 변수 부분을 재사용해서 계정을 업그레이드 할 수도 있을 것이다.
이 경우 더 많은 정보(가령 용도, 업그레이드 또는 활성)를 서명 대상에
포함시킬 수도 있겠지만 다른 솔트를 쓰는 방법도 가능하다.

.. code-block:: python

    from itsdangerous.url_safe import URLSafeSerializer
    s1 = URLSafeSerializer("secret-key", salt="activate")
    s1.dumps(42)
    'NDI.MHQqszw6Wc81wOBQszCrEE_RlzY'
    s2 = URLSafeSerializer("secret-key", salt="upgrade")
    s2.dumps(42)
    'NDI.c0MpsD6gzpilOAeUPra3NShPXsE'

첫 번째 serializer가 내놓은 데이터를 두 번째 serializer로 받을 수
없다. 솔트가 다르기 때문이다.

.. code-block:: python

    s2.loads(s1.dumps(42))
    Traceback (most recent call last):
      ...
    itsdangerous.exc.BadSignature: Signature "MHQqszw6Wc81wOBQszCrEE_RlzY" does not match

솔트가 같은 serializer로만 데이터를 받을 수 있다.

.. code-block:: python

    s2.loads(s2.dumps(42))
    42


실패 대응
---------

예외에는 유용한 속성들이 있어서 서명 검사가 실패한 경우 페이로드를
살펴볼 수 있다. 그 경우 특별히 주의할 필요가 있는데 그 지점으로
갔다는 건 누군가 데이터를 조작했다는 뜻이기 때문이다. 디버깅 용도에
유용할 수도 있다.

.. code-block:: python

    from itsdangerous.serializer import Serializer
    from itsdangerous.exc import BadSignature, BadData

    s = URLSafeSerializer("secret-key")
    decoded_payload = None

    try:
        decoded_payload = s.loads(data)
        # 페이로드를 디코딩 했으며 안전함
    except BadSignature as e:
        if e.payload is not None:
            try:
                decoded_payload = s.load_payload(e.payload)
            except BadData:
                pass
            # 페이로드를 디코딩 했지만 누군가 서명을 조작했으므로
            # 안전하지 않음. 명시적으로 디코딩(load_payload) 단계가
            # 있는 건 페이로드를 역직렬화 하는 게 안전하지 않을 수도
            # 있기 때문임. (json이 아니라 pickle이라고 생각해 보라!)

속성을 들여다봐서 정확히 뭐가 잘못됐는지 알아내려는 게 아니라면
:meth:`~Serializer.loads_unsafe` 를 쓸 수도 있다.

.. code-block:: python

    sig_okay, payload = s.loads_unsafe(data)

반환되는 튜플의 첫 번째 항목이 서명이 올바른지 나타내는 불리언이다.

API
---

.. autoclass:: Serializer
    :members:
