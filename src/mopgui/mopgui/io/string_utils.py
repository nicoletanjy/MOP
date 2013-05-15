"""
Utility string functions for parsing.
"""

__author__ = "David Rusk <drusk@uvic.ca>"

import re


def split_2_or_more_spaces(string):
    """
    Split a string into a list of strings based on where there is more than
    one space.
    """
    return re.findall("([\w\d\.]+(?:[ ]?[\w\d\.]+)*)", string)
