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


def spinner(frame: int, variant=0) -> str:
    """Return a spinning character.

    Returns a character that when printed on the same position as the previous creates a nice little animation.

    Arguments:
        frame {int} -- The frame of the anmimation.

    Keyword Arguments:
        variant {int} -- The chosen variant (default: {0})

    Returns:
        str -- A string containig a character that can be animated in subsequent functions.
    """

    spinners = [
        {
            "speed": 30,
            "chars": '|/-\\'
        },

        {
            "speed": 60,
            "chars": '◜◝◞◟'
        },
        {
            "speed": 20,
            "chars": '◐◓◑◒'
        }
    ]
    max_idx = len(spinners) - 1
    assert 0 <= variant <= max_idx, "Invalid Index '{0}'. Must be from 0 to {1}".format(
        variant, max_idx)

    speed = spinners[variant]['speed']
    idx = int((frame*speed/100) % len(spinners[variant]['chars']))
    return spinners[variant]["chars"][idx]


def compute(length: int = 1) -> str:
    """Returns a character looking like a panel of blinkling lamps.

    Uses the braille range in unicode to create a 'running' Indicator, showing that a Process is still running.

    Keyword Arguments:
        length {int} -- Determines how many characters are returned. (default: {1})

    Returns:
        str -- A string containig characters that can be animated in subsequent functions.
    """

    c_min = 10240
    c_max = 10495

    out = ''
    for _ in range(length):
        out += chr(random.randint(c_min, c_max))
    return out
