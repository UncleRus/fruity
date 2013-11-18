# -*- coding: utf-8 -*-

from . import *

FUNCTION_4BIT_1LINE = 0x20      # 4-bit interface, single line, 5x7 dots
FUNCTION_4BIT_2LINES = 0x28     # 4-bit interface, dual line,   5x7 dots
FUNCTION_8BIT_1LINE = 0x30      # 8-bit interface, single line, 5x7 dots 0b00110000
FUNCTION_8BIT_2LINES = 0x38     # 8-bit interface, dual line,   5x7 dots

CMD_DISP_OFF = 0x08             # display off
CMD_DISP_ON = 0x0C              # display on, cursor off
CMD_DISP_ON_BLINK = 0x0D        # display on, cursor off, blink char
CMD_DISP_ON_CURSOR = 0x0E       # display on, cursor on
CMD_DISP_ON_CURSOR_BLINK = 0x0F # display on, cursor on, blink char

REG_CLR = 0                     # DB0: clear display
REG_HOME = 1                    # DB1: return to home position
REG_ENTRY_MODE = 2              # DB2: set entry mode
REG_ENTRY_INC = 1               # DB1: 1=increment, 0=decrement
REG_ENTRY_SHIFT = 0             # DB2: 1=display shift on
REG_ON = 3                      # DB3: turn lcd/cursor on
REG_ON_DISPLAY = 2              # DB2: turn display on
REG_ON_CURSOR = 1               # DB1: turn cursor on
REG_ON_BLINK = 0                # DB0: blinking cursor ?
REG_MOVE = 4                    # DB4: move cursor/display
REG_MOVE_DISP = 3               # DB3: move display (0-> cursor) ?
REG_MOVE_RIGHT = 2              # DB2: move right (0-> left) ?
REG_FUNCTION = 5                # DB5: function set
REG_FUNCTION_8BIT = 4           # DB4: set 8BIT mode (0->4BIT mode)
REG_FUNCTION_2LINES = 3         # DB3: two lines (0->one line)
REG_FUNCTION_10DOTS = 2         # DB2: 5x10 font (0->5x7 font)
REG_CGRAM = 6                   # DB6: set CG RAM address
REG_DDRAM = 7                   # DB7: set DD RAM address
REG_BUSY = 7                    # DB7: LCD is busy


_lines_offsets = (0x0, 0x40, 0x14, 0x54)


class HD44780 (object):

    def __init__ (self, pin_rs = 2, pin_e = 3, pins_db = (27, 22, 23, 24), lines = 2, cols = 16):
        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_db = pins_db
        self.lines = lines
        self.cols = cols
        self._pos = [0, 0]

        RPIO.setup (self.pin_rs, RPIO.OUT, initial = RPIO.LOW)
        RPIO.setup (self.pin_e, RPIO.OUT, initial = RPIO.LOW)

        for pin in self.pins_db:
            RPIO.setup (pin, RPIO.OUT, initial = RPIO.LOW)

        delay_ms (15)

        for _i in xrange (3):
            self._out_high (FUNCTION_8BIT_1LINE)
            self._toggle_e ()
            delay_ms (2)

        self._out_high (FUNCTION_4BIT_1LINE)
        self._toggle_e ()

        self.command (FUNCTION_4BIT_1LINE if lines == 1 else FUNCTION_4BIT_2LINES)
        self.command (CMD_DISP_OFF)
        self.clear ()
        self.command (bv (REG_ENTRY_MODE, REG_ENTRY_INC))
        self.command (CMD_DISP_ON)
        delay_ms (3)

    def _toggle_e (self):
        RPIO.output (self.pin_e, True)
        delay_us (10)
        RPIO.output (self.pin_e, False)

    def _out_low (self, byte):
        for pin in xrange (4):
            RPIO.output (self.pins_db [pin], bool (byte & 1))
            byte = byte >> 1

    def _out_high (self, byte):
        self._out_low (byte >> 4)

    def _write (self, byte, rs = False):
        if isinstance (byte, str):
            byte = ord (byte)

        self._out_high (byte)
        RPIO.output (self.pin_rs, rs)
        self._toggle_e ()

        self._out_low (byte)
        RPIO.output (self.pin_rs, rs)
        self._toggle_e ()

    def command (self, cmd):
        delay_us (10)
        self._write (cmd)
        delay_us (10)

    def clear (self):
        self.line = self.col = 0
        self.command (bv (REG_CLR))

    @property
    def pos (self):
        return self._pos

    @pos.setter
    def pos (self, value):
        line, col = value
        if line < 0 or line >= self.lines or col < 0 or col >= self.cols:
            raise IOError ('Position is out if bounds')
        self.command (bv (REG_DDRAM) + _lines_offsets [line] + col)
        self._pos = [line, col]

    def _next_line (self):
        line = self.line + 1
        if line >= self.lines:
            line = 0
        self.pos = (line, 0)

    def putc (self, char):
        delay_us (10)
        self._write (char, True)
        delay_us (10)
        self.col += 1
        if self.col == self.cols:
            self._next_line ()

    def put (self, string):
        if not isinstance (string, str):
            string = str (string)
        for c in string:
            self.putc (c)

    def set_char_pattern (self, charcode, pattern):
        if charcode < 0 or charcode > 7:
            raise ValueError ('Custom character code is out of bounds')
        if len (pattern) != 8:
            raise IOError ('Invalid custom character pattern')
        self.command (bv (REG_CGRAM) + charcode * 8)
        for byte in pattern:
            delay_us (10)
            self._write (byte, True)
            delay_us (10)
        self.pos = self._pos

    def __setitem__ (self, pos, string):
        self.pos = pos
        self.put (string)
