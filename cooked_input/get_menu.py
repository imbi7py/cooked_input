from __future__ import print_function

"""
get_menu - menu system for cooked_input

Len Wanger, 2017

TODO:

# Table(rows, col_names=None, title=None, prompt=None, default_choice=None, default_str=None, default_action=None, **options):
# show_table? sort_by_value?
# navigation keys
# return value from action (default - return tag)


- Document and add to tutorial

- Examples/scenarios:
    - menus:
        - dynamic menu - from:
            X list
            X database
            - Pandas
        X test hidden commands. Test commands in header/footer
        - different display functions (i.e. function for displaying the table - silent_table for no display of menu or table)
        - set user profile - list users, add profile, edit profile
        - different borders
        - example runner
        - change Menus to tables - extend table to multiple columns with first as tag
        - How to deal with non unique tags? Unique option and keep set of tags? Or pick first, or pick from current paginated page
        X Header and footer to print. So can have commands listed per page as hidden menu items (e.g. Search or filter)
        - Dynamic function - for long tables, lookup entered value instead of showing as rows. Maybe lazy evaluation? A lookup cleaner?
"""

"""
TODO:
    - Look at veryprettytable? https://github.com/smeggingsmegger/VeryPrettyTable/blob/master/veryprettytable.py
    - Look at: https://github.com/moul/prettytable-extras
        adds color_styles: 'bold','italic','underline','inverse', white,gray,black,blue,cyan,green,magenta,red,yellow
        new PrettyTable kwarg options - auto_width, header_color
    - port prettytable-extras to veryprettytable?
    - add color for title and header
    - add setting fore and back colors on rows? (int or slice?)
    - curses ability - use get_string?
    - pagination - add paginator? - paginate in veryprettytable isn't quite right... need like flask paginate
        Pagination()
            __init__(page, per_page, total_count)   <-- can add search (and search col?)
                cur_page
                found   - when searching
                per_page
                search - None or value? or callable function (key)
                total - total records for pagination
                display_msg - fmt string for all these things (gets variables for cur_page, found, total_pages, etc.)
                search_msg
            has_prev()
            has_next()
            iter_pages()
            render(page_num='first'|'last'|'current'|'next'|'last'|#) - renders with stop/end and navigation (page x of y) or 'found' with search
navigation buttons (selected line and up/down, pageup/pagedown, home,end
"""


import sys
import string
import logging

from prompt_toolkit.layout.containers import Window, VSplit
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.interface import Application, CommandLineInterface
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.key_binding.manager import KeyBindingManager, Registry
from prompt_toolkit.keys import Keys

from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import LayoutDimension

import veryprettytable as pt

from cooked_input import get_input
from cooked_input import GetInputInterrupt, RefreshScreenInterrupt
from cooked_input import default_key_registry
from .input_utils import put_in_a_list, isstring
from .cleaners import CapitalizationCleaner, StripCleaner, ChoiceCleaner
from .convertors import ChoiceConvertor
# from .validators import RangeValidator
from .validators import ChoiceValidator


TABLE_DEFAULT_ACTION = 'default'
TABLE_ACTION_EXIT = 'exit'
TABLE_ACTION_RETURN = 'return'

TABLE_ADD_EXIT = 'exit'
TABLE_ADD_RETURN = 'return'
TABLE_ADD_NONE = 'none'


# def register_table_keys(registry):
def register_table_keys(registry, ptable, table_buffer):
    # closure values to avoid globals. ptable is the Table instance, table_buffer is the prompt_toolkit buffer
    # for the table text.
    tbl = ptable
    tbl_buffer = table_buffer
    # prompt_buffer = prompt_buffer # TODO - redraw prompt...

    @registry.add_binding(Keys.Escape, eager=True)
    def _(event):
        event.cli.set_return_value(None)

    @registry.add_binding(Keys.ControlD, eager=True)
    def _(event):
        raise GetInputInterrupt('Operation cancelled by the user.')

    @registry.add_binding(Keys.PageUp)
    def _(event):
        # global ptable
        # ptable.table_page_up(event.cli.buffers['TABLE'])
        tbl.page_up(event.cli.buffers[tbl_buffer])


    @registry.add_binding(Keys.PageDown)
    def _(event):
        # tbl.page_down(event.cli.buffers[tbl_buffer])
        tbl.page_down()

    @registry.add_binding(Keys.Home)
    def _(event):
        # global ptable
        # ptable.table_goto_home(event.cli.buffers['TABLE'])
        tbl.goto_home(event.cli.buffers[tbl_buffer])


    @registry.add_binding(Keys.End)
    def _(event):
        # global ptable
        # ptable.table_goto_end(event.cli.buffers['TABLE'])
        tbl.goto_end(event.cli.buffers[tbl_buffer])


    @registry.add_binding(Keys.Up)
    def _(event):
        # global ptable
        # up arrow goes down in the table
        # ptable.table_go_down(event.cli.buffers['TABLE'])
        tbl.scroll_down_one_row(event.cli.buffers[tbl_buffer])


    @registry.add_binding(Keys.Down)
    def _(event):
        # global ptable
        # down arrow goes up in the table
        # ptable.table_go_up(event.cli.buffers['TABLE'])
        tbl.scroll_up_one_row(event.cli.buffers[tbl_buffer])


    # ????
    @registry.add_binding(Keys.Enter)
    def _(event):
        event.cli.set_return_value(event.cli.buffers['DEFAULT_BUFFER'].text)

    # @registry.add_binding(Keys.F2)
    # def _(event):
    #     print('F2!')

    # return registry


