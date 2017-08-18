
"""

"""

import sys
import random

def simple_guess():
    number = random.randint(1, 10)
    print('I am thinking of a number between 1 and 10.')

    guess = int(input('Guess what number I am thinking of: '))

    if guess < number:
        print('Buzz.... you guessed too low.')
    elif guess > number:
        print('Buzz.... you guessed too high.')
    else:
        print('Ding ding... you guessed it!')


def robust_guess():
    number = random.randint(1, 10)
    print('I am thinking of a number between 1 and 10.')

    while True:
        if sys.version_info.major > 2:
            result = input('Guess what number I am thinking of: ')
        else:
            result = raw_input('Guess what number I am thinking of: ')

        try:
            guess = int(result)
            if guess < 1 or guess > 10:
                print('Please enter a number between 1 and 10, try again.')
                continue
            break
        except ValueError:
            print('That is not an integer, try again.')

    if guess < number:
        print('Buzz.... you guessed too low.')
    elif guess > number:
        print('Buzz.... you guessed too high.')
    else:
        print('Ding ding... you guessed it!')


from cooked_input import get_input, IntConvertor, InRangeValidator

def get_input_guess():
    number = random.randint(1, 10)
    print('I am thinking of a number between 1 and 10.')
    guess = get_input(prompt='Guess what number I am thinking of', convertor=IntConvertor(),
                      validators=InRangeValidator(min_val=1, max_val=10, ))

    if guess < number:
        print('Buzz.... you guessed too low.')
    elif guess > number:
        print('Buzz.... you guessed too high.')
    else:
        print('Ding ding... you guessed it!')


if __name__ == '__main__':
    simple_guess()
    # robust_guess()
    get_input_guess()