.. module:: itsdangerous.jws

JSON 웹 서명 (JWS)
==================

JSON 웹 서명(JWS)은 앞서 본 URL 안전 serializer와 비슷하게
동작하되 `draft-ietf-jose-json-web-signature <http://self-issued.info/
docs/draft-ietf-jose-json-web-signature.html>`_ 에 따라 헤더를
찍는다.

.. code-block:: python

    from itsdangerous import JSONWebSignatureSerializer
    s = JSONWebSignatureSerializer("secret-key")
    s.dumps({"x": 42})
    'eyJhbGciOiJIUzI1NiJ9.eyJ4Ijo0Mn0.ZdTn1YyGz9Yx5B5wNpWRL221G1WpVE5fPCPKNuc6UAo'

값을 다시 받을 때 다른 serializer들과 마찬가지로 기본적으로 헤더가
반환되지 않는다. 하지만 ``return_header=True`` 를 줘서 헤더를
요청할 수도 있다. 직렬화 때 자체적인 헤더 필드를 제공할 수 있다.

.. code-block:: python

    s.dumps(0, header_fields={"v": 1})
    'eyJhbGciOiJIUzI1NiIsInYiOjF9.MA.wT-RZI9YU06R919VBdAfTLn82_iIQD70J_j-3F4z_aM'
    s.loads(
        "eyJhbGciOiJIUzI1NiIsInYiOjF9"
        ".MA.wT-RZI9YU06R919VBdAfTLn82_iIQD70J_j-3F4z_aM"
    )
    (0, {'alg': 'HS256', 'v': 1})

현재 itsdangerous에서는 HMAC SHA 파생 알고리듬과 none 알고리듬만
제공하고 ECC 기반 알고리듬을 지원하지 않는다. 헤더 내의 알고리듬을
serializer의 알고리듬과 비교해서 불일치 시
:exc:`~itsdangerous.exc.BadSignature` 예외를 던진다.

.. autoclass:: JSONWebSignatureSerializer
    :members:

.. autoclass:: TimedJSONWebSignatureSerializer
    :members:
