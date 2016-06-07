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
.. _wave generation: https://zach.se/generate-audio-with-python/
"""
import bisect
from collections import namedtuple
from decimal import Decimal
import math

Tone = namedtuple("Tone", ["theta", "delta", "omega", "val"])


class Sinewave:

    def generate(self, tone=None):
        if tone is None:
            tone = yield None
        while True:
            tone = yield tone._replace(
                val = self.value(**tone._asdict())
            )

    def value(self, theta, delta, omega, val):
        return Decimal(math.sin(theta))

class Trapezoid:

    def __init__(self, nRise, nHigh, nFall, nLow):
        nBins = sum((nRise, nHigh, nFall, nLow))
        self.features = [
            Decimal(2 * math.pi * i / nBins)
            for i in (
                0, nRise / 2, nRise / 2 + nHigh,
                nBins - nRise / 2 - nLow, nBins - nRise / 2, nBins
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

if __name__ == "__main__":
    import struct
    import wave
 
    F_SAMPLE = 44.1e3 
    N_SAMPLE = int(3 * F_SAMPLE)
    AMPLITUDE = Decimal(32767.0)
    VEL_800_HZ = Decimal(800 * 2 * math.pi)  # Radians/ sec

    zero = Decimal(0)
    dt = Decimal(1 / F_SAMPLE)
    wf = Sinewave()
    source = wf.generate()
    source.send(None)

    with wave.open("sine.wav", "w") as w:
        w.setnframes(N_SAMPLE) 
        w.setnchannels(2) 
        w.setsampwidth(2) 
        w.setframerate(F_SAMPLE) 
        w.setcomptype("NONE", "not compressed")

        for n in range(N_SAMPLE):
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

            w.writeframesraw(struct.pack(
                "h", int(AMPLITUDE * output.val)
            ))
            w.writeframesraw(struct.pack(
                "h", int(AMPLITUDE * output.val)
            ))
