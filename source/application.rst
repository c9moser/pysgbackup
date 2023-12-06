Application
============

.. autofunction:: sgbackup.main

.. autoclass:: sgbackup.application::Application
    :members:

Examples
---------

Using :func:`sgbackup.main`
___________________________

If you hust want to implement a simple app running from commandline arguments,
you can use the :func:`sgbackup.main` function. This is the most simple 
usecase for `pysgbackup`.

.. code-block:: python3

    import sys
    import sgbackup

    if __name__ == '__main__':
        sys.exit(sgbackup.main())

Using :class:`sgbackup.application.Application`
_______________________________________________

To use the :class:`sgbackup.application.Application` you need to initialize it
properly before you can use it. This can be done by calling 
:func:`sgbackup.application.Application.initialize`.

.. code-block:: python3

    import sgbackup

    app = sgbackup.Application()
    app.initialize()

If you just want to run it from command line arguments you can use 
:func:`sgbackup.application.Application.run`, which does the initialisation for
you too. The `sgbackup` program, which calls the :func:`main` function are 
using this interface.

.. code-block:: python3

    import sys
    import sgbackup

    app = sgbackup.Application()
    app.run(sys.argv[1])
