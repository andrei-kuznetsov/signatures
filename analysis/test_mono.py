import io
import tempfile
import unittest

from music21 import converter
from music21.stream import Part

from analysis.mono import extract_mono
from dataset import Dataset


class TestSignatures(unittest.TestCase):
    def test_mozart_sonata_13_3(self):
        path = Dataset.resolve_relative_path('testdata/sonata13-3.krn')
        scores = converter.parse(path)
        mono: Part = extract_mono(scores)

        with tempfile.NamedTemporaryFile() as tmp:
            tst_path = mono.write(fmt="text", fp=tmp.name)
            ref_path = Dataset.resolve_relative_path('testdata/sonata13-3.skyline.txt')
            self.assertListEqual(
                list(io.open(tst_path)),
                list(io.open(ref_path)))
