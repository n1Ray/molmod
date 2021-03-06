# -*- coding: utf-8 -*-
# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>, Center
# for Molecular Modeling (CMM), Ghent University, Ghent, Belgium; all rights
# reserved unless otherwise stated.
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# MolMod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
#--


from common import BaseTestCase

from molmod.io.dlpoly import *
from molmod.units import *

import numpy


__all__ = ["DLPolyTestCase"]


class DLPolyTestCase(BaseTestCase):
    def test_history_reader(self):
        hr = DLPolyHistoryReader("input/dlpoly_HISTORY")
        for frame in hr:
            self.assertEqual(frame["step"], 4000)
            self.assertAlmostEqual(frame["timestep"]/picosecond, 0.001)
            self.assertAlmostEqual(frame["time"]/picosecond, 4.00)
            self.assertAlmostEqual(frame["cell"][0,0]/angstrom, 16.46)
            self.assertEqual(frame["symbols"][0], "O")
            self.assertAlmostEqual(frame["masses"][0]/amu, 16.000000)
            self.assertAlmostEqual(frame["charges"][0], -1.2)
            self.assertArraysAlmostEqual(frame["pos"][0]/angstrom, numpy.array([1.3522E+00, 1.3159E+00, 1.4312E+00]))
            self.assertArraysAlmostEqual(frame["vel"][0]/angstrom*picosecond, numpy.array([1.5113E+01, 1.0559E+00, 1.2843E-01]))
            self.assertArraysAlmostEqual(frame["frc"][0]/(amu*angstrom/picosecond**2), numpy.array([1.7612E+03, 3.6680E+03, 2.4235E+03]))
            break

    def test_output_reader(self):
        r = DLPolyOutputReader("input/dlpoly_OUTPUT")
        for row in r:
            self.assertAlmostEqual(row[0], 4000)
            self.assertAlmostEqual(row[-1]/(1000*atm), -1.1421E-01)
            break
