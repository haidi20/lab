import unittest

from modules.vps.config import VPSConfig
from modules.vps.deploy import SITE_ROOTS, deploy_from_git
from modules.vps.fakes import FakeSSHRunner
from modules.vps.templates import BE_SERVICE, CICD_PORTFOLIO, NGINX_DEFAULT, NGINX_SITES

PORTFOLIO_REPO = '/var/www/portfolio'
PORTFOLIO_DIST = '/var/www/portfolio/fe/dist'


class ConfigPathTest(unittest.TestCase):
    def test_repo_dir_portfolio(self):
        self.assertEqual(VPSConfig().repo_dir, PORTFOLIO_REPO)

    def test_deploy_root_langsung_ke_dist(self):
        self.assertEqual(VPSConfig().deploy_root, PORTFOLIO_DIST)


class TemplatePathTest(unittest.TestCase):
    def test_tidak_ada_path_hello_di_semua_template(self):
        for content in NGINX_SITES.values():
            self.assertNotIn('/var/www/hello', content)
        self.assertNotIn('/var/www/hello', BE_SERVICE)
        self.assertNotIn('/var/www/hello', CICD_PORTFOLIO)

    def test_nginx_default_root_dist_portfolio(self):
        self.assertIn('root %s;' % PORTFOLIO_DIST, NGINX_DEFAULT)

    def test_be_service_working_directory_portfolio(self):
        self.assertIn('WorkingDirectory=%s/be' % PORTFOLIO_REPO, BE_SERVICE)

    def test_cicd_portfolio_pull_dan_build_di_portfolio(self):
        self.assertIn('cd %s && git pull' % PORTFOLIO_REPO, CICD_PORTFOLIO)
        self.assertIn('%s/fe' % PORTFOLIO_REPO, CICD_PORTFOLIO)


class DeployTest(unittest.TestCase):
    def test_site_root_portfolio(self):
        self.assertEqual(SITE_ROOTS['portfolio'], PORTFOLIO_DIST)

    def test_deploy_portfolio_tidak_menyalin_dist(self):
        runner = FakeSSHRunner()
        config = VPSConfig()
        deploy_from_git(runner, config, 'portfolio')
        commands = '\n'.join(c[0] for c in runner.commands)
        self.assertIn('cd %s && git' % PORTFOLIO_REPO, commands)
        self.assertIn('%s/fe' % PORTFOLIO_REPO, commands)
        self.assertNotIn('cp -r', commands)
        self.assertNotIn('/var/www/hello', commands)


if __name__ == '__main__':
    unittest.main()
