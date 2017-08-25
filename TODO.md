
# cooked_input TODO list

**TODO:**

* general:
    * Improve the README file
    * Add automated tests (pytest?)
    * Add queue_errors error handler. Use for an example to send flash_messages for Flask support. Add option to 
        validators to force running all validators vs. quiting after first error found.
    * Add tables (build-a-burger) to tutorial
    * Review examples, tutorial interface. Clean up and make: easier, cleaner, more consistent.
        Are classes needed for Validators, Convertors, Cleaners, or can the be any callable? Convertors
        using error string only.
    * decorators to make cleaners, convertors, etc. decorator for strip and lower cleaners? 
        get yes/no, get an int in a range, etc. Use decorators to reduce boilerplate code.
    * add part 2 (and part 3?) to tutorial to show more examples: passwords (get_user_info), tables,
        menus, and databases?

* get_input:
    * send error messages to stderr?
    * option to list choices in prompt_str (???)? Show hints? Create Mini-language of /cmds
    * replace raw_input with version using sys.stdin.readline()
    * show all errors for validation errors? Perform like flash messages where can have a list of them?
    * provide kwarg to run all validators, instead of failing on first one, so can see all errors.
    * autocomplete (???)
    * add routine to make menus more easily

* get_table_input
    * make it easier to make tables from query results
    * allow showing multiple columns tables (with one column as value)
    * allow value column to show longer description, but type in value
    * allow typing unique first characters of a choice input?
       
* examples/tests:
    * change to examples
    * add: date
    * add: ReplaceCleaner

* cleaners:
    * make default cleaners = [Stripcleaner]
    * cleaner for Unicode normalization and character encodings
    * cleaner for html quoting/unquoting
    * make a single capitalization cleaner with parameter for upper, lower, or capitalized
    * strip sql injection when dealing with tables

* convertors:
    * add: file, path, etc.
    * add dollar convertor that has minimum of 0.00 and strips off $ sign and commas. Returns float
 
* validators:
    * NotInValidator - if a value or list is passed in should use those as exact values. 
        NotInValidator('foo') causes a TypeError for now.
    * add: date range, date day of week
    * allow forcing to validate all validators instead of stopping on first failure
    * return list of all validation failures
    * provide list of hints for what is required
    * password validator should create hint of what's required for password