#!/usr/bin/env python3

import argparse
import os

from argparse_completion import argparse_completion


def setup_example_parser():
    # It is expected that your apps name is the name of the prog in the parser
    parser = argparse.ArgumentParser('example_argparse_app.py')
    parser.add_argument('--upper',
                        action = 'store_true',
                        help = 'Changes the printed output to uppercase.',
                        default = False)
    parser.add_argument('message',
                        default = False,
                        action = 'store',
                        help = 'Prints "Hello" to the current user.',
                        choices = ['hello', 'goodbye'])
    return parser

def print_hello(upper:bool=False):
    print_string = _message_to_user('Hello')
    if upper:
        print_string = print_string.upper()
    print(print_string)

def print_goodbye(upper:bool=False):
    print_string = _message_to_user('Goodbye')
    if upper:
        print_string = print_string.upper()
    print(print_string)

def _message_to_user(message=str) -> str:
    user = os.getenv('USER','USER')
    ret_str = f'{message} {user}!'
    return ret_str

##### MAIN #####
if __name__ == '__main__':
    PARSER = setup_example_parser()
    if os.getenv('_ARGPARSE_COMPLETE'):
        completion_options = argparse_completion.get_completion(PARSER)
        print('\n'.join(completion_options))
        raise SystemExit(0)
    ARGS = PARSER.parse_args()
    try:
        match ARGS.message:
            case 'hello':
                print_hello(ARGS.upper)
            case 'goodbye':
                print_goodbye(ARGS.upper)
            case _:
                PARSER.print_help()
    except:
        PARSER.print_help()
