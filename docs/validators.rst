Validators
**********

.. module::  validators

The last step in cooked input is to validate that the entered input is valid. When called, Validators return True if
the input passes the validation (i.e. is valid), and False otherwise.


Creating Validators
===================

Validator classes inherit from the Validator metaclass. They must be callable, with the __call__ dunder
method taking three parameters: the value to validate, a function to call when an error occurs and the format string
for the error function. See the [error_callbacks] for more information on error functions and their format strings.

An example of a validator to verify that the input is exactly a specified length looks like::

    class LengthValidator(Validator):
        def __init__(self, min_len=None, max_len=None, **kwargs):
            self._min_len = min_len
            self._max_len = max_len
            super(LengthValidator, self).__init__(**kwargs)

        def __call__(self, value, error_callback, validator_fmt_str):
            try:
                val_len = len(value)
            except (TypeError):
                print('LengthValidator: value "{}" does not support __len__.'.format(value), file=sys.stderr)
                return False

            min_condition = (self._min_len is None or val_len >= self._min_len)
            max_condition = (self._max_len is None or val_len <= self._max_len)

            if min_condition and max_condition:
                return True
            elif not min_condition:
                error_callback(validator_fmt_str, value, 'too short (min_len={})'.format(self._min_len))
                return False
            else:
                error_callback(validator_fmt_str, value, 'too long (max_len={})'.format(self._max_len))
                return False

        def __repr__(self):
            return 'LengthValidator(min_len=%s, max_len=%s)' % (self.min_len, self.max_len)

Note: There are a large number of Boolean validation functions available from the validus project. These can be used as
cooked_input validation functions by wrapping them in a SimpleValidator. For instance, to use validus to validate an email address::

    from validus import isemail
    email_validator = SimpleValidator(isemail, name='email')
    email = get_input(prompt='enter a valid Email address', validators=email_validator)


for more information on validus see: https://github.com/shopnilsazal/validus


Validators
==========

LengthValidator
---------------

.. autoclass:: cooked_input.LengthValidator

EqualToValidator
-------------------

.. autoclass:: cooked_input.EqualToValidator

RangeValidator
----------------

.. autoclass:: cooked_input.RangeValidator

ChoicesValidator
------------------

.. autoclass:: cooked_input.ChoicesValidator

NoneOfValidator
--------------

.. autoclass:: cooked_input.NoneOfValidator

AnyOfValidator
--------------

.. autoclass:: cooked_input.AnyOfValidator

SimpleValidator
---------------

.. autoclass:: cooked_input.SimpleValidator

RegexValidator
--------------

.. autoclass:: cooked_input.RegexValidator

PasswordValidator
-----------------

.. autoclass:: cooked_input.PasswordValidator

ListValidator
-------------

.. autoclass:: cooked_input.ListValidator
