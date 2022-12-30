#!/bin/env python3

# mcctl: A Minecraft Server Management Utility written in Python
# Copyright (C) 2021 Matthias Cotting

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
from typing import Callable
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


def get_fmtbytes(num: int) -> str:
    """Return a string with a Unit (KB up to EB).

    Args:
        num (int): A huge Number.

    Returns:
        str: A human-readable huge Number (e.g. "3.5G").
    """
    units = ['K', 'M', 'G', 'T', 'P', 'E']
    out = ''
    for unit in units:
        num /= 1024
        out = unit
        if abs(num) < 1024:
            break
    return f"{round(num, 2)}{out}"


def progress(current: int, elapsed: float, total: int) -> None:
    """Print Progress.

    Output the progress of the download given blockcount, blocksize and total bytes.

    Arguments:
        downloaded (int): The number of bits recieved.
        elapsed (int): Elapsed time in seconds.
        total (int): The size of the complete File.
    """
    spinner = SPINNERS[1]
    chars = spinner['chars']
    char_idx = int((elapsed * spinner.get('fps')) % len(chars))

    percent = current * 100 / total
    out = f"\r{chars[char_idx]} {percent:3.0f}% {current / 1024 :>{len(str(total // 1024))}.0f}kB / {(total/1024):.0f}kB"
    print(out, end="", flush=True)


def list_selector(choices: list, display: Callable = lambda x: x) -> list:
    """Show a list of choices of which one, a range or all can be selected.

    Args:
        choices (list): A List of potential choices.
        display (Callable, optional): A callable that returns a display value (str) for a specific choice.

    Returns:
        list: [description]
    """
    for i, choice in enumerate(choices, 1):
        print(f"{i}: {display(choice)}")
    num_ans = None
    ans = input("Please specify a number or '0' to select all: ")
    while True:
        try:
            num_ans = int(ans)
        except ValueError:
            pass
        if num_ans and num_ans >= 0 and num_ans < len(choices):
            break
        msg = f"Please specify a valid number between 0 and {len(choices)}: "
        ans = input(msg)

    return choices if ans == 0 else [choices[ans]]


def bool_selector(msg: str) -> bool:
    """Get a definitive answer from the user.

    Args:
        msg (str): The Message the user is shown/asked.

    Returns:
        bool: True if the User answered with "y".
    """
    msg = f"{msg} [y/n]: "
    ans = input(msg).lower()
    while ans not in ("y", "n"):
        ans = input("Please answer [y]es or [n]o: ")
    return ans == "y"


def clear() -> None:
    """Clear the screen on Unix-based Systems."""
    print("\033[2J\033[H", end='', flush=True)
