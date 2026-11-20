import unittest

from modules.inaproc.api.spt import SptNumber, build_keyword, sequence_range

SAMPLE = "11469/SJ-IND.8/E-TKDN/7/2025"


class SptNumberTest(unittest.TestCase):
    def test_parse_valid(self):
        spt = SptNumber.parse(SAMPLE)
        self.assertEqual(spt.sequence, 11469)
        self.assertEqual(spt.unit, "SJ-IND.8")
        self.assertEqual(spt.doc_type, "E-TKDN")
        self.assertEqual(spt.month, 7)
        self.assertEqual(spt.year, 2025)

    def test_parse_bagian_kurang(self):
        with self.assertRaises(ValueError):
            SptNumber.parse("11469/SJ-IND.8/E-TKDN/2025")

    def test_parse_bulan_invalid(self):
        with self.assertRaises(ValueError):
            SptNumber.parse("11469/SJ-IND.8/E-TKDN/13/2025")

    def test_parse_tahun_bukan_4_digit(self):
        with self.assertRaises(ValueError):
            SptNumber.parse("11469/SJ-IND.8/E-TKDN/7/25")

    def test_parse_sequence_bukan_angka(self):
        with self.assertRaises(ValueError):
            SptNumber.parse("x/SJ-IND.8/E-TKDN/7/2025")

    def test_with_sequence(self):
        spt = SptNumber.parse(SAMPLE).with_sequence(11468)
        self.assertEqual(spt.sequence, 11468)
        self.assertEqual(spt.unit, "SJ-IND.8")
        self.assertEqual(spt.doc_type, "E-TKDN")
        self.assertEqual(spt.month, 7)
        self.assertEqual(spt.year, 2025)

    def test_str_roundtrip(self):
        spt = SptNumber.parse(SAMPLE)
        self.assertEqual(str(spt), SAMPLE)
        self.assertEqual(SptNumber.parse(str(spt)), spt)

    def test_build_keyword_encodes_slashes(self):
        keyword = build_keyword(SptNumber.parse(SAMPLE))
        self.assertEqual(keyword, "11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025")


class SequenceRangeTest(unittest.TestCase):
    def test_sequence_range_inclusive(self):
        numbers = sequence_range(SptNumber.parse(SAMPLE), 1000, 1003)
        self.assertEqual([n.sequence for n in numbers], [1000, 1001, 1002, 1003])

    def test_sequence_range_terbalik(self):
        with self.assertRaises(ValueError):
            sequence_range(SptNumber.parse(SAMPLE), 10, 5)


if __name__ == "__main__":
    unittest.main()
