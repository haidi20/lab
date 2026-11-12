import unittest

from modules.vps.fakes import FakeSSHRunner
from modules.vps.config import VPSConfig
from modules.vps.setup import VPSSetupper

DIST = '/var/www/portfolio/fe/dist'


class BuildPortfolioTest(unittest.TestCase):
    def setUp(self):
        self.runner = FakeSSHRunner()
        self.setupper = VPSSetupper(VPSConfig(), runner=self.runner)

    def test_build_di_folder_fe_portfolio(self):
        self.setupper.build_and_deploy_portfolio()
        joined = '\n'.join(c[0] for c in self.runner.commands)
        self.assertIn('/var/www/portfolio/fe', joined)

    def test_tidak_menyalin_ke_folder_lain(self):
        self.setupper.build_and_deploy_portfolio()
        joined = '\n'.join(c[0] for c in self.runner.commands)
        self.assertNotIn('cp -r', joined)
        self.assertNotIn('/var/www/hello', joined)

    def test_memverifikasi_dist_ada(self):
        self.setupper.build_and_deploy_portfolio()
        joined = '\n'.join(c[0] for c in self.runner.commands)
        self.assertIn('test -f %s/index.html' % DIST, joined)


if __name__ == '__main__':
    unittest.main()
