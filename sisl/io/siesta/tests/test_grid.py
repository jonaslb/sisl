from __future__ import print_function, division

import pytest

import sisl
import numpy as np

pytestmark = [pytest.mark.io, pytest.mark.siesta]
_dir = 'sisl/io/siesta'


def test_si_pdos_kgrid_grid(sisl_files):
    si = sisl.get_sile(sisl_files(_dir, 'si_pdos_kgrid.VT'))
    grid = si.read_grid()
    assert si.grid_unit == pytest.approx(sisl.unit.siesta.unit_convert('Ry', 'eV'))