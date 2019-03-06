.. module:: itsdangerous.url_safe

URL에 안전한 직렬화
===================

이런 신뢰하는 문자열을 제한된 문자들만 쓸 수 있는 곳으로 보낼 수
있으면 좋을 때가 많이 있다. 그래서 itsdagerous에서는 URL에 안전한
serializer를 함께 제공한다.

.. code-block:: python

    from itsdangerous.url_safe import URLSafeSerializer
    s = URLSafeSerializer("secret-key")
    s.dumps([1, 2, 3, 4])
    'WzEsMiwzLDRd.wSPHqC0gR7VUqivlSukJ0IeTDgo'
    s.loads("WzEsMiwzLDRd.wSPHqC0gR7VUqivlSukJ0IeTDgo")
    [1, 2, 3, 4]

.. autoclass:: URLSafeSerializer

.. autoclass:: URLSafeTimedSerializer
