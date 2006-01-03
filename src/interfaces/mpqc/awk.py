# PyChem is a general chemistry oriented python package.
# Copyright (C) 2005 Toon Verstraelen
# 
# This file is part of PyChem.
# 
# PyChem is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
# --

from pychem.interfaces.base import AwkJob
from pychem.moldata import periodic
from pychem.units import to_angstrom, from_angstrom
from pychem.molecules import molecule_from_xyz_string

import os, copy, glob
import Numeric


__all__ = [
    "AwkMpqcJob", "AwkMpqcJobSinglePoint", "AwkMpqcJobOptimize"
]


class AwkMpqcJob(AwkJob):
    """MPQC jobs that use the Awk input format."""
    
    def __init__(self, prefix, title, input_molecule, method, basis, charge=0, multiplicity=1, memory=None):
        """
        Initialize a AwkMpqcJob instance.
        
        New arguments:
        method -- The type of approximation for the many body electron
                  Hamiltonian
        basis -- The basis set used to describe the wave-function.
        """
        self.input_molecule = input_molecule
        self.method = method
        self.basis = basis
        self.charge = charge
        self.multiplicity = multiplicity
        self.memory = memory
        AwkJob.__init__(self, prefix, title)
        
    def write_input(self, f):
        print >> f, "% " + self.title
        if self.memory != None:
            print >> f, "memory: " + self.memory
        print >> f, "method: " + self.method
        print >> f, "basis: " + self.basis
        print >> f, "charge: " + str(self.charge)
        print >> f, "multiplicity: " + str(self.multiplicity)
        print >> f, "molecule: "
        for number, (x, y, z) in zip(self.input_molecule.numbers, to_angstrom(self.input_molecule.coordinates)):
            print >> f, "   %2s  % 10.7f  % 10.7f  % 10.7f" % (periodic.symbol[number], x, y, z)

    def external_command(self):
        return "mpqc -o %s.out %s.in" % (self.prefix, self.prefix)
        
    def remove_temporary_files(self):
        for temp_filename in glob.glob("%s.wfn.*.tmp" % self.prefix):
            os.remove(temp_filename)

    def summarize_output(self):
        AwkJob.summarize_output(self)
        self.assign_fields(["accuracy_warnings"])


def yesno(value):
    if value:
        return "yes"
    else:
        return "no"

class AwkMpqcJobSinglePoint(AwkMpqcJob):
    """
    Awk MPQC jobs that doesn't change the geometry of the molecule.
    Only one SCF iteration is performed, with eventual post analysis.
    """
    def __init__(self, prefix, title, input_molecule, method, basis, charge=0, multiplicity=1, memory=None, do_gradient=False):
        """
        Initialize a AwkMpqcJobSinglePoint instance.
        
        Extra arguments:
        do_gradient -- wether calculate the gradient of the energy
        """
        self.do_gradient = do_gradient
        AwkMpqcJob.__init__(self, prefix, title, input_molecule, method, basis, charge, multiplicity, memory)
        self.energy = None
        self.gradient = None
        
    def write_input(self, f):
        AwkMpqcJob.write_input(self, f)
        print >> f, "optimize: no"
        print >> f, "gradient: " + yesno(self.do_gradient)

    def process_output_summary(self):
        if not self.accuracy_warnings:
            self.assign_fields(["energy"])
            gradient = self.summary.get("gradient")
            if gradient != None:
                self.gradient = Numeric.array(gradient, Numeric.Float)


class AwkMpqcJobOptimize(AwkMpqcJob):
    """
    A Awk MPQC job that optimizes the geometry of the molecule towards
    lower energies. The default MPQC optimization scheme is used.
    """
    def __init__(self, prefix, title, input_molecule, method, basis, charge=0, multiplicity=1, memory=None):
        """Initialize a AwkMpqcJobOptimize instance."""
        AwkMpqcJob.__init__(self, prefix, title, input_molecule, method, basis, charge, multiplicity, memory)
        self.energies = []
        self.output_molecule = None
        self.gradient = None
        
    def write_input(self, f):
        AwkMpqcJob.write_input(self, f)
        print >> f, "optimize: yes"
        
    def process_output_summary(self):
        if not self.accuracy_warnings:
            self.assign_fields(["energies"])
            self.output_molecule = copy.deepcopy(self.input_molecule)
            self.output_molecule.coordinates = from_angstrom(Numeric.array(self.summary["output_coordinates"], Numeric.Float))
