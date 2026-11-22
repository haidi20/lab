from __future__ import annotations

import unittest
from unittest.mock import patch

from modules.telegram_group_reader import __main__ as tg_main


class TestTelegramGroupReaderMain(unittest.TestCase):
    def test_main_uses_module_sync_days_variable(self) -> None:
        with patch.object(tg_main, "load_env_file"), \
             patch.object(tg_main.SyncConfig, "from_env") as config, \
             patch.object(tg_main.pymysql, "connect") as connect, \
             patch.object(tg_main, "MysqlMessageStore") as store, \
             patch.object(tg_main, "TelethonBackend") as backend, \
             patch.object(tg_main, "TelegramGroupReader") as reader, \
             patch.object(tg_main, "run_sync") as sync:
            config.return_value = type(
                "Config",
                (),
                {
                    "mysql_host": "h",
                    "mysql_port": 3306,
                    "mysql_user": "u",
                    "mysql_password": "p",
                    "mysql_database": "d",
                    "api_id": 1,
                    "api_hash": "hash",
                    "session": "s",
                },
            )()
            sync.return_value = {"groups": 1, "messages": 2}

            tg_main.main()

        self.assertTrue(connect.called)
        self.assertTrue(store.called)
        self.assertTrue(backend.called)
        self.assertTrue(reader.called)
        sync.assert_called_once()
        _args, kwargs = sync.call_args
        self.assertNotIn("since", kwargs)
        self.assertEqual(kwargs.get("days"), tg_main.SYNC_DAYS)


    def test_sync_days_is_one_month(self) -> None:
        self.assertEqual(tg_main.SYNC_DAYS, 30)

if __name__ == "__main__":
    unittest.main()