def return_table_item_action(row, action_dict):
    """
    Default action function for Tables. This function returns the whole row of data.

    :param row: the data associated with the selected row
    :param action_dict: the dictionary of values associated with the action - ignored in this function

    :return: A list containing all of the data for the selected row of the table.
    """
    return row


def return_row_action(row, action_dict):
    """
    Default action function for Tables. This function returns the whole row of data.

    :param row: the data associated with the selected row
    :param action_dict: the dictionary of values associated with the action - ignored in this function

    :return: A list containing all of the data for the selected row of the table.
    """
    return row.values


def return_tag_action(row, action_dict):
    """
    Default action function for menus. This function returns the tag for the
    row of data.

    :param row: the data associated with the selected row
    :param action_dict: the dictionary of values associated with the action - ignored in this function

    :return: A list containing all of the data for the selected row of the table.
    """
    return row.tag


class TableItem(object):
    def __init__(self, col_values, tag=None, action=TABLE_DEFAULT_ACTION, item_data=None, hidden=False, enabled=True):
        """
        # TODO - flesh out documentation - for instance parameters to action calls

        TableItem is used to represent individual rows in a table. Can also be used for menu items.

        :param col_values: A list of values the row's columns
        :param tag:  a value that can be used to choose the item. If None, a default tag will be assigned by the Table
            The tag is often an integer of the row number, a database ID, or a textual tag.
        :param action:  the action to take when the item is selected. By default the tag value is returned.
        :param item_data:  a dictionary containing data for the table row. Can be used for database ID's. Also
            used for item filters
        :param hidden:  Table row will not be shown if True (but will still be selectable), the table row is shown
            if False (default). Useful for filtering tables
        :param enabled:  Table row is shown and selectable if True (default), shown and not selectable if False

        TableItem actions:

        +----------------------+--------------------------------------------------------------------------+
        | value                | action                                                                   |
        +----------------------+--------------------------------------------------------------------------+
        | TABLE_DEFAULT_ACTION |  use default method to handle the table item (e.g. call                  |
        |                      |  default_action handler function)                                        |
        +----------------------+--------------------------------------------------------------------------+
        | TABLE_ACTION_EXIT    |  selecting the table row should exit (ie exit the menu)                  |
        +----------------------+--------------------------------------------------------------------------+
        | TABLE_ACTION_RETURN  |  selecting the table row should return (ie return from the menu)         |
        +----------------------+--------------------------------------------------------------------------+

        """
        self.values = put_in_a_list(col_values)
        self.tag = tag
        self.action = action
        self.item_data = item_data
        self.hidden = hidden
        self.enabled = enabled

    def __repr__(self):
        return 'TableItem(col_values={}, tag={}, action={}, item_data={}, hidden={}, enabled={})'.format(self.values, self.tag,
                                                                                                         self.action, self.item_data, self.hidden, self.enabled)


class DynamicTableItem(TableItem):
    # TODO - document - dynamically create table items from an iterable (query). Each iteration calls the table item
    # factory to add that row to the table. Document factory calls - get row #, row data, and item_data. Returns a
    # Table item. Row # is 1 based (not zero based).
    def __init__(self, query, table_item_factory, item_data=None):
        self.query = query
        self.table_item_factory = table_item_factory
        self.item_data = item_data
        # no call to super... sub-class is so isinstance works to detect subclass.

    def __repr__(self):
        return 'DynamicTableItem(query={}, table_item_factory={}, item_data={})'.format(self.query, self.table_item_factory, self.item_data)

    def __call__(self, *args, **kwargs):
        table_items = []

        for i, row in enumerate(self.query):
            table_item = self.table_item_factory(i + 1, row, self.item_data)
            table_items.append(table_item)

        return table_items


