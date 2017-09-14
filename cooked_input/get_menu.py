"""
get_menu - menu system for cooked_input

Len Wanger, 2017

TODO:

- Examples/scenarios:
    - menus:
        X simple menu (numbered item built from list)
        X pick-once and exit
        X loop w/ pick until exit picked
        - action functions (with args/kwargs for context)
        - sub-menus
        - filter functions (i.e. only choices matching a role)
        - different borders
        - sub-menu with multiple parents
        - dynamic menu - from: list, pretty-table, database, Pandas
        - different display functions (i.e. function for displaying the table - silent_table for no display of menu or table)
        - set user profile - list users, add profile, edit profile
        - use lambda for actions
        - example runner

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
import veryprettytable as pt
from cooked_input import get_input
from .cleaners import CapitalizationCleaner, StripCleaner, ChoiceCleaner
from .convertors import ChoiceIndexConvertor
from .validators import RangeValidator

MENU_DEFAULT_ACTION = 'default'
MENU_ACTION_EXIT = 'exit'


class MenuItem(object):
    def __init__(self, text, tag=None, action=MENU_DEFAULT_ACTION):
        """
        MenuItem is used to represent individual menu items (choices) in the Menu class.

        :param text: the text description to be used for the item in the printed menu
        :param tag:  a value that can be used to choose the item. If None, a default tag will be assigned by the Menu
        :param action:  the action to take when the item is selected

        MenuItem actions:

        +---------------------+--------------------------------------------------------------------------+
        | value               | action                                                                   |
        +---------------------+--------------------------------------------------------------------------+
        | MENU_DEFAULT_ACTION |  use default method to handle the menu item (e.g. call                   |
        |                     |  default_action handler function)                                        |
        +---------------------+--------------------------------------------------------------------------+
        | MENU_ACTION_EXIT    |  the menu item should exit the menu                                      |
        +---------------------+--------------------------------------------------------------------------+

        """
        self.text = text
        self.tag = tag
        self.action = action

    def __repr__(self):
        return 'MenuItem(text={}, tag={}, action={})'.format(self.text, self.tag, self.action)


class Menu(object):
    def __init__(self, rows=(), title=None, prompt=None, default_choice='', default_action=None, **kwargs):
        """

        :param rows:
        :param title:
        :param prompt:
        :param default_choice:
        :param default_action:
        :param kwargs:
        """
        try:
            self.add_exit = kwargs['add_exit']
        except KeyError:
            self.add_exit = True

        try:
            self.action_args = kwargs['action_args']
        except KeyError:
            self.action_args = []

        try:
            self.action_kwargs = kwargs['action_kwargs']
        except KeyError:
            self.action_kwargs = {}

        try:
            self.case_sensitive = kwargs['case_sensitive']
        except KeyError:
            self.case_sensitive = False

        if prompt is None:
            self.prompt = 'Choose a menu item'
        else:
            self.prompt = prompt

        self.title = title
        self.default_choice = default_choice
        self.default_action = default_action
        self._rows = []
        self.tbl = pt.VeryPrettyTable()

        self.tbl.field_names = "tag text action".split()
        self.tbl.set_style(pt.PLAIN_COLUMNS)
        self.tbl.border = False
        self.tbl.header = False
        self.tbl.align = 'l'
        self.tbl.align['tag'] = 'r'
        # self.tbl.left_padding_width = 2

        for i, v in enumerate(rows):
            if v.tag is None:
                r = ['{:3}'.format(i+1), v.text, v.action]
                v.tag = i+1
            else:
                r = [v.tag, v.text, v.action]

            self.tbl.add_row(r)
            self._rows.append(v)

        if self.add_exit:
            r = MenuItem('exit', 'exit', MENU_ACTION_EXIT)
            self.tbl.add_row([r.tag, r.text, r.action])
            self._rows.append(r)

    def __repr__(self):
        return 'Menu(rows=..., title={}, prompt={}, default_choice={}, kwargs=...)'.format(self.title, self.prompt, self.default_choice)

    def get_numchoices(self):
        return len(self._rows)

    def get_action(self, tag):
        for row in self._rows:
            if row.tag == tag:
                return row.action
        raise ValueError('Menu.get_action: tag ({}) not in the menu'.format(tag))

    def _prep_get_input(self):
        choices = tuple(c.tag for c in self._rows)

        # cleaners = [StripCleaner(), CapitalizationCleaner('lower'), ChoiceCleaner(choices)]
        cleaners = [StripCleaner()]
        if not self.case_sensitive:
            cleaners.append(CapitalizationCleaner('lower'))
        cleaners.append(ChoiceCleaner(choices))

        convertor = ChoiceIndexConvertor(choices)
        validators = RangeValidator(min_val=0, max_val=len(choices))
        return choices, cleaners, convertor, validators

    def _get_choice(self, menu_choices, menu_cleaners, menu_convertor, menu_validators):
        if self.title is not None:
            print('{}'.format(self.title))
        print(self.tbl.get_string(fields=['tag', 'text']))  # don't show action
        result = get_input(prompt=self.prompt, cleaners=menu_cleaners, convertor=menu_convertor,
                           validators=menu_validators, default=self.default_choice)

        return self._rows[result]

    def get_menu_choice(self):
        menu_choices, menu_cleaners, menu_convertor, menu_validators = self._prep_get_input()
        row = self._get_choice(menu_choices, menu_cleaners, menu_convertor, menu_validators)
        return row.tag

    def run(self):
        menu_choices, menu_cleaners, menu_convertor, menu_validators = self._prep_get_input()

        while True:
            choice = self._get_choice(menu_choices, menu_cleaners, menu_convertor, menu_validators)
            action = choice.action

            if action == MENU_ACTION_EXIT:
                break
            elif action == MENU_DEFAULT_ACTION:
                self.default_action(choice.tag, self.action_args, self.action_kwargs)
            elif callable(action):
                action(choice.tag, self.action_args, self.action_kwargs)
            else:
                print('Menu.run - no action specified for tag ({})'.format(choice.tag), file=sys.stderr)
        return True


def get_menu(choices, title=None, prompt=None, default_choice='', add_exit=False, **kwargs):
    menu_choices = [MenuItem(choice) for choice in choices]
    menu = Menu(menu_choices, title=title, prompt=prompt, default_choice=default_choice, add_exit=add_exit, **kwargs)
    result = menu.get_menu_choice()

    if add_exit and result=='exit':
        return result

    return menu_choices[result-1].text


### tests ####
def default_action(tag, *args, **kwargs):
    print('called default_action, tag={}, args={} kwargs={}'.format(tag, args, kwargs))
    return True

def action_1(tag, *args, **kwargs):
    print('called action_1')
    return True


def simple_menu():
    menu_choices = [
        MenuItem("Choice 1", None, None),
        MenuItem("Choice 2", 2, MENU_DEFAULT_ACTION),
        MenuItem("Do Foo", 'foo', MENU_DEFAULT_ACTION),
        MenuItem("Do Bar (action_1)", 'bar', action_1),
        MenuItem("STOP the menu!", 'stop', MENU_ACTION_EXIT),
    ]

    print('\nget_menu_choice - add_exit=True\n')
    menu = Menu(menu_choices[:-1])
    choice = menu.get_menu_choice()
    print('choice={}, action={}'.format(choice, menu.get_action(choice)))

    print('\nget_menu_choice - add_exit=False (no exit!), case_sensitive=True, with title\n')
    menu = Menu(menu_choices[:-1], title='My Menu:', add_exit=False, case_sensitive=True)
    choice = menu.get_menu_choice()
    print('choice={}, action={}'.format(choice, menu.get_action(choice)))

    print('\nget_menu_choice - add_exit=False, w/ prompt, default="stop"\n')
    menu = Menu(menu_choices, prompt='Choose or die!', default_choice='stop', default_action=default_action, add_exit=False)
    choice = menu.get_menu_choice()
    print('choice={}, action={}'.format(choice, menu.get_action(choice)))

    print('\nmenu.run - add_exit=True\n')
    menu.run()
    print('done')

def test_get_menu():
    choices = ['red', 'blue', 'green']

    print('test_get_menu:\n')
    print('simplest case:\n')
    result = get_menu(choices)
    print('result={}'.format(result))

    print('\nwith options...\n')
    result = get_menu(choices, title='My Menu', prompt="Choose m'lady", default_choice='red', add_exit=True, case_sensitive=True)
    print('result={}'.format(result))


if __name__ == '__main__':
    test_get_menu()
    # simple_menu()