import os
import json
import re
import shutil
import unittest

from supporting_files import utils, templates

class RuleTestCases(unittest.TestCase):

    def test_rule_initialize_switch(self):
        rule = templates.Rule({
            'template': 'test',
            'where': { 'x': True },
            'initialize': {
                'Property': {
                    '$switch': {
                        '$on': 'value',
                        '$cases': [
                            { '$eq': 'foo', '$value': 'found_foo' },
                            { '$eq': 'bar', '$value': 'found_bar' },
                            { '$default': True, '$value': 'found_nothing' }
                        ]
                    }
                }
            }
        })

        context = { 'value': 'foo' }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'found_foo' } )

        context = { 'value': 'bar' }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'found_bar' } )

        context = { 'value': 'something_else' }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'found_nothing' } )

    def test_rule_initialize_switch_lists(self):
        rule = templates.Rule({
            'template': 'test',
            'where': { 'x': True },
            'initialize': {
                'Property': {
                    '$switch': {
                        '$on': 'value',
                        '$cases': [
                            { '$eq': ['a', 'b', 'c'], '$value': 'match1' },
                            { '$eq': ['a', 'd'], '$value': 'match2' },
                            { '$default': True, '$value': 'no_match' }
                        ]
                    }
                }
            }
        })

        context = { 'value': ['c', 'b', 'a'] }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'match1' } )

        context = { 'value': ['a', 'd'] }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'match2' } )

        context = { 'value': ['a', 'b'] }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'no_match' } )

        context = { 'value': ['a', 'b', 'c', 'd'] }
        info = { }
        rule.initializeProperties(info, context)
        self.assertEqual( info, { 'Property': 'no_match' } )

