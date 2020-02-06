.. module:: itsdangerous.timed

타임스탬프 사용해 서명하기
==========================

서명이 만료되게 하고 싶다면 :class:`TimestampSigner` 클래스를
쓸 수 있다. 그러면 타임스탬프 정보를 추가하고 서명한다.
서명 검증 시 타임스탬프가 만료되지 않았는지 확인할 수 있다.

.. code-block:: python

    from itsdangerous import TimestampSigner
    s = TimestampSigner('secret-key')
    string = s.sign('foo')

.. code-block:: python

    s.unsign(string, max_age=5)
    Traceback (most recent call last):
      ...
    itsdangerous.exc.SignatureExpired: Signature age 15 > 5 seconds

.. autoclass:: TimestampSigner
    :members:

.. autoclass:: TimedSerializer
    :members:
