"""Test title formatting."""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cds_paper_bot


class TestFormatTitle(object):
    @pytest.mark.parametrize(
        "input, expected",
        [
            ("Analysis at $\\sqrt s=13 TeV$", "Analysis at √(s) = 13 TeV"),
            ("\\sqrt s", "√(s)"),
            ("Analysis  of process $x \\rightarrowy$", "Analysis of process x → y"),
            ("$x__s$", "x_s"),
            ("x →y", "x → y"),
            ("$t\\overline tt$", "ttt"),
            ("$t\\bar{t}$", "tt̅"),
            ("$t \\bar{t}$", "tt̅"),
            ("$t \\overline t$", "tt"),
            ("\\overline xy", "xy"),
            ("Bethe--Bloch", "Bethe-Bloch"),
            ("Energies of 15keV and MeV, 6eV", "Energies of 15 keV and MeV, 6 eV"),
            ("13TeV", "13 TeV"),
            ("nonsenseTeV", "nonsenseTeV"),
            ("13tev", "13tev"),
            ("50eV", "50 eV"),
        ],
    )
    def test_formatting(self, input, expected):
        new_title = cds_paper_bot.format_title(input)
        assert new_title == expected
