
Cooked Input CHANGELOG
======================

This is the change log for the cooked_input Python package,

github archive: https://github.com/lwanger/cooked_input

for the latest documentation, see: https://readthedocs.org/projects/cooked-input/

see TODO.md for list of TODO items

v0.2.2:
-------

* Added minimum and maximum parameters to get_int and get_float convenience functions.


v0.2.1:
-------

* Added convenience functions for: get_sring, get_int, get_float, get_boolean, get_list, get_date, and get_yes_no.

* Added examples of calling the convenience functions to the examples (e.g. get_ints, get_lists, get_strs, simple_input).

* Updated the tutorial to use the get_int convenience function. Also show example of PasswordValidator.

* Created exception for: MaxRetriesError (subclassed from RuntimeError), raised when the maximum number of retries is exceeded.

* Created exception for: ValidationError (subclassed from ValueError), raised when a value does not pass validation.

* Get_*, Convertors and validators now raise MaxRetriesExceeded and ValidationError.

* Added pytest tests for getting ints and floats. A lot more case to add.

v0.2.0:
-------


* Made a major change to how errors are handled. Added error_callbacks, convertor format strings, and
  validation convertor strings. This changed most of the code base and some of the examples.

* Added print_error, log_error, and ignore_error error callback routines.



