import os
import unittest
from unittest.mock import patch

from modules.inaproc.api.config import InaprocDbConfig, InaprocConfigError


class InaprocDbConfigTest(unittest.TestCase):
    def test_reads_prefixed_env(self):
        env = {
            "INAPROC_MYSQL_HOST": "db.internal",
            "INAPROC_MYSQL_PORT": "3307",
            "INAPROC_MYSQL_USER": "inaproc_user",
            "INAPROC_MYSQL_PASSWORD": "secret",
            "INAPROC_MYSQL_DATABASE": "inaproc",
        }
        with patch.dict(os.environ, env, clear=True):
            config = InaprocDbConfig.from_env()

        self.assertEqual(config.host, "db.internal")
        self.assertEqual(config.port, 3307)
        self.assertEqual(config.user, "inaproc_user")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.database, "inaproc")

    def test_falls_back_to_shared_mysql_host_settings(self):
        env = {
            "MYSQL_HOST": "127.0.0.1",
            "MYSQL_PORT": "3308",
            "MYSQL_USER": "root",
            "MYSQL_PASSWORD": "rootpass",
            "INAPROC_MYSQL_DATABASE": "inaproc",
        }
        with patch.dict(os.environ, env, clear=True):
            config = InaprocDbConfig.from_env()

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 3308)
        self.assertEqual(config.user, "root")
        self.assertEqual(config.password, "rootpass")

    def test_database_does_not_fall_back_to_shared_mysql_database(self):
        env = {"MYSQL_DATABASE": "telegram_data"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(InaprocConfigError) as ctx:
                InaprocDbConfig.from_env()

        self.assertIn("INAPROC_MYSQL_DATABASE", str(ctx.exception))

    def test_reads_connect_timeout(self):
        env = {
            "INAPROC_MYSQL_DATABASE": "inaproc",
            "INAPROC_MYSQL_CONNECT_TIMEOUT": "3",
        }
        with patch.dict(os.environ, env, clear=True):
            config = InaprocDbConfig.from_env()

        self.assertEqual(config.connect_timeout, 3)

    def test_invalid_port_is_rejected(self):
        env = {"INAPROC_MYSQL_DATABASE": "inaproc", "INAPROC_MYSQL_PORT": "abc"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(InaprocConfigError):
                InaprocDbConfig.from_env()

    def test_password_is_not_in_repr(self):
        config = InaprocDbConfig(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="topsecret",
            database="inaproc",
        )
        self.assertNotIn("topsecret", repr(config))


if __name__ == "__main__":
    unittest.main()
