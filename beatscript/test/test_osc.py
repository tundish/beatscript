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
    yield tone
    while True:
        pos = Decimal.fma(tone.delta, tone.omega, tone.theta)
        tone = yield tone._replace(
            theta=pos,
            val=Decimal(math.sin(pos))
        )

def trapezoid(nRise, nHigh, nFall, nLow, tone=None):
    nBins = sum((nRise, nHigh, nFall, nLow))
    features = [
        Decimal(2 * math.pi * i / nBins)
        for i in (
            0, nRise / 2, nRise / 2 + nHigh, nBins - nRise / 2 - nLow, nBins - nRise / 2, nBins
        )
    ]
    if tone is None:
        tone = yield None
    while True:
        pos = Decimal(tone.theta % Decimal(2 * math.pi))
        sector = bisect.bisect_left(features, pos)
        if sector in (0, 1):
            grad = 1 / features[1]
            print("Grad: ", grad, Decimal(0.4) / grad)
            val = tone.val + tone.delta * tone.omega * grad
        elif sector == 2:
            val = Decimal(1)
        elif sector == 3:
            val = tone.val - (pos - features[2]) / nFall
        elif sector in (4, 5):
            val = Decimal(-1)
        else:
            warnings.warn("Bad trapezoid sector")
            val = tone.val
        tone = yield tone._replace(
            val=val
        )

class OSCTests(unittest.TestCase):

    def tost_sine_800hz(self):
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
                output = source.send(Tone(zero, dt, VEL_800_HZ, zero))
            else:
                output = source.send(
                    Tone(output.theta + dt * VEL_800_HZ, dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                self.assertAlmostEqual(x, output.val, places=2)

    def test_regular_trapezoid_800hz(self):
        source = trapezoid(2, 2, 2, 2)
        source.send(None)
        zero = Decimal(0)
        dt = Decimal(2 * math.pi) / Decimal(16 * VEL_800_HZ)

        # 4 cycles at 16 samples per cycle
        expected = [
            Decimal(i) for i in (
                0.2, 0.6, 1, 1, 1, 1, 0.6, 0.2, -0.2, -0.6, -1, -1, -1, -1, -0.6, -0.2
            ) * 4]

        for n, x in enumerate(expected):
            if n == 0:
                output = source.send(Tone(zero, dt, VEL_800_HZ, x))
            else:
                output = source.send(
                    Tone(output.theta + dt * VEL_800_HZ, dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                print(x, output.val)
                self.assertAlmostEqual(x, output.val, places=2)
