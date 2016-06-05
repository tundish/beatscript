#!/usr/bin/env python3
# encoding: UTF-8

# This file is part of beatscript.
#
# Beatscript is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Beatscript is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with beatscript.  If not, see <http://www.gnu.org/licenses/>.

"""
.. _maclaurin: http://voorloopnul.com/blog/approximating-the-sine-function-with-maclaurin-series-using-python/
.. _wave generation: https://zach.se/generate-audio-with-python/
"""
import bisect
from collections import namedtuple
from decimal import Decimal
import math
import warnings

import unittest

Tone = namedtuple("Tone", ["theta", "delta", "omega", "val"])

VEL_800_HZ = Decimal(800 * 2 * math.pi)  # Radians/ sec

def sinewave(tone=None):
    if tone is None:
        tone = yield None
    while True:
        tone = yield tone._replace(val=Decimal(math.sin(tone.theta)))

class Trapezoid:

    def __init__(self, nRise, nHigh, nFall, nLow):
        nBins = sum((nRise, nHigh, nFall, nLow))
        self.features = [
            Decimal(2 * math.pi * i / nBins)
            for i in (
                0, nRise / 2, nRise / 2 + nHigh, nBins - nRise / 2 - nLow, nBins - nRise / 2, nBins
            )
        ]

    def generate(self, tone=None):
        if tone is None:
            tone = yield None
        while True:
            val = self.value(**tone._asdict())
            tone = yield tone._replace(val=val)

    def value(self, theta, delta, omega, val):
        grad = 1 / self.features[1]
        prev = theta - delta * omega
        pos = Decimal(prev % Decimal(2 * math.pi))
        sector = bisect.bisect_left(self.features, pos)
        if sector in (0, 1, 5, 6):
            val = val + delta * omega * grad
        elif sector == 2:
            val = Decimal(1)
        elif sector == 3:
            val = val - delta * omega * grad
        elif sector == 4:
            val = Decimal(-1)
        return val

class OSCTests(unittest.TestCase):

    def test_sine_800hz(self):
        source = sinewave()
        source.send(None)
        zero = Decimal(0)
        dt = Decimal(2 * math.pi) / Decimal(16 * VEL_800_HZ)

        # 4 cycles at 16 samples per cycle
        expected = [
            Decimal(math.sin(x * 2 * math.pi / 16))
            for x in range(0, 4 * 16)
        ]

        for n, x in enumerate(expected):
            if n == 0:
                output = source.send(Tone(zero, dt, VEL_800_HZ, expected[-1]))
            else:
                output = source.send(
                    Tone(n * (dt * VEL_800_HZ), dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                self.assertAlmostEqual(x, output.val)

    def test_trapezoid_value(self):
        wave = Trapezoid(2, 2, 2, 2)
        zero = Decimal(0)
        dt = Decimal(2 * math.pi) / Decimal(16 * VEL_800_HZ)
        self.assertAlmostEqual(Decimal(-0.5), wave.value(zero, -dt, VEL_800_HZ, zero))

    def test_regular_trapezoid_800hz(self):
        source = Trapezoid(2, 2, 2, 2).generate()
        source.send(None)
        zero = Decimal(0)
        dt = Decimal(2 * math.pi) / Decimal(16 * VEL_800_HZ)

        # 4 cycles at 16 samples per cycle
        expected = [
            Decimal(i) for i in (
                0, 0.5, 1, 1, 1, 1, 1, 0.5, 0, -0.5, -1, -1, -1, -1, -1, -0.5
            ) * 4
        ]

        for n, x in enumerate(expected):
            if n == 0:
                output = source.send(Tone(zero, dt, VEL_800_HZ, expected[-1]))
            else:
                output = source.send(
                    Tone(n * (dt * VEL_800_HZ), dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                self.assertAlmostEqual(x, output.val)
