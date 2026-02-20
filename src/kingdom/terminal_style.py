# terminal_style.py
# TRS-80 inspired terminal styling for text adventure (green phosphor look)
# Uses ANSI escapes + Unicode block/box drawing characters
# Compatible with modern terminals: Windows Terminal, iTerm2, Kitty, Alacritty, VS Code integrated, etc.

import os
import sys
import random  # only if you want random "CRT flicker" effect later

# ────────────────────────────────────────────────
# ANSI Escape Codes
# ────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
INVERSE = "\033[7m"          # black text on colored bg (status line)

# Green phosphor shades (most authentic for TRS-80 Model I/III)
GREEN = "\033[32m"           # standard green
DIM_GREEN = "\033[2;32m"     # faded/older monitor look
BRIGHT_GREEN = "\033[92m"    # bright green (if terminal supports)
AMBER = "\033[33m"           # alternative amber monitor look
BRIGHT_AMBER = "\033[93m"

# Clear screen (cross-platform)
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ────────────────────────────────────────────────
# Block / Box Drawing Characters (Unicode)
# ────────────────────────────────────────────────

# Basic box drawing (for borders, status, ASCII art)
TL_CORNER = "┌"
TR_CORNER = "┐"
BL_CORNER = "└"
BR_CORNER = "┘"
HLINE     = "─"
VLINE     = "│"
T_DOWN    = "┬"
T_UP      = "┴"
CROSS     = "┼"

# Semigraphics / block "pixels" (approximates TRS-80 semigraphics mode)
BLOCK_FULL  = "█"
BLOCK_DARK  = "▓"
BLOCK_MED   = "▒"
BLOCK_LIGHT = "░"
BLOCK_EMPTY = " "

# Half-blocks for crude graphics
HALF_TOP    = "▀"
HALF_BOTTOM = "▄"
HALF_LEFT   = "▌"
HALF_RIGHT  = "▐"

# ────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────

def trs80_print(text, style=GREEN, bold=False, dim=False, inverse=False, end="\n"):
    """Print text with TRS-80 style."""
    codes = []
    if bold:   codes.append(BOLD)
    if dim:    codes.append(DIM)
    if inverse: codes.append(INVERSE)
    codes.append(style)
    
    prefix = "".join(codes)
    print(f"{prefix}{text}{RESET}", end=end, flush=True)

def trs80_status_line(room_name, score=0, moves=0, light_on=True, width=64):
    """Draw a classic top/bottom status bar (inverse video)."""
    light_text = "LIGHT ON " if light_on else "DARK    "
    status = f" {room_name[:20]:<20}  Score:{score:>5}  Moves:{moves:>5}  {light_text} "
    filler = " " * (width - len(status))
    
    trs80_print(" " * width, inverse=True, style=GREEN, end="")
    trs80_print(status + filler, inverse=True, style=GREEN, end="")
    trs80_print(" " * width, inverse=True, style=GREEN)

def trs80_box(title, content_lines, width=60, style=GREEN):
    """Draw a boxed area (like ASCII art rooms or messages)."""
    title_padded = title.center(width - 4)
    top    = f"{TL_CORNER}{HLINE * (width-2)}{TR_CORNER}"
    middle = f"{VLINE} {title_padded} {VLINE}"
    sep    = f"{T_DOWN}{HLINE * (width-2)}{T_UP}"
    bottom = f"{BL_CORNER}{HLINE * (width-2)}{BR_CORNER}"
    
    trs80_print(top, style=style)
    trs80_print(middle, style=style)
    trs80_print(sep, style=style)
    
    for line in content_lines:
        padded = line[:width-4].ljust(width-4)
        trs80_print(f"{VLINE} {padded} {VLINE}", style=style)
    
    trs80_print(bottom, style=style)

def trs80_prompt():
    """Input prompt with TRS-80 green cursor feel."""
    trs80_print("> ", style=BRIGHT_GREEN, end="")
    return input().strip()

def trs80_clear_and_show_room(room, score=0, moves=0, light_on=True):
    """Typical turn refresh: clear, status, room desc, contents."""
    clear_screen()
    trs80_status_line(room.name, score, moves, light_on)
    print()  # spacer
    trs80_print(room.name.upper(), bold=True, style=BRIGHT_GREEN)
    trs80_print(room.description, style=DIM_GREEN)
    # Add your items/boxes/directions listing here...

# ────────────────────────────────────────────────
# Example Usage (test / demo)
# ────────────────────────────────────────────────

if __name__ == "__main__":
    clear_screen()
    
    # Status bar example
    trs80_status_line("Entrance Hall", score=35, moves=12, light_on=False)
    print()
    
    # Boxed message / ASCII art example
    trs80_box(
        "QUICKSAND WARNING",
        [
            "   ▓▓▓▓▓▓▓▓▓   ",
            "  YOU ARE SINKING!  ",
            "   ▓▓▓▓▓▓▓▓▓   ",
            "  DROP SOMETHING HE