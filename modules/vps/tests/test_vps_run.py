import os
import importlib
import unittest
from unittest import mock

class VpsRunEnvTest(unittest.TestCase):
    def setUp(self):
        self.old = {k: os.environ.get(k) for k in ('VPS_HOST','VPS_PORT','VPS_USER','VPS_PASSWORD')}
        os.environ.update({
            'VPS_HOST': 'example.test',
            'VPS_PORT': '2222',
            'VPS_USER': 'tester',
            'VPS_PASSWORD': 'secret',
        })
        global vps_run
        import modules.vps.vps_run as vps_run
        importlib.reload(vps_run)

    def tearDown(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_connect_uses_env_host_port_user_password(self):
        client = mock.Mock()
        with mock.patch.object(vps_run.paramiko, 'SSHClient', return_value=client):
            result = vps_run.connect()
        self.assertIs(result, client)
        client.connect.assert_called_once_with('example.test', 2222, 'tester', password='secret', timeout=30)

    def test_password_requires_env(self):
        os.environ['VPS_PASSWORD'] = ''
        with self.assertRaises(RuntimeError):
            vps_run.password()

if __name__ == '__main__':
    unittest.main()
