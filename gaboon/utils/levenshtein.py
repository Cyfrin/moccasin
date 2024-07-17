"""Docopt is a Pythonic command-line interface parser that will make you smile.

Now: with spellcheck, flag extension (de-abbreviation), and capitalization fixes.
(but only when unambiguous)

 * Licensed under terms of MIT license (see LICENSE-MIT)

Contributors (roughly in chronological order):

 * Copyright (c) 2012 Andrew Kassen <atkassen@ucdavis.edu>
 * Copyright (c) 2012 jeffrimko <jeffrimko@gmail.com>
 * Copyright (c) 2012 Andrew Sutton <met48@met48.com>
 * Copyright (c) 2012 Andrew Sutton <met48@met48.com>
 * Copyright (c) 2012 Nima Johari <nimajohari@gmail.com>
 * Copyright (c) 2012-2013 Vladimir Keleshev, vladimir@keleshev.com
 * Copyright (c) 2014-2018 Matt Boersma <matt@sprout.org>
 * Copyright (c) 2016 amir <ladsgroup@gmail.com>
 * Copyright (c) 2015 Benjamin Bach <benjaoming@gmail.com>
 * Copyright (c) 2017 Oleg Bulkin <o.bulkin@gmail.com>
 * Copyright (c) 2018 Iain Barnett <iainspeed@gmail.com>
 * Copyright (c) 2019 itdaniher, itdaniher@gmail.com

"""

from __future__ import annotations

import re
import sys
from typing import Any, Callable, NamedTuple, Tuple, Type, Union, cast

__all__ = ["docopt", "DocoptExit", "ParsedOptions"]
__version__ = "0.9.0"


def levenshtein_norm(source: str, target: str) -> float:
    """Returns float in the range 0-1, with 1 meaning the biggest possible distance"""
    distance = _levenshtein(source, target)
    return distance / max(len(source), len(target))


def _levenshtein(source: str, target: str) -> int:
    """Computes the Levenshtein distances between two strings

    Uses the Wagner-Fischer algorithm
    (https://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm).
    These distances are defined recursively, since the distance between two
    strings is just the cost of adjusting the last one or two characters plus
    the distance between the prefixes that exclude these characters (e.g. the
    distance between "tester" and "tested" is 1 + the distance between "teste"
    and "teste"). The Wagner-Fischer algorithm retains this idea but eliminates
    redundant computations by storing the distances between various prefixes in
    a matrix that is filled in iteratively.
    """

    # Create matrix of correct size (this is s_len + 1 * t_len + 1 so that the
    # empty prefixes "" can also be included). The leftmost column represents
    # transforming various source prefixes into an empty string, which can
    # always be done by deleting all characters in the respective prefix, and
    # the top row represents transforming the empty string into various target
    # prefixes, which can always be done by inserting every character in the
    # respective prefix. The ternary used to build the list should ensure that
    # this row and column are now filled correctly
    s_range = range(len(source) + 1)
    t_range = range(len(target) + 1)
    matrix = [[(i if j == 0 else j) for j in t_range] for i in s_range]

    for i in s_range[1:]:
        for j in t_range[1:]:
            # Applies the recursive logic outlined above using the values
            # stored in the matrix so far. The options for the last pair of
            # characters are deletion, insertion, and substitution, which
            # amount to dropping the source character, the target character,
            # or both and then calculating the distance for the resulting
            # prefix combo. If the characters at this point are the same, the
            # situation can be thought of as a free substitution
            del_dist = matrix[i - 1][j] + 1
            ins_dist = matrix[i][j - 1] + 1
            sub_trans_cost = 0 if source[i - 1] == target[j - 1] else 1
            sub_dist = matrix[i - 1][j - 1] + sub_trans_cost

            # Choose option that produces smallest distance
            matrix[i][j] = min(del_dist, ins_dist, sub_dist)

    # At this point, the matrix is full, and the biggest prefixes are just the
    # strings themselves, so this is the desired distance
    return matrix[len(source)][len(target)]