class Table(object):
    # TODO - document, including actions

    def __init__(self, rows, col_names=None, title=None, prompt=None, default_choice=None, default_str=None,
                 default_action=None, rows_per_page=20, **options):
        """

        :param rows:
        :param col_names:
        :param title:
        :param prompt:
        :param default_choice:
        :param default_str:
        :param default_action:
        :param rows_per_page:
        :param options: see below for a list of valid options

        Options:

        required            requires an entry if True, exits the menu on blank entry if False
        add_exit            automatically adds a MenuItem to exit the menu (MENU_ADD_EXIT - default) or return to the
                            parent menu (MENU_ADD_RETURN), or not to add a MenuItem at all (False)
        action_dict         a dictionary of values to pass to action functions. Used to provide context to the action
        case_sensitive      whether choosing menu items should be case sensitive (True) or not (False - default)
        item_filter         a function used to determine which menu items to display. An item is display if the function returns True for the item.
                                All items are displayed if item_filter is None (default)
        refresh             refresh menu items each time the menu is shown (True - default), or just when created (False). Useful for dynamic menus
        header              a format string to print before the table, can use any value from action_dict as well as pagination information
        footer              a format string to print after the table, can use any values from action_dict as well as pagination information
        """
        try:
            self.required = options['required']
        except KeyError:
            self.required = True

        try:
            add_exit = options['add_exit']
            if add_exit in { False, TABLE_ADD_EXIT, TABLE_ADD_RETURN }:
                self.add_exit = add_exit
            else:
                print('Table:__init__: ')
                raise RuntimeError('Table: unexpected value for add_exit option ({})'.format(add_exit))
        except KeyError:
            self.add_exit = False


class TableItem(object):
    def __init__(self, col_values, tag=None, action=TABLE_DEFAULT_ACTION, item_data=None, hidden=False, enabled=True):
        """
        # TODO - flesh out documentation - for instance parameters to action calls

        TableItem is used to represent individual rows in a table. Can also be used for menu items.

        :param col_values: A list of values the row's columns
        :param tag:  a value that can be used to choose the item. If None, a default tag will be assigned by the Table
            The tag is often an integer of the row number, a database ID, or a textual tag.
        :param action:  the action to take when the item is selected. By default the tag value is returned.
        :param item_data:  a dictionary containing data for the table row. Can be used for database ID's. Also
            used for item filters
        :param hidden:  Table row will not be shown if True (but will still be selectable), the table row is shown
            if False (default). Useful for filtering tables
        :param enabled:  Table row is shown and selectable if True (default), shown and not selectable if False

        TableItem actions:

        +----------------------+--------------------------------------------------------------------------+
        | value                | action                                                                   |
        +----------------------+--------------------------------------------------------------------------+
        | TABLE_DEFAULT_ACTION |  use default method to handle the table item (e.g. call                  |
        |                      |  default_action handler function)                                        |
        +----------------------+--------------------------------------------------------------------------+
        | TABLE_ACTION_EXIT    |  selecting the table row should exit (ie exit the menu)                  |
        +----------------------+--------------------------------------------------------------------------+
        | TABLE_ACTION_RETURN  |  selecting the table row should return (ie return from the menu)         |
        +----------------------+--------------------------------------------------------------------------+

        """
        self.values = put_in_a_list(col_values)
        self.tag = tag
        self.action = action
        self.item_data = item_data
        self.hidden = hidden
        self.enabled = enabled

    def __repr__(self):
        return 'TableItem(col_values={}, tag={}, action={}, item_data={}, hidden={}, enabled={})'.format(self.values, self.tag,
                                                                                                         self.action, self.item_data, self.hidden, self.enabled)


class DynamicTableItem(TableItem):
    # TODO - document - dynamically create table items from an iterable (query). Each iteration calls the table item
    # factory to add that row to the table. Document factory calls - get row #, row data, and item_data. Returns a
    # Table item. Row # is 1 based (not zero based).
    def __init__(self, query, table_item_factory, item_data=None):
        self.query = query
        self.table_item_factory = table_item_factory
        self.item_data = item_data
        # no call to super... sub-class is so isinstance works to detect subclass.

    def __repr__(self):
        return 'DynamicTableItem(query={}, table_item_factory={}, item_data={})'.format(self.query, self.table_item_factory, self.item_data)

    def __call__(self, *args, **kwargs):
        table_items = []

        for i, row in enumerate(self.query):
            table_item = self.table_item_factory(i + 1, row, self.item_data)
            table_items.append(table_item)

        return table_items


