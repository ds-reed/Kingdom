# terminal_style.py
# OLD_SCHOOL uses TRS-80 inspired terminal styling for text adventure  
# MODE_MODERN is a more standard modern terminal style 


import os
from pydoc import text
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

#OLD_SCHOOL shades for a more authentic look
OLD_SCHOOL_WHITE = "\033[38;2;220;220;255m"  # subtle bluish tint
SHOW_STATUS_BANNER = False
TERMINAL_MODE_OLD_SCHOOL = "OLD_SCHOOL"
TERMINAL_MODE_MODERN = "modern"
ACTIVE_TERMINAL_MODE = TERMINAL_MODE_MODERN


import time

BAUD_DELAY = 0.0001  #  9600 baud

OLD_SCHOOL_ALLOWED = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?;:'\"()[]/-+*=<> "
    "█▓▒░▀▄▌▐─│┌┐└┘┬┴┤├┼♥♦♣♠╱╲╳"
)

def tty_set_terminal_mode(mode):
        global ACTIVE_TERMINAL_MODE
        ACTIVE_TERMINAL_MODE = mode

def set_session_logger(logger):
    global session_logger
    session_logger = logger


def _OLD_SCHOOL_sanitize(text: str) -> str:
    return "".join(ch if ch in OLD_SCHOOL_ALLOWED else " " for ch in text)

def _wrap_width(text: str, width=64) -> list[str]:
    words = text.split()
    lines = []
    current = ""

    for w in words:
        # If adding the next word would exceed width chars, start a new line
        if len(current) + len(w) + (1 if current else 0) > width:
            lines.append(current)
            current = w
        else:
            current = w if not current else current + " " + w

    if current:
        lines.append(current)

    return lines


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


def tty_get_terminal_mode():
    return ACTIVE_TERMINAL_MODE

def _apply_mode_case(text) -> str:
    rendered = str(text)
    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_OLD_SCHOOL:
        return rendered.upper()
    return rendered

def tty_clear_screen():
    clear_screen()  

def tty_print(*args, end="\n", **kwargs):
    text = " ".join(str(arg) for arg in args)

    # ------------------------------------------------------------
    # OLD-SCHOOL MODE 
    # ------------------------------------------------------------
    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_OLD_SCHOOL:
        # 1. ALL CAPS
        text = text.upper()

        # 2. TRS-80 character palette
        text = _OLD_SCHOOL_sanitize(text)

        # 3. Split on explicit newlines BEFORE wrapping
        logical_lines = text.split("\n")

        for logical in logical_lines:
            if logical == "":
                # preserve blank lines
                _slow_print("")   # or print("") if slow-print isn't ready
                continue

            # 4. Wrap to 64 columns
            segments = _wrap_width(logical, width=64)

            # 5. Slow-print each wrapped segment
            for seg in segments:
                _slow_print(seg)

        return  # old-school mode does not use `end`

    # ------------------------------------------------------------
    # MODERN MODE 
    # ------------------------------------------------------------
    logical_lines = text.split("\n")

    for logical in logical_lines:
        if logical == "":
            # preserve blank lines
            print("", flush=True)
            continue

        segments = _wrap_width(logical, width=80)

        # Print all wrapped segments except the last with a normal newline
        for seg in segments[:-1]:
            print(seg, flush=True)

        # Print the last segment using the caller's `end`
        print(segments[-1], end=end, flush=True, **kwargs)


def _show_cursor():
    sys.stdout.write(CURSOR_BLOCK)
    sys.stdout.flush()

def _erase_cursor():
    sys.stdout.write("\b \b")
    sys.stdout.flush()

def tty_input_OLD_SCHOOL(prompt="> "):
    # Print prompt in TRS-80 style
    sys.stdout.write(f"{OLD_SCHOOL_WHITE}{prompt.upper()}{RESET}")
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
    if ACTIVE_TERMINAL_MODE == TERMINAL_MODE_OLD_SCHOOL:
        user_input = tty_input_OLD_SCHOOL(prompt_text)
    else:
        styled_prompt = f"{OLD_SCHOOL_WHITE}{_apply_mode_case(prompt_text)}{RESET}"
        print(styled_prompt, end="", flush=True)
        user_input = input()                     # <-- terminal echoes once here

    # ────────────────────────────────────────────────
    #          ADD THIS BLOCK (the actual logging)
    # ────────────────────────────────────────────────
    if session_logger is not None:
        try:
            logfile = session_logger.get_logfile()
            from datetime import datetime
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logfile.write(f"{ts} > {user_input.rstrip()}\n")
            logfile.flush()
        except RuntimeError as e:
            # logger not started → usually safe to ignore
            pass
        except Exception as e:
            # temporary visibility during debugging
            import sys
            print(f"[LOG ERROR in tty_prompt] {type(e).__name__}: {e}", file=sys.__stderr__)

    return user_input

def tty_show_room(content_lines: Sequence[str], clear = True, **kwargs):
    if clear is True:
        clear_screen()
    if content_lines:
        for line in content_lines:
            tty_print(line)

