# terminal_style.py
# TRS-80 inspired terminal styling for text adventure  
# Uses ANSI escapes + Unicode block/box drawing characters
# not using unicode for text yet. Need to update

import os
import sys
import msvcrt
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


import time

BAUD_DELAY = 0.0001  #  9600 baud

TRS80_ALLOWED = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?;:'\"()[]/-+*=<> "
    "█▓▒░▀▄▌▐─│┌┐└┘┬┴┤├┼♥♦♣♠╱╲╳"
)

def set_terminal_mode(mode):
    global ACTIVE_TERMINAL_MODE
    ACTIVE_TERMINAL_MODE = mode


def _trs80_sanitize(text: str) -> str:
    return "".join(ch if ch in TRS80_ALLOWED else " " for ch in text)

def _wrap_64(text: str) -> list[str]:
    words = text.split()
    lines = []
    current = ""

    for w in words:
        # If adding the next word would exceed 64 chars, start a new line
        if len(current) + len(w) + (1 if current else 0) > 64:
            lines.append(current)
            current = w
        else:
            current = w if not current else current + " " + w

    if current:
        lines.append(current)

    return lines

def tty_input_trs80(prompt="> "):
    # Print the prompt using TRS-80 styling
    tty_print(prompt, end="")

    buffer = []

    _show_cursor()

    import msvcrt
    while True:
        ch = msvcrt.getwch()

        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(buffer)

        if ch == "\x08":  # backspace
            if buffer:
                buffer.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue

        # Normal character
        up = ch.upper()
        buffer.append(up)
        sys.stdout.write(up)
        sys.stdout.flush()


def _slow_print(text: str):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(BAUD_DELAY)
    sys.stdout.write("\n")
    sys.stdout.flush()


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

CURSOR_BLOCK = "█"


def _apply_mode_case(text) -> str:
    rendered = str(text)
    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_TRS80:
        return rendered.upper()
    return rendered

def tty_clear_screen():
    clear_screen()  

def tty_print(*args, style=TRS80_WHITE, bold=False, dim=False, inverse=False, end="\n", **kwargs):
    text = " ".join(str(arg) for arg in args)

    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_TRS80:
        # 1. ALL CAPS
        text = text.upper()

        # 2. TRS-80 character palette
        text = _trs80_sanitize(text)

        # 3. Wrap to 64 columns
        segments = _wrap_64(text)

        # 4. Slow-print each segment   (not working right now)
        for seg in segments:
            _slow_print(seg)
        return

    # Modern mode (unchanged)
    codes = []
    if bold:
        codes.append(BOLD)
    if dim:
        codes.append(DIM)
    if inverse:
        codes.append(INVERSE)
    codes.append(style)

    prefix = "".join(codes)
    print(f"{prefix}{text}{RESET}", end=end, flush=True, **kwargs)


def trs80_status_line(room_name, score=0, moves=0, light_on=True, width=64, hero_name=None):
    light_text = "LIGHT ON " if light_on else "DARK    "
    hero_text = f" {hero_name[:12]:<12}" if hero_name else ""
    status = f" {room_name[:20]:<20}{hero_text}  Score:{score:>5}  Moves:{moves:>5}  {light_text} "
    filler = " " * max(0, width - len(status))
    tty_print(status + filler, inverse=True, style=TRS80_WHITE)


def trs80_box(title, content_lines, width=60, style=TRS80_WHITE):
    title_padded = title.center(width - 4)
    top = f"{TL_CORNER}{HLINE * (width - 2)}{TR_CORNER}"
    middle = f"{VLINE} {title_padded} {VLINE}"
    sep = f"{T_DOWN}{HLINE * (width - 2)}{T_UP}"
    bottom = f"{BL_CORNER}{HLINE * (width - 2)}{BR_CORNER}"

    tty_print(top, style=style)
    tty_print(middle, style=style)
    tty_print(sep, style=style)

    for line in content_lines:
        padded = str(line)[: width - 4].ljust(width - 4)
        tty_print(f"{VLINE} {padded} {VLINE}", style=style)

    tty_print(bottom, style=style)


def _show_cursor():
    sys.stdout.write(CURSOR_BLOCK)
    sys.stdout.flush()

def _erase_cursor():
    sys.stdout.write("\b \b")
    sys.stdout.flush()

def tty_input_trs80(prompt="> "):
    # Print prompt in TRS-80 style
    sys.stdout.write(f"{TRS80_WHITE}{prompt.upper()}{RESET}")
    sys.stdout.flush()

    buffer = []

    # Show initial cursor
    _show_cursor()


    while True:
        ch = msvcrt.getwch()

        # ENTER
        if ch in ("\r", "\n"):
            _erase_cursor()
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(buffer)

        # BACKSPACE
        if ch == "\x08":
            if buffer:
                buffer.pop()
                _erase_cursor()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
                _show_cursor()
            continue

        # Normal character
        up = ch.upper()
        buffer.append(up)

        _erase_cursor()
        sys.stdout.write(up)
        sys.stdout.flush()
        _show_cursor()



def tty_prompt(prompt_text="> "):
    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_TRS80:
        return tty_input_trs80(prompt_text)

    prompt = f"{TRS80_WHITE}{_apply_mode_case(prompt_text)}{RESET}"
    return input(prompt)


def tty_show_room(content_lines: Sequence[str], clear = True, **kwargs):
    if clear is True:
        clear_screen()
    for line in content_lines:
        tty_print(line, style=TRS80_WHITE)


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

