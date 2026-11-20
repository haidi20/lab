import unittest
from unittest.mock import MagicMock

from modules.inaproc.api.cache import TkdnMysqlStore


class CacheSchemaTest(unittest.TestCase):
    def test_create_schema_creates_tables_with_comments(self):
        factory = MagicMock()
        connection = factory.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        store = TkdnMysqlStore(factory)

        store.create_schema()

        statements = [call.args[0] for call in cursor.execute.call_args_list]
        joined = "\n".join(statements)
        self.assertIn("CREATE TABLE IF NOT EXISTS tkdn_rows", joined)
        self.assertIn("CREATE TABLE IF NOT EXISTS tkdn_checks", joined)
        self.assertIn("COMMENT='Baris hasil scraping TKDN", joined)
        self.assertIn("COMMENT='Status pengecekan per nomor SPT", joined)
        self.assertIn("ALTER TABLE tkdn_rows COMMENT=", joined)
        self.assertIn("ALTER TABLE tkdn_checks COMMENT=", joined)
        connection.commit.assert_called()
        connection.close.assert_called()


if __name__ == "__main__":
    unittest.main()
