Cleaners
********

.. module::  cleaners

Cleaner classes for cleaning input before conversion and validation.


Creating Cleaners
=================

Cleaner classes inherit from the Cleaner metaclass. They must be callable, with the __call__ dunder
method taking one parameter, the value. An example of a cleaner to change the input value to lower
case looks like::

    class LowerCleaner(Cleaner):
        def __init__(self, **kwargs):
            super(LowerCleaner, self).__init__(**kwargs)
            # initialize any specific state for the cleaner.

        def __call__(self, value, error_callback, convertor_fmt_str):
            result = value.lower()
            return result

Cleaners
========

StripCleaner
------------

.. autoclass:: cooked_input.StripCleaner

CapitalizationCleaner
---------------------

.. autoclass:: cooked_input.CapitalizationCleaner

ReplaceCleaner
--------------

.. autoclass:: cooked_input.ReplaceCleaner

RemoveCleaner
-------------

.. autoclass:: cooked_input.RemoveCleaner

ChoiceCleaner
-------------

.. autoclass:: cooked_input.ChoiceCleaner

RegexCleaner
------------

.. autoclass:: cooked_input.RegexCleaner
