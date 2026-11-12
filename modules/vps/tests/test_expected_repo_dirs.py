import os
import unittest

from modules.vps.config import DEFAULT_REPO_DIRS, expected_repo_dirs


class ExpectedRepoDirsTest(unittest.TestCase):
    def tearDown(self):
        os.environ.pop('VPS_EXPECTED_REPO_DIRS', None)

    def test_default_adalah_repo_vps_saat_ini(self):
        os.environ.pop('VPS_EXPECTED_REPO_DIRS', None)
        self.assertEqual(expected_repo_dirs(), list(DEFAULT_REPO_DIRS))

    def test_default_memuat_monitoring_ph_air(self):
        os.environ.pop('VPS_EXPECTED_REPO_DIRS', None)
        self.assertIn('monitoring-ph-air', expected_repo_dirs())

    def test_env_override_dipisah_koma_dan_dirapikan(self):
        os.environ['VPS_EXPECTED_REPO_DIRS'] = ' haidi , karta ,, skripsi '
        self.assertEqual(expected_repo_dirs(), ['haidi', 'karta', 'skripsi'])

    def test_env_kosong_jatuh_ke_default(self):
        os.environ['VPS_EXPECTED_REPO_DIRS'] = '   '
        self.assertEqual(expected_repo_dirs(), list(DEFAULT_REPO_DIRS))

    def test_hasil_baru_dan_tidak_mengubah_default(self):
        result = expected_repo_dirs()
        result.append('x')
        self.assertNotIn('x', list(DEFAULT_REPO_DIRS))


if __name__ == '__main__':
    unittest.main()