class Table(object):
    # TODO - document, including actions

    # def __init__(self, rows, col_names=None, title=None, prompt=None, default_choice=None, default_str=None,
    def __init__(self, rows, col_names, title=None, prompt=None, default_choice=None, default_str=None,
                 default_action=None, rows_per_page=20, **options):
        """

        :param rows:
        :param col_names:
        :param title:
        :param prompt:
        :param default_choice:
        :param default_str:
        :param default_action:
        :param rows_per_page:
        :param options: see below for a list of valid options

        Options:

        required            requires an entry if True, exits the menu on blank entry if False
        add_exit            automatically adds a MenuItem to exit the menu (MENU_ADD_EXIT - default) or return to the
                            parent menu (MENU_ADD_RETURN), or not to add a MenuItem at all (False)
        action_dict         a dictionary of values to pass to action functions. Used to provide context to the action
        case_sensitive      whether choosing menu items should be case sensitive (True) or not (False - default)
        item_filter         a function used to determine which menu items to display. An item is display if the function returns True for the item.
                                All items are displayed if item_filter is None (default)
        refresh             refresh menu items each time the menu is shown (True - default), or just when created (False). Useful for dynamic menus
        header              a format string to print before the table, can use any value from action_dict as well as pagination information
        footer              a format string to print after the table, can use any values from action_dict as well as pagination information
        """
        try:
            self.required = options['required']
        except KeyError:
            self.required = True

        try:
            add_exit = options['add_exit']
            if add_exit in { False, TABLE_ADD_EXIT, TABLE_ADD_RETURN }:
                self.add_exit = add_exit
            else:
                print('Table:__init__: ')
                raise RuntimeError('Table: unexpected value for add_exit option ({})'.format(add_exit))
        except KeyError:
            self.add_exit = TABLE_ADD_EXIT

        try:
            self.action_dict = options['action_dict']
        except KeyError:
            self.action_dict = {}

        try:
            self.case_sensitive = options['case_sensitive']
        except KeyError:
            self.case_sensitive = False

        try:
            self.refresh = options['refresh']
        except KeyError:
            self.refresh = True

        try:
            self.item_filter = options['item_filter']
        except KeyError:
            self.item_filter = None

        try:
            self.header = options['header']
        except KeyError:
            self.header = None

        try:
            self.footer = options['footer']
        except KeyError:
            self.footer = None

        if prompt is None:
            # self.prompt = 'Choose a menu item'
            self.prompt = 'Choose a table item'
        else:
            self.prompt = prompt

        self.options = options
        self.title = title
        self.default_choice = default_choice
        self.default_str= default_str

        if default_action is None or default_action == 'tag':
            self.default_action = return_tag_action
        elif default_action == 'row':
            self.default_action = return_row_action
        elif default_action == 'table_item':
            self.default_action = return_table_item_action
        else:
            self.default_action = default_action

        self.rows_per_page = rows_per_page
        self._table_items = put_in_a_list(rows)             # the original, raw table items for the table
        self._rows = []                     # the expanded, refreshed table items for the table used to create the pretty table
        self.table = pt.VeryPrettyTable()     # the pretty table to display

        # if col_names is None:
        #     if isinstance(self._table_items[0], DynamicTableItem):
        #         # Find the first DynamicTable with data to get the number of columns
        #         # For dynamic tables, need to call the factory method to get a sample row so can determine the number of columns
        #         first_item = None
        #         num_cols = 0
        #
        #         #     for ti in self._table_items:
        #         #         if first_item is None:
        #         #             for first_row in ti.query:
        #         #                 first_item = self._table_items[0].table_item_factory(0, first_row, self._table_items[0].item_data)
        #         #                 if first_item is not None:
        #         #                     num_cols = len(first_item.values)
        #         #                     break
        #         #     # if first_item is None:  # None of the table items had any data
        #         #     #     num_cols = 0
        #         #     # else:
        #         #     #     num_cols = len(first_item.values)
        #         # else:
        #         #     num_cols = len(self._table_items[0].values)
        #
        #         for ti in self._table_items:
        #             # r = ti.next()
        #             r = next(ti.query)
        #             first_item = ti.table_item_factory(0, r, self._table_items[0].item_data)
        #             # if first_item is not None:
        #             if first_item is not None:
        #                 num_cols = len(first_item.values)
        #                 break
        #     else:
        #         num_cols = len(self._table_items[0].values)
        #     num_cols = len(self._table_items[0].values)
        #
        #     field_names = ['col {}'.format(i) for i in range(1, num_cols+1)]
        # elif isstring(col_names):
        if isstring(col_names):
            field_name_list = col_names.split()
            field_names = field_name_list
            num_cols = len(field_name_list)
        else:
            field_names = col_names
            num_cols = len(field_names)

        if len(field_names) != num_cols:
            raise RuntimeError('Table: number of column names does not match number of columns in the table'.format())

        self.field_names = ['tag'] + field_names
        self.table.field_names = ['tag'] + field_names + ['action']

        self.table.set_style(pt.PLAIN_COLUMNS)
        self.table.border = False
        self.table.header = False
        self.table.align = 'l'
        self.table.align['tag'] = 'r'
        # self.tbl.left_padding_width = 2

        if self.refresh is False:   # set up rows to start as won't be refreshed each time called
            self.refresh_items(rows=rows, add_exit=True, item_filter=self.item_filter)

        self.show_rows(0)


    def __repr__(self):
        return 'Table(rows={}, col_name={}, title={}, prompt={}, default_choice={}, action_dict={})'.format(self._table_items,
                                            self.field_names, self.title, self.prompt, self.default_choice, self.action_dict)

    def get_num_rows(self):
        return len(self._rows)

    def get_row(self, tag):
        for row in self._rows:
            if row.tag == tag:
                return row
        raise ValueError('Table.get_row: tag ({}) not in the table'.format(tag))

    def get_action(self, tag):
        row = self.get_row(tag)
        return row.action

    def do_action(self, row):
        action = row.action
        if callable(action):
            return action(row, self.action_dict)
        elif action == 'default' and self.default_action is not None:
            return self.default_action(row, self.action_dict) # TODO - passing row now -- item_data available from row
        else:
            return row

    def show_rows(self, start_row):
        # set the starting and ending rows to show
        table_max_rows = self.get_num_rows()
        if start_row > table_max_rows - self.rows_per_page:
            start_row = table_max_rows - self.rows_per_page

        if start_row < 1:
            self.table.start = 0
        else:
            self.table.start = start_row

        table_end = self.table.start + self.rows_per_page
        if table_end > table_max_rows:
            table_end = table_max_rows

        self.table.end = table_end

    def refresh_buffer(self, buffer):
        if buffer:
            buffer.text = self.table.get_string()
        else:
            print(self.table.get_string())
            print()
            raise RefreshScreenInterrupt


    def page_up(self, buffer=None):
        # page up for the table
        self.show_rows(self.table.start - self.rows_per_page)
        # if buffer:
        #     buffer.text = self.table.get_string()
        self.refresh_buffer(buffer)


    def page_down(self, buffer=None):
        self.show_rows(self.table.start + self.rows_per_page)
        # if buffer:
        #     buffer.text = self.table.get_string()
        self.refresh_buffer(buffer)


    def goto_home(self, buffer=None):
        # page up for the table
        # buff = buffer if buffer is not None else self.buffers['TABLE']
        self.show_rows(0)
        # buff.text = self.table.get_string()
        self.refresh_buffer(buffer)

    def goto_end(self, buffer=None):
        # page up for the table
        # buff = buffer if buffer is not None else self.buffers['TABLE']
        self.show_rows(self.get_num_rows() - self.rows_per_page)
        # buff.text = self.table.get_string()
        self.refresh_buffer(buffer)

    def scroll_up_one_row(self, buffer=None):
        # go up one row
        # buff = buffer if buffer is not None else self.buffers['TABLE']
        self.show_rows(self.table.start + 1)
        # buff.text = self.table.get_string()
        self.refresh_buffer(buffer)


    def scroll_down_one_row(self, buffer=None):
        # go down one row
        buff = buffer if buffer is not None else self.buffers['TABLE']
        self.show_rows(self.table.start - 1)
        buff.text = self.table.get_string()
        self.refresh_buffer(buffer)


    def _prep_get_input(self):
        if self.refresh:
            self.refresh_items(self._table_items, self.add_exit, self.item_filter)
        if len(self._rows) == 0:
            raise RuntimeError('get_menu::_prep_get_input: Table has no rows of data ({}).'.format(self))

        if self.case_sensitive:
            choices = {str(item.tag): i for i, item in enumerate(self._rows) if item.enabled is True}
        else:
            choices = {str(item.tag).lower(): i for i, item in enumerate(self._rows) if item.enabled is True}

        cleaners = [StripCleaner()]
        if not self.case_sensitive:
            cleaners.append(CapitalizationCleaner('lower'))
        cleaners.append(ChoiceCleaner(choices))

        convertor = ChoiceConvertor(choices)
        #validators = RangeValidator(min_val=0, max_val=max(choices.values()))   # TODO - This is wrong... only works for integers? Should be ChoiceValidator?
        validators = ChoiceValidator(choices.values())

        return choices, cleaners, convertor, validators

    def screen_refresher(self, buffer=None):
        # use a closure to set the values so the function can be called without without the self reference
        header = self.header
        action_dict = self.action_dict
        title = self.title
        table = self.table
        field_names = self.field_names
        footer = self.footer
        buffer = buffer

        def refresh_screen():
            formatter = string.Formatter()

            # print header
            if header:
                print(formatter.vformat(header, None, action_dict))

            # print table
            if title is not None:
                print('{}'.format(title))

            print(table.get_string(fields=field_names))  # don't show action

            # print footer
            if footer:
                print(formatter.vformat(footer, None, action_dict))

        return refresh_screen

    # def refresh_screen(self):
    #     formatter = string.Formatter()
    #
    #     # print header
    #     if self.header:
    #         print(formatter.vformat(self.header, None, self.action_dict))
    #
    #     # print table
    #     if self.title is not None:
    #         print('{}'.format(self.title))
    #
    #     print(self.table.get_string(fields=self.field_names))  # don't show action
    #
    #     # print footer
    #     if self.footer:
    #         print(formatter.vformat(self.footer, None, self.action_dict))
    #
    #     return self.screen_refresher()

    def choice_refresher(self):
        # use a closure to set the values so the function can be called without without the self reference
        table = self

        def refresh_choices():
            return table._prep_get_input()

        return refresh_choices


    # def _get_choice(self, table_choices, table_cleaners, table_convertor, table_validators, **options):
    def _get_choice(self, **options):
        gi_options = {}
        gi_options['prompt'] = self.prompt
        gi_options['required'] = self.required
        gi_options['default'] = self.default_choice
        gi_options['default_str'] = self.default_str
        for k,v in options.items():
            gi_options[k] = v

        # formatter = string.Formatter()
        #
        # # print header
        # if self.header:
        #     print( formatter.vformat(self.header, None, self.action_dict) )
        #
        # # print table
        # if self.title is not None:
        #     print('{}'.format(self.title))
        #
        # print(self.table.get_string(fields=self.field_names))  # don't show action
        #
        # # print footer
        # if self.footer:
        #     print( formatter.vformat(self.footer, None, self.action_dict) )
        screen_refresher = self.screen_refresher()
        gi_options['screen_refresh_action'] = screen_refresher
        # gi_options['refresh_action'] = screen_refresher

        choice_refresher = self.choice_refresher()
        table_choices, table_cleaners, table_convertor, table_validators = choice_refresher()
        gi_options['choice_refresh_action'] = choice_refresher
        # table_choices, table_cleaners, table_convertor, table_validators = self._prep_get_input()

        self.show_rows(0)
        screen_refresher()  # need to refresh screen after choice refresh or dynamic tables won't show any rows

        result = get_input(cleaners=table_cleaners, convertor=table_convertor, validators=table_validators, **gi_options)

        if result is None:
            return None
        else:
            return self._rows[result]

    def get_table_choice(self, do_action=True, **options):
        # TODO - document - get the choice from the table - does not run the action...
        # TODO - can raise GetInputInterrupt... handle here or not?

        # if True:
        #     use_key_registry = default_key_registry
        # else:
        #     use_key_registry = Registry()
        #     use_key_registry.key_bindings.extend(default_key_registry.key_bindings)
        #     # key_registry =  default_key_registry
        #
        # if 'key_registry' in options:
        #     # key_registry = options['key_registry']
        #     options_key_registry = options['key_registry']
        #     use_key_registry.key_bindings.extend(options_key_registry.key_bindings)

        if 'key_registry' in options:
            use_key_registry = options['key_registry']
            # register_table_keys(options['key_registry'], self, 'DEFAULT_BUFFER')
        else:
            use_key_registry = default_key_registry
            # register_table_keys(default_key_registry, self, 'DEFAULT_BUFFER')

        register_table_keys(use_key_registry, self, 'DEFAULT_BUFFER')

        # table_choices, table_cleaners, table_convertor, table_validators = self._prep_get_input()
        # self.show_rows(0)
        # row = self._get_choice(table_choices, table_cleaners, table_convertor, table_validators, **options)
        row = self._get_choice(**options)

        if row is None:
            # return 'exit'
            return None
        else:
            return self.do_action(row)

    def refresh_items(self, rows=None, add_exit=False, item_filter=None):
        # Used to update rows in the table. Adds tags if necessary. formatter is used so
        # values can be substituted in format strings from action_dict using vformat.
        formatter = string.Formatter()

        if rows is None:
            use_rows = self._table_items
        elif isinstance(rows, TableItem):  # single item, not list
            use_rows = [rows]
        else:
            use_rows = rows

        self.table.clear_rows()
        self._rows = []

        table_idx = 1

        table_items = []
        for item in use_rows:
            if isinstance(item, DynamicTableItem):  # expand dynamic rows
                table_items.extend(item())
            else:
                table_items.append(item)

        if item_filter is None or item_filter is True:
            filtered_items = table_items
        elif callable(item_filter):
            filtered_items = []
            for item in table_items:
                if item_filter(item, self.action_dict):
                    filtered_items.append(item)

        for item in filtered_items:
        # for item in table_items:
            if item.tag is None:
                tag_str = '{:3}'.format(table_idx)
                tag = table_idx
            else:
                tag = tag_str = item.tag

            # try:
            #     item_values = [formatter.vformat(str(v), None, self.action_dict) for v in item.values]
            # except (ValueError):
            #     # a curly brace in the value causes a ValueError exception. Double it up to fix this.
            #     item_values = []
            #     for v in item.values:
            #         # v2 = str(item.values).replace('}', '}}').replace('{', '{{')
            #         v2 = str(v).replace('}', '}}').replace('{', '{{')
            #         item_values.append(v2)

            item_values = []
            for v in item.values:
                if isstring(v):
                    # a curly brace in the value causes a ValueError exception. Double it up to fix this.
                    v2 = str(v).replace('}', '}}').replace('{', '{{')
                    formatted_val = formatter.vformat(str(v2), None, self.action_dict)
                    item_values.append(formatted_val)
                else:
                    item_values.append(v)

            row_entry = TableItem(item_values, tag, item.action, item_data=item.item_data, hidden=item.hidden, enabled=item.enabled)

            ###
            # if item_filter is None or item_filter is True or (callable(item_filter) and item_filter(item, self.action_dict)):
            #     if item.hidden is not True:
            #         self.table.add_row([tag_str] + item_values + [item.action])
            ###

            # if item.hidden is not True:
            #     self.table.add_row([tag_str] + item_values + [item.action])

            self._rows.append(row_entry)
            table_idx += 1

        if add_exit and self.add_exit:
            num_values = 1
            # if len(filtered_items):
            if len(self._rows):
                # num_values = len(filtered_items[0].values)
                num_values = len(self._rows[0].values)
            row_values = ['' for i in range(num_values)]
            if self.add_exit == TABLE_ADD_EXIT:
                row_tag, row_action = 'exit', TABLE_ACTION_EXIT
            elif self.add_exit == TABLE_ADD_RETURN:
                row_tag, row_action = 'return', TABLE_ACTION_EXIT

            row_entry = TableItem(row_values, row_tag, row_action)

            self.table.add_row([row_entry.tag] + row_entry.values + [row_entry.action])
            self._rows.append(row_entry)

        # refresh table
        self.table.clear_rows()
        table_idx =1
        for r in self._rows:
            if item.hidden is not True:
                # self.table.add_row([tag_str] + item_values + [item.action])
                self.table.add_row([r.tag] + r.values + [r.action])
            table_idx += 1

        if self.table.start > self.get_num_rows():
            # filtering can cause the table to not show any rows. If so, show last page of filtered table
            start_row = max(self.get_num_rows() - self.rows_per_page, 0)
            self.show_rows(start_row)


    def __call__(self, tag=None, action_dict={}, item_data={}):
        """
        This makes tables convenient by making them callable. To call the run method on a table just call the
        table like a function: (i.e. my_table()). The reason it takes takes, args, and kwargs is so it can be
        used for submenus by putting the menu as the action for the TableItem.

        :param tag: tag the table was called with (used for submenus)
        :param args: arg list the table was called with (used for submenus)
        :param kwargs: keyword arg dictionary the table was called with (used for submenus)
        :return: the status from run.
        """
        # return self.run(**kwargs)
        return self.run()

    def run(self):
        table_choices, table_cleaners, table_convertor, table_validators = self._prep_get_input()
        self.show_rows(0)

        options = {'prompt': self.prompt}

        while True:
            try:
                #choice = self._get_choice(table_choices, table_cleaners, table_convertor, table_validators, **options)
                choice = self._get_choice(**options)
            except (GetInputInterrupt) as gii:
                print('\n{}\n'.format(gii))
                continue

            if choice is None:
                action - TABLE_ACTION_EXIT
            else:
                action = choice.action

            if action == TABLE_ACTION_EXIT:
                break
            elif action == TABLE_ACTION_RETURN:
                break
            elif action == TABLE_DEFAULT_ACTION:
                if callable(self.default_action):
                    try:
                        self.default_action(choice, self.action_dict)
                    except (GetInputInterrupt) as gii:
                        print('\n{}\n'.format(gii))
                        return False
                else:
                    print('Table:run: default_action not set for {}'.format(choice), file=sys.stderr)
            elif callable(action):
                try:
                    action(choice, self.action_dict)
                except (GetInputInterrupt) as gii:
                    print('\n{}\n'.format(gii))
                    continue
            else:
                print('Table.run - no action specified for {}'.format(choice), file=sys.stderr)

            if self.refresh:
                table_choices, table_cleaners, table_convertor, table_validators = self._prep_get_input()
                self.show_rows(self.table.start)

        return True


