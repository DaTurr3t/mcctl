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


def spinner(frame, variant=0):
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

    assert variant >= 0, "Invalid Index '{0}'. Must be from 0 to {1}".format(
        variant, len(spinners))

    speed = spinners[variant]['speed']
    idx = int((frame*speed/100) % len(spinners[variant]['chars']))
    return spinners[variant]["chars"][idx]


def compute(length=1):
    min = 10240
    max = 10495

    out = ''
    for _ in range(length):
        out += chr(random.randint(min, max))
    return out
