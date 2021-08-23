from time import sleep

import framebuf
from machine import SPI, Pin
from micropython import const

SET_POWER_CONTROL = const(0x28)
SET_SCROLL_LINE = const(0x40)
SET_PAGE_ADDRESS = const(0xB0)
SET_VLCD_RESISTOR_RATIO = const(0x20)
SET_CONTRAST = const(0x81)
SET_ALL_PIXEL_OM = const(0xA4)
SET_INVERSE_DISPLAY = const(0xA6)
SET_DISPLAY_ENABLE = const(0xAE)
SET_SEG_DIRECTION = const(0xA0)
SET_COM_DIRECTION = const(0xC0)
SYSTEM_RESET = const(0xE2)
SET_LCD_BIAS_RATIO = const(0xA2)
RESET_CURSOR_UPDATE_MODE = const(0xEE)
SET_BOOSTER_RATIO = const(0xF8)


class UC1701(framebuf.FrameBuffer):
    """
    FrameBuffer based driver for the UC1701 128*64 displays
    """

    def __init__(self, spi: SPI, cd: Pin, rst: Pin = None, cs: Pin = None) -> None:
        """
        :param spi: SPI instance
        :param cd: Control/Display data pin
        :param rst: Reset pin
        :param cs: CS pin
        """
        self.rate = 10 * 1024 * 1024

        self.width = 128
        self.height = 64

        self.pages = self.height // 8

        self.buffer = bytearray(self.width * self.pages)

        if cd is not None:
            cd.init(mode=cd.OUT, value=0)

        if rst is not None:
            rst.init(mode=rst.OUT, value=0)

        if cs is not None:
            cs.init(mode=cs.OUT, value=0)

        self.spi = spi
        self.cd = cd
        self.rst = rst
        self.cs = cs

        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)

        self.init_display()

    def init_display(self) -> None:
        """
        Initializes display
        :return: None
        """
        self._reset()
        self._write_cmd(SYSTEM_RESET)
        self._write_cmd(SET_SCROLL_LINE | 0x00)
        self._write_cmd(SET_COM_DIRECTION | (0x01 << 3))
        self._write_cmd(SET_SEG_DIRECTION | 0x00)
        self._write_cmd(SET_ALL_PIXEL_OM | 0x00)
        self.inverse(False)
        self._write_cmd(SET_LCD_BIAS_RATIO | 0x00)
        self._write_cmd(SET_POWER_CONTROL | 0x07)
        self._write_cmd([SET_BOOSTER_RATIO, 0x00])
        self._write_cmd(SET_VLCD_RESISTOR_RATIO | 0x03)
        self.contrast(128)
        self._write_cmd(RESET_CURSOR_UPDATE_MODE)
        self._write_cmd(SET_DISPLAY_ENABLE | 0x01)
        self._cursor_position(0, 0)

    def contrast(self, contrast: int) -> None:
        """
        Set display contrast
        :param contrast: Contrast value, from 0 to 255
        :return: None
        """
        self._write_cmd([SET_CONTRAST, (contrast >> 2) & 0x3f])

    def show(self) -> None:
        """
        Update display
        :return: None
        """
        for page in range(8):
            self._cursor_position(page, 0)
            start = self.width * page
            end = start + self.width
            self._write_data(self.buffer[start:end + 1])

    def inverse(self, inverse: bool) -> None:
        """
        Set inverse display
        :param inverse: Inverse display
        :return: None
        """
        self._write_cmd(SET_INVERSE_DISPLAY + (0x01 if inverse else 0x00))

    def _reset(self) -> None:
        """
        Reset display
        :return: None
        """
        if self.rst is not None:
            self.rst.value(0)
            sleep(0.1)
            self.rst.value(1)

    def _select(self, selected: bool) -> None:
        """
        Chip Select
        :param selected: True if chip selected, False otherwise
        :return: None
        """
        if self.cs:
            self.cs.value(0 if selected else 1)  # inverse logic

    def _cd_data(self, display: bool) -> None:
        """
        Select Control data or Display data for write operation
        :param display: True if Display data will be sent, False if Control data will be sent
        :return: None
        """
        if self.cd:
            self.cd.value(1 if display else 0)

    def _write_cmd(self, cmd) -> None:
        """
        Write Control data
        :param cmd: Control data. Single byte or sequence of the bytes
        :return: None
        """
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self._select(False)
        self._cd_data(False)
        self._select(True)
        if isinstance(cmd, bytes) or isinstance(cmd, list):
            self.spi.write(bytearray(cmd))
        else:
            self.spi.write(bytearray([cmd]))
        self._select(False)

    def _write_data(self, buf) -> None:
        """
        Write Display data
        :param buf: Display data. Sequence of the bytes
        :return: None
        """
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self._select(False)
        self._cd_data(True)
        self._select(True)
        self.spi.write(bytearray(buf))
        self._select(False)

    def _cursor_position(self, page: int, column: int) -> None:
        """
        Set position to write Display data
        :param page: Page number, from 0 to 7
        :param column: Column number, from 0 to 127
        :return: None
        """
        self._write_cmd(SET_PAGE_ADDRESS + (0x0f & page))
        self._write_cmd(0x0f & column)
        self._write_cmd(0x10 + ((column >> 4) & 0x0f))
