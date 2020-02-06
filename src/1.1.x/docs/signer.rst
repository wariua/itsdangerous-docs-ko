.. module:: itsdangerous.signer

서명 인터페이스
===============

가장 기본적인 인터페이스는 서명 인터페이스다. :class:`Signer`
클래스를 써서 특정 문자열에 서명을 붙일 수 있다.

.. code-block:: python

    from itsdangerous import Signer
    s = Signer("secret-key")
    s.sign("my string")
    b'my string.wh6tMHxLgJqB6oY1uT73iMlyrOA'

마침표로 구분해서 문자열 뒤에 서명이 덧붙는다. 문자열을 검증하려면
:meth:`~Signer.unsign` 메소드를 쓰면 된다.

.. code-block:: python

    s.unsign(b"my string.wh6tMHxLgJqB6oY1uT73iMlyrOA")
    b'my string'

유니코드 문자열을 주면 암묵적으로 UTF-8 인코딩이 이뤄진다.
하지만 서명 검증 후에 그 문자열이 유니코드였는지 바이트열이었는지
알 방법은 없다.

값이 바뀌면 서명이 더는 일치하지 않게 되고 서명 검증 과정에서
:exc:`~itsdangerous.exc.BadSignature` 예외를 던지게 된다.

.. code-block:: python

    s.unsign(b"different string.wh6tMHxLgJqB6oY1uT73iMlyrOA")
    Traceback (most recent call last):
      ...
    itsdangerous.exc.BadSignature: Signature "wh6tMHxLgJqB6oY1uT73iMlyrOA" does not match

서명 유효 기간을 써넣고 검증하고 싶다면 :doc:`/timed` 절을 보라.

.. autoclass:: Signer
    :members:


서명 알고리듬
-------------

.. autoclass:: NoneAlgorithm

.. autoclass:: HMACAlgorithm
