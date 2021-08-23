# micropython-uc1701
MicroPython driver for UC1701 based 128\*64 pixels monochrome displays like Fysetc Mini12864.

# Installation
Put the module to the root of the filesystem on your board.

# Usage
```python
from machine import SPI, Pin
from uc1701 import UC1701

hspi = SPI(1)

cd = Pin(2)
rst = Pin(0)
cs = Pin(15)

display = UC1701(hspi, cd, rst, cs)
display.contrast(240)
display.fill(0)
display.rect(0, 0, 128, 64, 1)
display.text("UC1701", 3, 3, 1)
display.show()
display.inverse()
```

# Wiring
UC1701 is using SPI bus with additional CD and RST lines.

Sample code uses following connection scheme between Fysetc Mini12864 and ESP8266.

| Signal    | GPIO ESP8266 | GPIO Fysetc Mini12864 |
| --------- | ------------ | --------------------- |
| sck       | 14           | SCK (EXP2_9)          |
| mosi      | 13           | MOSI (EXP2_5)         |
| cd        | 2            | LCD A0 (EXP1_7)       |
| rst       | 0            | LCD RST (EXP1_6)      |
| cs        | 15           | LCD CS (EXP1_8)       |

# License
The MIT License (MIT). Please see [License File](LICENSE) for more information.
