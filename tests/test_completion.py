#!/usr/bin/env python3
#** *****************************************************************************
# *
# * If not stated otherwise in this file or this component's LICENSE file the
# * following copyright and licenses apply:
# *
# * Copyright 2025 RDK Management
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# * http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# *
#* ******************************************************************************

import argparse
import unittest
import os
from argparse_completion import get_completion

class CompletionTests(unittest.TestCase):
    parser = None

    def setUp(self):
        os.environ['_ARGPARSE_COMPLETE'] = 'complete_bash'
        self.parser = argparse.ArgumentParser('test')
        self.parser.add_argument('POS1', help='Positional 1', choices=['choice1', 'choice2'])
        self.parser.add_argument('POS2', help='Positional 2')
        self.parser.add_argument('-o', '--option', help='Optional', action='store_true')
        subparsers = self.parser.add_subparsers(dest='cmd')
        subparser1 = subparsers.add_parser('subcommand1', aliases=['sub1', 's1'], help='This is the help message')
        subparser2 = subparsers.add_parser('sub')
        subparser2_subparsers = subparser2.add_subparsers(dest='sub2')
        subparser2_subparser = subparser2_subparsers.add_parser('sub2sp1')
        subparser2_subparser.add_argument('--problem')

    def test_no_args(self):
        os.environ['COMP_WORDS'] = ''
        options = get_completion(self.parser)
        self.assertEqual(len(options),6)
        self.assertIn('subcommand1', options)
        self.assertIn('sub1', options)
        self.assertIn('s1', options)
        self.assertIn('choice1', options)
        self.assertIn('choice2', options)
        self.assertIn('sub',options)

    def test_partial_option(self):
        os.environ['COMP_WORDS'] = '--'
        options = get_completion(self.parser)
        self.assertEqual(len(options),2)
        self.assertIn('--option', options)
        self.assertIn('--help', options)

    def test_first_option(self):
        os.environ['COMP_WORDS'] = '-o'
        options = get_completion(self.parser)
        self.assertEqual(len(options),6)

    def test_partial_positional(self):
        os.environ['COMP_WORDS'] = 'choice'
        options = get_completion(self.parser)
        self.assertEqual(len(options),2)
        self.assertIn('choice1', options)
        self.assertIn('choice2', options)

    def test_positional(self):
        os.environ['COMP_WORDS'] = 'choice1'
        options = get_completion(self.parser)
        self.assertEqual(0,len(options))

    def test_subcommand(self):
        os.environ['COMP_WORDS'] = 'subcommand1'
        options = get_completion(self.parser)
        self.assertEqual(len(options), 0)

    def test_subcommand_choice(self):
        os.environ['COMP_WORDS'] = 'sub sub'
        options = get_completion(self.parser)
        self.assertEqual(len(options),1)
        self.assertIn('sub2sp1', options)

    def test_intermixed_subcommand(self):
        os.environ['COMP_WORDS'] = '--option sub'
        options = get_completion(self.parser)
        self.assertEqual(len(options),1)
        self.assertIn('sub2sp1', options)

if __name__ == '__main__':
    unittest.main(verbosity=3)
