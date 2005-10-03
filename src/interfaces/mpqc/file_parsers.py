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

from pychem.interfaces.output_parsers import FileParser
from pychem.moldata import periodic

import re

class ScfEnergiesParser(FileParser):
    extension="out"

    def __init__(self, name, condition=None):
        FileParser.__init__(self, name, condition)
        self.re = re.compile(r"total scf energy =\s(?P<energy>\S+)")
        
    def reset(self):
        self.energies = []
        
    def parse(self, line):
        match_object = self.re.search(line)
        if match_object != None:
            self.energies.append(float(match_object.group("energy")))
        
    def result(self):
        return self.energies


class MolecularEnergiesParser(FileParser):
    extension="out"

    def __init__(self, name, condition=None):
        FileParser.__init__(self, name, condition)
        self.re = re.compile(r"Value of the MolecularEnergy:\s(?P<energy>\S+)")
        
    def reset(self):
        self.energies = []
        
    def parse(self, line):
        match_object = self.re.search(line)
        if match_object != None:
            self.energies.append(float(match_object.group("energy")))
        
    def result(self):
        return self.energies


class WarningParser(FileParser):
    extension="out"

    def __init__(self, name, condition=None):
        FileParser.__init__(self, name, condition)
        self.re = re.compile(r"WARNING:")
        
    def reset(self):
        self.warnings = False
        
    def parse(self, line):
        if not self.warnings:
            match_object = self.re.search(line)
            if match_object != None:
                self.warnings = True
        
    def result(self):
        return self.warnings


class OptimizationConvergedParser(FileParser):
    extension="out"

    def __init__(self, name, condition=None):
        FileParser.__init__(self, name, condition)
        self.re = re.compile(r"The optimization has converged.")
        
    def reset(self):
        self.converged = False
        
    def parse(self, line):
        if not self.converged:
            match_object = self.re.search(line)
            if match_object != None:
                self.converged = True
        
    def result(self):
        return self.converged


class MultiLineParser(FileParser):
    def __init__(self, name, activator, deactivator, condition=None):
        FileParser.__init__(self, name, condition)
        self.activator = activator
        self.deactivator = deactivator

    def reset(self):
        self.active = False

    def parse(self, line):
        if self.active:
            if self.deactivator.search(line) != None:
                self.active = False
                self.stop_collecting()
            else:
                self.collect(line)
        elif self.activator.search(line) != None:
            self.active = True
            self.start_collecting()

    def start_collecting(self):
        raise NotImplementedError

    def collect(self, line):
        raise NotImplementedError

    def stop_collecting(self):
        raise NotImplementedError


class OutputMoleculesParsers(MultiLineParser):
    extension="out"

    def __init__(self, name, condition=None):
        activator = re.compile(r"n\s+atoms\s+geometry")
        deactivator = re.compile(r"}$")
        MultiLineParser.__init__(self, name, activator, deactivator, condition)
        self.re = re.compile(r"(?P<symbol>\S+)\s*[\s*(?P<x>\S+)\s*(?P<y>\S+)\s*(?P<z>\S+)\s*]")
        
    def reset(self):
        self.molecules = []
        self.active = False
        
    def start_collecting(self):
        self.current_atoms = []

    def collect(self, line):
        match_object = self.re.search(line)
        self.current_atoms.append([
            periodic.reverse_symbol_lookup(match_object.group("symbol"))),
            float(match_object.group("x")),
            float(match_object.group("y")),
            float(match_object.group("z"))
        ])

    def stop_collecting(self):
        self.molecules.append(Molecule(self.current_atoms))
        del self.current_atoms
        
    def result(self):
        return self.molecules


class GradientsParsers(MultiLineParser):
    extension="out"

    def __init__(self, condition):
        activator = re.compile(r"Gradient of the MolecularEnergy:")
        deactivator = re.compile(r"^$")
        MultiLineParser.__init__(self, name, activator, deactivator, condition)
        self.re = re.compile(r"\d+\s+(?P<gradient>\S+)")
        
    def reset(self):
        self.gradients = []
        self.active = False
        
    def start_collecting(self):
        self.current_gradient = []

    def collect(self, line):
        match_object = self.re.search(line)
        self.current_gradient.append(float(match_object.group("gradient")))
        
    def stop_collecting(self):
        gradient = Numeric.array(self.current_gradient, Numeric.Float)
        gradient.shape = (-1,3)
        self.gradients.append(gradient)
        del self.current_gradient

    def result(self):
        return self.gradients
