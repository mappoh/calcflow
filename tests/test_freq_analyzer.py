import os
import tempfile
import pytest

from calcflow.core.freq_analyzer import extract_frequencies


SAMPLE_OUTCAR_LINES = """
   1 f  =    1.234567 THz     7.757080 2PiTHz    41.172760 cm-1     5.103900 meV
   2 f  =    2.345678 THz    14.737200 2PiTHz    78.234500 cm-1     9.700100 meV
   3 f/i=    0.567890 THz     3.568000 2PiTHz    18.941200 cm-1     2.348300 meV
"""


def test_extract_frequencies():
    with tempfile.NamedTemporaryFile(mode="w", suffix="OUTCAR", delete=False) as f:
        f.write(SAMPLE_OUTCAR_LINES)
        f.flush()
        path = f.name

    try:
        freqs = extract_frequencies(path)
        assert len(freqs) == 3

        # First mode: real
        assert freqs[0]["mode"] == 1
        assert freqs[0]["is_imaginary"] is False
        assert abs(freqs[0]["cm-1"] - 41.17276) < 0.001

        # Third mode: imaginary
        assert freqs[2]["mode"] == 3
        assert freqs[2]["is_imaginary"] is True
    finally:
        os.unlink(path)
