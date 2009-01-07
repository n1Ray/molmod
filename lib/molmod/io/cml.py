# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2008 Toon Verstraelen <Toon.Verstraelen@UGent.be>
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
# --

from molmod.units import angstrom
from molmod.molecules import Molecule
from molmod.molecular_graphs import MolecularGraph
from molmod.data.periodic import periodic

import numpy

from xml.sax import make_parser
from xml.sax.handler import feature_namespaces, ContentHandler


__all__ = ["load_cml", "dump_cml"]


class CMLMoleculeLoader(ContentHandler):
    def __init__(self):
        self.molecules = []
        self.current_title = None # current molecule

    atom_exclude = frozenset(['id', 'elementType', 'x3', 'y3', 'z3', 'x2', 'y2'])
    bond_exclude = frozenset(['id', 'atomRefs2', 'order'])
    molecule_exclude = frozenset(['id', 'xmlns'])

    def get_extra(self, attrs, exclude):
        result = {}
        for key in attrs.getNames():
            if key not in exclude:
                result[str(key)] = str(attrs[key])
        return result

    def startElement(self, name, attrs):
        #print "START", name
        # If it's not a comic element, ignore it
        if name == 'molecule':
            self.current_title = attrs.get('id', 'No Title')
            self.current_numbers = []
            self.current_coordinates = []
            self.current_atom_names = []
            self.current_bonds = []
            self.current_extra = self.get_extra(attrs, self.molecule_exclude)
            self.current_atoms_extra = {}
        elif self.current_title is not None:
            if name == 'atom':
                atom_name = attrs.get('id', None)
                if atom_name is None: return
                symbol = attrs.get('elementType', None)
                if symbol is None: return
                try:
                    x = float(attrs.get('x3', None))
                    y = float(attrs.get('y3', None))
                    z = float(attrs.get('z3', None))
                except ValueError:
                    return
                atom_record = periodic[symbol]
                if atom_record is None: return
                self.current_atom_names.append(atom_name)
                self.current_numbers.append(atom_record.number)
                self.current_coordinates.append([x,y,z])
                # find potential extra attributes
                extra = self.get_extra(attrs, self.atom_exclude)
                if len(extra) > 0:
                    self.current_atoms_extra[len(self.current_numbers)-1] = extra
            elif name == 'bond':
                refs = attrs.get('atomRefs2', None)
                if not isinstance(refs, basestring): return
                if refs.count(" ") != 1: return
                name1, name2 = refs.split(" ")
                extra = self.get_extra(attrs, self.bond_exclude)
                self.current_bonds.append((name1,name2,extra))

    def endElement(self, name):
        #print "END", name
        if name == 'molecule':
            if len(self.current_numbers) > 0:
                self.current_coordinates = numpy.array(self.current_coordinates)*angstrom
                molecule = Molecule(self.current_numbers, self.current_coordinates, self.current_title)
                molecule.extra = self.current_extra
                molecule.atoms_extra = self.current_atoms_extra

                name_to_index = {}
                for counter, name in enumerate(self.current_atom_names):
                    name_to_index[name] = counter

                pairs = set()
                current_bonds_extra = {}
                for name1, name2, extra in self.current_bonds:
                    i1 = name_to_index.get(name1)
                    i2 = name_to_index.get(name2)
                    if i1 is not None and i2 is not None:
                        pair = frozenset([i1,i2])
                        if len(extra) > 0:
                            current_bonds_extra[pair] = extra
                        pairs.add(pair)

                molecule.bonds_extra = current_bonds_extra
                if len(pairs) == 0:
                    self.current_graph = None
                else:
                    molecule.graph = MolecularGraph(pairs, self.current_numbers)
                del self.current_atom_names
                del self.current_bonds

                self.molecules.append(molecule)
            self.current_title = None


def load_cml(f):
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = CMLMoleculeLoader()
    parser.setContentHandler(dh)
    parser.parse(f)
    return dh.molecules


def _dump_cml_molecule(f, molecule):
    extra = getattr(molecule, "extra", {})
    attr_str = " ".join("%s='%s'" % (key,value) for key,value in extra.iteritems())
    f.write(" <molecule id='%s' %s>\n" % (molecule.title, attr_str))
    f.write("  <atomArray>\n")
    atoms_extra = getattr(molecule, "atoms_extra", {})
    for counter, number, coordinate in zip(xrange(molecule.size), molecule.numbers, molecule.coordinates/angstrom):
        atom_extra = atoms_extra.get(counter, {})
        attr_str = " ".join("%s='%s'" % (key,value) for key,value in atom_extra.iteritems())
        f.write("   <atom id='a%i' elementType='%s' x3='%s' y3='%s' z3='%s' %s />\n" % (
            counter, periodic[number].symbol, coordinate[0],  coordinate[1],
            coordinate[2], attr_str,
        ))
    f.write("  </atomArray>\n")
    if molecule.graph is not None:
        bonds_extra = getattr(molecule, "bonds_extra", {})
        f.write("  <bondArray>\n")
        for pair in molecule.graph.pairs:
            bond_extra = bonds_extra.get(pair, {})
            attr_str = " ".join("%s='%s'" % (key,value) for key,value in bond_extra.iteritems())
            i1,i2 = pair
            f.write("   <bond atomRefs2='a%i a%i' %s />\n" % (i1, i2, attr_str))
        f.write("  </bondArray>\n")
    f.write(" </molecule>\n")


def dump_cml(f, molecules):
    if isinstance(f, basestring):
        f = file(f, "w")
        close = True
    else:
        close = False
    f.write("<?xml version='1.0'?>\n")
    f.write("<list xmlns='http://www.xml-cml.org/schema'>\n")
    for molecule in molecules:
        _dump_cml_molecule(f, molecule)
    f.write("</list>\n")
    if close:
        f.close()
