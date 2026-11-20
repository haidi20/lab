import unittest

from pydantic import ValidationError

from modules.inaproc.api.schemas import (
    CollectRequest,
    LoginRequest,
    LookupRequest,
    PreviewRequest,
)


class SchemaTest(unittest.TestCase):
    def test_login_valid(self):
        data = LoginRequest(email="a@b.com", password="secret")
        self.assertEqual(data.email, "a@b.com")

    def test_login_email_invalid(self):
        with self.assertRaises(ValidationError):
            LoginRequest(email="not-an-email", password="secret")

    def test_lookup_nomor_valid(self):
        data = LookupRequest(number="11469/SJ-IND.8/E-TKDN/7/2025")
        self.assertTrue(data.number.endswith("/2025"))

    def test_lookup_nomor_invalid(self):
        with self.assertRaises(ValidationError):
            LookupRequest(number="11469/2025")

    def test_collect_rentang_terbalik(self):
        with self.assertRaises(ValidationError):
            CollectRequest(template="11469/SJ-IND.8/E-TKDN/7/2025", start=10, end=5)

    def test_collect_lebih_dari_1000(self):
        with self.assertRaises(ValidationError):
            CollectRequest(template="11469/SJ-IND.8/E-TKDN/7/2025", start=1, end=1002)

    def test_collect_tepat_1000(self):
        data = CollectRequest(template="11469/SJ-IND.8/E-TKDN/7/2025", start=1, end=1000)
        self.assertEqual(data.end - data.start + 1, 1000)

    def test_collect_delay_default(self):
        data = CollectRequest(template="11469/SJ-IND.8/E-TKDN/7/2025", start=1, end=10)
        self.assertEqual((data.delay_min, data.delay_max), (1.0, 3.0))

    def test_collect_delay_min_tidak_valid(self):
        with self.assertRaises(ValidationError):
            CollectRequest(
                template="11469/SJ-IND.8/E-TKDN/7/2025",
                start=1,
                end=10,
                delay_min=0,
            )

    def test_collect_delay_max_lebih_kecil_dari_min(self):
        with self.assertRaises(ValidationError):
            CollectRequest(
                template="11469/SJ-IND.8/E-TKDN/7/2025",
                start=1,
                end=10,
                delay_min=5,
                delay_max=2,
            )

    def test_collect_delay_max_terlalu_besar(self):
        with self.assertRaises(ValidationError):
            CollectRequest(
                template="11469/SJ-IND.8/E-TKDN/7/2025",
                start=1,
                end=10,
                delay_min=1,
                delay_max=31,
            )

    def test_preview_boleh_lebih_dari_1000(self):
        data = PreviewRequest(template="11469/SJ-IND.8/E-TKDN/7/2025", start=1, end=2500)
        self.assertEqual(data.end - data.start + 1, 2500)

    def test_preview_rentang_terbalik(self):
        with self.assertRaises(ValidationError):
            PreviewRequest(template="11469/SJ-IND.8/E-TKDN/7/2025", start=10, end=5)


if __name__ == "__main__":
    unittest.main()
