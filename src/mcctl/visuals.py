#!/bin/env python3

# mcctl: A Minecraft Server Management Utility written in Python
# Copyright (C) 2020 Matthias Cotting

# This file is part of mcctl.

# mcctl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# mcctl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with mcctl. If not, see <http:// www.gnu.org/licenses/>.
import random
DASHES = 0
QUARTERCIRCLE = 1
HALFCIRCLE = 2

SPINNERS = [
    {
        "fps": 4,
        "chars": '|/-\\'
    },

    {
        "fps": 8,
        "chars": '◜◝◞◟'
    },
    {
        "fps": 3,
        "chars": '◐◓◑◒'
    }
]


def compute(length: int = 1) -> str:
    """Return a character looking like a panel of blinkling lamps.

    Uses the braille range in unicode to create a 'running' Indicator, showing that a Process is still running.

    Keyword Arguments:
        length (int): Determines how many characters are returned. (default: {1})

    Returns:
        str: A string containig characters that can be animated in subsequent functions.
    """
    c_min = 10240
    c_max = 10495

    out = ''
    for _ in range(length):
        out += chr(random.randint(c_min, c_max))
    return out
