import unittest
from unittest.mock import patch

import pymysql

from modules.inaproc.api.config import InaprocDbConfig
from modules.inaproc.api.db import DbUnavailableError, connect_mysql


def make_config():
    return InaprocDbConfig(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="secret",
        database="inaproc",
    )


class ConnectMysqlTest(unittest.TestCase):
    def test_passes_timeout_and_utf8mb4(self):
        sentinel = object()
        with patch("modules.inaproc.api.db.pymysql.connect", return_value=sentinel) as connect:
            result = connect_mysql(make_config(), connect_timeout=7)

        self.assertIs(result, sentinel)
        kwargs = connect.call_args.kwargs
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 3306)
        self.assertEqual(kwargs["database"], "inaproc")
        self.assertEqual(kwargs["charset"], "utf8mb4")
        self.assertEqual(kwargs["connect_timeout"], 7)
        self.assertIs(kwargs["cursorclass"], pymysql.cursors.DictCursor)

    def test_operational_error_becomes_db_unavailable(self):
        with patch(
            "modules.inaproc.api.db.pymysql.connect",
            side_effect=pymysql.err.OperationalError(2003, "can't connect"),
        ):
            with self.assertRaises(DbUnavailableError) as ctx:
                connect_mysql(make_config())

        self.assertIn("db_unavailable", str(ctx.exception))
        self.assertNotIn("secret", str(ctx.exception))

    def test_interface_error_becomes_db_unavailable(self):
        with patch(
            "modules.inaproc.api.db.pymysql.connect",
            side_effect=pymysql.err.InterfaceError(0, "closed"),
        ):
            with self.assertRaises(DbUnavailableError):
                connect_mysql(make_config())


if __name__ == "__main__":
    unittest.main()
