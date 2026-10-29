import json
import unittest
from pathlib import Path


MENUS = [
    "glaccount",
    "expense_accrual",
    "employee_payment",
    "journal_voucher",
    "accountbudget_monitor",
    "accountbudget_transfer",
    "accountbudget_target",
    "account_history",
    "audit_journal",
]
REQUIRED_MD_SECTIONS = [
    "## Fitur",
    "## Form Data Baru",
    "## Daftar & Filter",
    "## Kolom Tabel",
    "## Sumber Data",
]


def menu_dir(menu):
    return Path("modules/accurate") / menu


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class GeneralLedgerDocumentationTests(unittest.TestCase):
    def test_general_ledger_menu_documentation_is_complete(self):
        for menu in MENUS:
            folder = menu_dir(menu)
            self.assertTrue((folder / f"{menu}.md").exists(), menu)
            self.assertTrue((folder / f"{menu}.json").exists(), menu)
            self.assertTrue((folder / "data.json").exists(), menu)

            data = load_json(folder / "data.json")
            self.assertEqual(
                set(data),
                {"menu", "module", "captured_at", "company", "database_id", "table", "status"},
            )
            self.assertEqual(set(data["table"]), {"columns", "record_count", "records"})
            self.assertEqual(data["table"]["record_count"], len(data["table"]["records"]))

            analysis = load_json(folder / f"{menu}.json")
            self.assertIn("module", analysis)
            self.assertIn("menu_key", analysis)
            self.assertIn("module_type", analysis)
            self.assertIn("features", analysis)
            self.assertIn("list_view", analysis)
            self.assertIn("form", analysis)
            self.assertIn("form_status", analysis)
            self.assertIn("data_sources", analysis)
            self.assertTrue(analysis["features"])
            self.assertIsInstance(analysis["list_view"]["columns"], list)
            self.assertIsInstance(analysis["list_view"]["filters"], list)
            self.assertTrue(analysis["data_sources"])

            markdown = (folder / f"{menu}.md").read_text(encoding="utf-8")
            for section in REQUIRED_MD_SECTIONS:
                self.assertIn(section, markdown, f"{menu}: {section}")

    def test_form_and_formless_menus_are_explicit(self):
        for menu in MENUS:
            analysis = load_json(menu_dir(menu) / f"{menu}.json")
            has_form = isinstance(analysis["form"], dict)
            self.assertEqual(has_form, analysis["form_status"]["available"])
            if has_form:
                self.assertTrue(analysis["form"]["tabs"])
            else:
                self.assertTrue(analysis["form_status"]["reason"])

    def test_actual_table_data_only_contains_records(self):
        for menu in MENUS:
            data = load_json(menu_dir(menu) / "data.json")
            self.assertNotIn("columns_definition", data)
            self.assertNotIn("filters", data)
            self.assertNotIn("form", data)


if __name__ == "__main__":
    unittest.main()
