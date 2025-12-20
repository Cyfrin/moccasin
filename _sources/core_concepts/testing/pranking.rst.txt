Pranking 
######## 

You can prank/impresonate/pretend to be other contracts or addresses in your test using the ``boa.prank`` function. 

.. code-block:: python 

    import boa
    print(boa.env.eoa) # 0x0000000000000000000000000000000000000065
    with boa.env.prank("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"):
        print(boa.env.eoa) # 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

Using this pranking feature is the ideal way to impresonate addresses in tests. 
