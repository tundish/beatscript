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
        Decimal(i / nBins)
        for i in (0, nRise / 2, nRise / 2 + nHigh, nBins - nRise / 2 - nLow, nBins - nRise / 2)
    ]
    if tone is None:
        tone = yield None
    yield tone
    while True:
        theta = Decimal.fma(tone.delta, tone.omega, tone.theta)
        pos = Decimal(theta % Decimal(2 * math.pi))
        sector = bisect.bisect_left(features, pos)
        if sector == 1:
            val = pos / features[1]
        elif sector == 2:
            val = Decimal(1)
        elif sector == 3:
            val = Decimal.fma(tone.delta, Decimal(2 * nRise / nBins), tone.val)
        elif sector == 4:
            val = Decimal(-1)
        else:
            warnings.warn("Bad trapezoid sector")
        tone = yield tone._replace(
            theta=theta,
            val=val
        )

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
                output = source.send(Tone(zero, dt, VEL_800_HZ, zero))
            else:
                output = source.send(
                    Tone(output.theta + dt, dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                self.assertAlmostEqual(x, output.val, places=2)

    def test_regular_trapezoid_800hz(self):
        source = trapezoid(2, 2, 2, 2)
        source.send(None)
        zero = Decimal(0)
        p = Decimal(2 * math.pi) / VEL_800_HZ
        dt = p / 16

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
                    Tone(output.theta + dt, dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                print(x, output.val)
                self.assertAlmostEqual(x, output.val, places=2)
