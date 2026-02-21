# terminal_style.py
# TRS-80 inspired terminal styling for text adventure (green phosphor look)
# Uses ANSI escapes + Unicode block/box drawing characters

import os
import sys
from typing import Sequence

# ANSI Escape Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
INVERSE = "\033[7m"

# Green phosphor shades
GREEN = "\033[32m"
DIM_GREEN = "\033[2;32m"
BRIGHT_GREEN = "\033[92m"
AMBER = "\033[33m"
BRIGHT_AMBER = "\033[93m"

#TRS-80 shades for a more authentic look
TRS80_WHITE = "\033[38;2;220;220;255m"  # subtle bluish tint
SHOW_STATUS_BANNER = False
TERMINAL_MODE_TRS80 = "trs80"
TERMINAL_MODE_MODERN = "modern"
ACTIVE_TERMINAL_MODE = TERMINAL_MODE_MODERN

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def set_terminal_size(columns=64, lines=16):
    if os.name == "nt":
        os.system(f"mode con: cols={columns} lines={lines}")
        return
    # ANSI escape: ESC [ 8 ; <lines> ; <cols> t
    print(f"\033[8;{lines};{columns}t", end="", flush=True)


# Box drawing
TL_CORNER = "┌"
TR_CORNER = "┐"
BL_CORNER = "└"
BR_CORNER = "┘"
HLINE = "─"
VLINE = "│"
T_DOWN = "┬"
T_UP = "┴"
CROSS = "┼"

# Block graphics
BLOCK_FULL = "█"
BLOCK_DARK = "▓"
BLOCK_MED = "▒"
BLOCK_LIGHT = "░"
BLOCK_EMPTY = " "

HALF_TOP = "▀"
HALF_BOTTOM = "▄"
HALF_LEFT = "▌"
HALF_RIGHT = "▐"


def _apply_mode_case(text) -> str:
    rendered = str(text)
    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_TRS80:
        return rendered.upper()
    return rendered


def trs80_print(text, style=TRS80_WHITE, bold=False, dim=False, inverse=False, end="\n"):
    codes = []
    if bold:
        codes.append(BOLD)
    if dim:
        codes.append(DIM)
    if inverse:
        codes.append(INVERSE)
    codes.append(style)
    prefix = "".join(codes)
    print(f"{prefix}{_apply_mode_case(text)}{RESET}", end=end, flush=True)


def trs80_status_line(room_name, score=0, moves=0, light_on=True, width=64, hero_name=None):
    light_text = "LIGHT ON " if light_on else "DARK    "
    hero_text = f" {hero_name[:12]:<12}" if hero_name else ""
    status = f" {room_name[:20]:<20}{hero_text}  Score:{score:>5}  Moves:{moves:>5}  {light_text} "
    filler = " " * max(0, width - len(status))
    trs80_print(status + filler, inverse=True, style=TRS80_WHITE)


def trs80_box(title, content_lines, width=60, style=TRS80_WHITE):
    title_padded = title.center(width - 4)
    top = f"{TL_CORNER}{HLINE * (width - 2)}{TR_CORNER}"
    middle = f"{VLINE} {title_padded} {VLINE}"
    sep = f"{T_DOWN}{HLINE * (width - 2)}{T_UP}"
    bottom = f"{BL_CORNER}{HLINE * (width - 2)}{BR_CORNER}"

    trs80_print(top, style=style)
    trs80_print(middle, style=style)
    trs80_print(sep, style=style)

    for line in content_lines:
        padded = str(line)[: width - 4].ljust(width - 4)
        trs80_print(f"{VLINE} {padded} {VLINE}", style=style)

    trs80_print(bottom, style=style)


def trs80_prompt(prompt_text="> "):
    prompt = f"{TRS80_WHITE}{_apply_mode_case(prompt_text)}{RESET}"
    return input(prompt)


def trs80_clear_and_show_room(
    room_name: str,
    content_lines: Sequence[str],
    score=0,
    moves=0,
    light_on=True,
    hero_name=None,
    clear=True,
    show_status=None,
):
    if clear:
        clear_screen()
    if show_status is None:
        show_status = SHOW_STATUS_BANNER
    if show_status:
        trs80_status_line(room_name, score, moves, light_on, hero_name=hero_name)
        print()

    trs80_print(str(room_name), bold=True, style=TRS80_WHITE)
    for line in content_lines:
        trs80_print(line, style=TRS80_WHITE)


if __name__ == "__main__":
    set_terminal_size(64, 16)
    clear_screen()
    trs80_status_line("Entrance Hall", score=35, moves=12, light_on=False)
    print()

    trs80_box(
        "QUICKSAND WARNING",
        [
            "   ▓▓▓▓▓▓▓▓▓   ",
            "  YOU ARE SINKING!  ",
            "   ▓▓▓▓▓▓▓▓▓   ",
            "  DROP SOMETHING HEAVY!",
        ],
        width=44,
        style=TRS80_WHITE,
    )

