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
from decimal import Decimal
import math
import unittest

from beatscript.osc import sinewave
from beatscript.osc import Tone
from beatscript.osc import Trapezoid


VEL_800_HZ = Decimal(800 * 2 * math.pi)  # Radians/ sec

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
        wf = Trapezoid(2, 2, 2, 2)
        source = wf.generate()
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
                output = source.send(
                    Tone(zero, dt, VEL_800_HZ, wf.value(
                        zero, -dt, VEL_800_HZ, zero)
                    )
                )
            else:
                output = source.send(
                    Tone(n * (dt * VEL_800_HZ), dt, VEL_800_HZ, output.val)
                )

            with self.subTest(n=n):
                self.assertAlmostEqual(x, output.val)
