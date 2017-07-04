#!/usr/bin/python

# Copyright 2012 Daniel Berlin (with some changes by Adafruit Industries/Limor Fried
# ported and simplified for Micropython by Cefn Hoile)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal  MCP230XX_GPIO(1, 0xin
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from machine import I2C, Pin
import time

#addresses = [MCP23017_IODIRA, MCP23017_IODIRB, MCP23017_GPIOA, MCP23017_GPIOB, MCP23017_GPPUA, MCP23017_GPPUB, MCP23017_OLATA, MCP23017_OLATB]

MCP23017_IODIRA = 0x00
MCP23017_IODIRB = 0x01
MCP23017_GPIOA  = 0x12
MCP23017_GPIOB  = 0x13
MCP23017_GPPUA  = 0x0C
MCP23017_GPPUB  = 0x0D
MCP23017_OLATA  = 0x14
MCP23017_OLATB  = 0x15

class MCP23017(object):
    OUTPUT = 0
    INPUT = 1

    def __init__(self, address=32, gpioScl=5, gpioSda=4):
        self.address = address
        sclPin = Pin(gpioScl, mode=Pin.OUT)
        sdaPin = Pin(gpioSda, mode=Pin.OUT)
        self.i2c = I2C(scl=sclPin, sda=sdaPin, freq=100000)
        self.num_gpios = 16

        self.put(MCP23017_IODIRA, 0xFF) # all inputs on port A
        self.put(MCP23017_IODIRB, 0xFF)  # all inputs on port B
        self.direction = self.get(MCP23017_IODIRA)
        self.direction |= self.get(MCP23017_IODIRB) << 8
        self.put(MCP23017_GPPUA, 0x00)
        self.put(MCP23017_GPPUB, 0x00)

    def put(self, reg, val):
        self.i2c.writeto_mem(self.address,reg,bytearray([val]))

    def get(self, reg):
        buf = self.i2c.readfrom_mem(self.address,reg,1)
        return buf[0]

    def _changebit(self, bitmap, bit, value):
        assert value == 1 or value == 0, "Value is %s must be 1 or 0" % value
        if value == 0:
            return bitmap & ~(1 << bit)
        elif value == 1:
            return bitmap | (1 << bit)

    def _readandchangepin(self, port, pin, value, currvalue = None):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        #assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        if not currvalue:
            currvalue = self.get(port)
        newvalue = self._changebit(currvalue, pin, value)
        self.put(port, newvalue)
        return newvalue


    def pullup(self, pin, value):
        lvalue = self._readandchangepin(MCP23017_GPPUA, pin, value)
        if (pin < 8):
            return
        else:
            return self._readandchangepin(MCP23017_GPPUB, pin-8, value) << 8

    # Set pin to either input or output mode
    def config(self, pin, mode):
        if (pin < 8):
            self.direction = self._readandchangepin(MCP23017_IODIRA, pin, mode)
        else:
            self.direction |= self._readandchangepin(MCP23017_IODIRB, pin-8, mode) << 8

        return self.direction

    def output(self, pin, value):
        # assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        if (pin < 8):
            self.outputvalue = self._readandchangepin(MCP23017_GPIOA, pin, value, self.get(MCP23017_OLATA))
        else:
            self.outputvalue = self._readandchangepin(MCP23017_GPIOB, pin-8, value, self.get(MCP23017_OLATB)) << 8

        return self.outputvalue

    def input(self, pin):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        assert self.direction & (1 << pin) != 0, "Pin %s not set to input" % pin
        value = self.get(MCP23017_GPIOA)
        value |= self.get(MCP23017_GPIOB) << 8
        return value & (1 << pin)

# RPi.GPIO compatible interface for MCP23017 and MCP23008


def main():

    mcp = MCP23017() 

    # Set pins 0, 1 and 2 to output (you can set pins 0..15 this way)
    mcp.config(0, mcp.OUTPUT)
    mcp.config(1, mcp.OUTPUT)
    mcp.config(2, mcp.OUTPUT)

    # Set pin 3 to input with the pullup resistor enabled
    mcp.config(3, mcp.INPUT)
    mcp.pullup(3, 1)

    # Read input pin and display the results

    print("Pin 3 = {}".format(mcp.input(3) >> 3))

    # Python speed test on output 0 toggling at max speed
    print("Starting blinky on pin 0 (CTRL+C to quit)")
    while (True):
        mcp.output(0, 1)  # Pin 0 High
        time.sleep(1)
        mcp.output(0, 0)  # Pin 0 Low
        time.sleep(1)