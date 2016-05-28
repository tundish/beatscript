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
from collections import namedtuple
from decimal import Decimal
import math

import unittest

Tone = namedtuple("Tone", ["theta", "delta", "omega", "val"])

FREQ_800_HZ = Decimal(2 * math.pi / 800)  # Radians/ sec

def osc(tone=None):
    if tone is None:
        tone = yield None
    while True:
        tone = yield tone._replace(
            val=math.sin(tone.theta + tone.delta * tone.omega)
        )

class OSCTests(unittest.TestCase):

    def test_init(self):
        
        expected = [math.sin(x) for x in range(0, 30)]

        source = osc()
        source.send(None)
        zero = Decimal(0)
        dt = Decimal("0.5")

        for n, x in enumerate(expected):
            if n == 0:
                output = source.send(Tone(zero, dt, FREQ_800_HZ, 0))
            else:
                output = source.send(
                    Tone(output.theta + dt, dt, FREQ_800_HZ, output.val)
                )

            with self.subTest(n=n):
                self.assertEqual(x, output.val)
