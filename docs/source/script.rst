Scripting
#########

# TODO


gaboon_main
-----------

The `gaboon_main` function is special, if you have a function with this name in your script, `gaboon` will run this function by default after running the script like a regular python file. For example, you could also do this:

.. code-block:: python

    from src import Counter

    def deploy():
        counter = Counter.deploy()
        print("Starting count: ", counter.number())
        counter.increment()
        print("Ending count: ", counter.number())
        return counter

    deploy()

And it would do the same as the above. 