def get_menu(choices, title=None, prompt=None, default_choice=None, add_exit=False, **kwargs):
    # TODO - document!
    menu_choices = [TableItem(choice) for choice in choices]
    default_str = default_choice
    default_idx = None

    # return the tag for the menu item unless the user set a specific default action.
    menu_options = dict(**kwargs)

    if 'default_action' not in kwargs:
        menu_options['default_action'] = return_tag_action

    if default_choice is not None:
        for i,mc in enumerate(menu_choices):
            try:
                if mc.tag is not None and mc.tag == default_choice:
                    default_idx = i+1
                elif mc.values[0] == default_choice:
                    default_idx = i+1
                elif mc.tag is None and i == int(default_choice):
                    default_idx = i+1
                break
            except ValueError:
                pass

    #menu = Table(menu_choices, title=title, prompt=prompt, default_choice=default_idx, default_str=default_str,
    #            add_exit=add_exit, **kwargs)
    menu = Table(menu_choices, title=title, prompt=prompt, default_choice=default_idx, default_str=default_str,
                add_exit=add_exit, **menu_options)
    result = menu.get_table_choice()

    if result is None:
        return 'exit'

    if add_exit and result=='exit':
        return result

    return result


# TODO - Note, this is not being used for now!
def get_table_input(self, cleaners=None, convertor=None, validators=None, do_action=False, **options):
    # TODO - document!
    # process options - TODO - too much duplicated code with get_input..
    prompt_str = ''
    required = True
    default_val = None
    default_string = None
    hidden = False
    # error_callback = print_error
    # convertor_error_fmt = DEFAULT_CONVERTOR_ERROR
    # validator_error_fmt = DEFAULT_VALIDATOR_ERROR
    # use_prompt_toolkit = True
    key_registry = default_key_registry
    # use_bottom_toolbar = False
    # bottom_toolbar_str = 'Ctrl-D to abort'
    # bottom_toolbar_str = ''

    # converted_response = None
    # valid_response = None

    for k, v in options.items():
        if k == 'prompt':
            prompt_str = '%s' % v
        elif k == 'required':
            required = True if v else False
        elif k == 'default':
            if v is None:
                default_val = None
            else:
                default_val = str(v)
        elif k == 'default_str':  # for get_from_table may want to display value but return id.
            default_string = v
        elif k == 'hidden':
            hidden = v
        # elif k == 'retries':
        #     max_retries = v
        # elif k == 'error_callback':
        #     error_callback = v
        # elif k == 'convertor_error_fmt':
        #     convertor_error_fmt = v
        # elif k == 'validator_error_fmt':
        #     validator_error_fmt = v
        # elif k == 'use_prompt_toolkit':
        #     use_prompt_toolkit = v
        # elif k == 'use_bottom_toolbar':
        #     use_bottom_toolbar = v
        # elif k == 'bottom_toolbar_str':
        #     bottom_toolbar_str = v
        elif k == 'key_registry':
            key_registry = v
        else:
            logging.warning('Warning: get_input received unknown option (%s)' % k)

    if default_val is not None and not default_string:
        default_string = str(default_val)

    if default_val is not None:
        # TODO - have a way to set blank if there is a default_val... a command like 'blank' or 'erase'?
        # logging.warning('Warning: both required and a default value specified. Blank inputs will use default value.')
        required = True

    if not required and not default_val:
        default_str = ' (enter to leave blank)'
    elif default_val:
        default_str = ' (enter for: %s)' % default_string
    else:
        default_str = ''
    ####

    buffers = {
        'DEFAULT_BUFFER': Buffer(is_multiline=True),
        'PROMPT_STR_BUFFER': Buffer(is_multiline=True),
        'TABLE': Buffer(is_multiline=True),
    }
    buffers['TABLE'].text = ptable.table.get_string()
    buffers['PROMPT_STR_BUFFER'].text = prompt_str

    manager = KeyBindingManager()
    registry = manager.registry
    register_table_keys(registry)
    # print(ptable.table.get_string())

    table_layout = Window(height=LayoutDimension.exact(26), content=BufferControl(buffer_name='TABLE'))
    prompt_str_layout = Window(width=LayoutDimension.exact(len(prompt_str) + 1), height=LayoutDimension.exact(3),
                               content=BufferControl(buffer_name='PROMPT_STR_BUFFER'))
    prompt_input_layout = Window(height=LayoutDimension.exact(3), content=BufferControl(buffer_name='DEFAULT_BUFFER'))
    prompt_line_layout = VSplit(children=[prompt_str_layout, prompt_input_layout])
    layout = HSplit(children=[table_layout, prompt_line_layout])

    try:
        loop = create_eventloop()
        application = Application(key_bindings_registry=registry, layout=layout, buffers=buffers,
                                  use_alternate_screen=True)
        cli = CommandLineInterface(application=application, eventloop=loop)
        result = cli.run()
        print('result={}'.format(result))
    finally:
        loop.close()

    if do_action:
        return self.do_action()
    else:
        return result
