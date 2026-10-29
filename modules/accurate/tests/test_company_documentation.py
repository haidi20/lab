import json
import unittest
from pathlib import Path


MENUS = [
    "branch", "tax", "payment_term", "shipment", "freeonboard",
    "employee_fee", "employee", "recurring", "period_end", "contact",
    "memorize_transaction", "calendar", "audit",
]
FORM_MENUS = {
    "branch", "tax", "payment_term", "shipment", "freeonboard",
    "employee_fee", "employee", "period_end",
}
REQUIRED_MD_SECTIONS = [
    "## Fitur", "## Form Data Baru", "## Daftar & Filter",
    "## Kolom Tabel", "## Sumber Data",
]


def menu_dir(menu):
    return Path("modules/accurate") / menu


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class CompanyDocumentationTests(unittest.TestCase):
    def test_company_menu_documentation_is_complete(self):
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
            self.assertEqual(analysis["module"], data["module"])
            self.assertIn(analysis["module_type"], {"MASTERDATA", "TRANSACTION", "INFORMATION", None})
            self.assertTrue(analysis["features"])
            self.assertIsInstance(analysis["list_view"], dict)
            self.assertIsInstance(analysis["list_view"]["columns"], list)
            self.assertIsInstance(analysis["list_view"]["filters"], list)
            self.assertTrue(analysis["data_sources"])
            self.assertEqual(menu in FORM_MENUS, isinstance(analysis["form"], dict))

            markdown = (folder / f"{menu}.md").read_text(encoding="utf-8")
            for section in REQUIRED_MD_SECTIONS:
                self.assertIn(section, markdown, f"{menu}: {section}")

    def test_add_form_fields_document_input_and_source(self):
        for menu in FORM_MENUS:
            form = load_json(menu_dir(menu) / f"{menu}.json")["form"]
            for tab in form["tabs"]:
                for section in tab["sections"]:
                    for field in section["fields"]:
                        self.assertTrue(field["label"])
                        self.assertTrue(field["inputs"])
                        self.assertTrue(field["source"])
                        for input_item in field["inputs"]:
                            self.assertTrue(input_item["name"])
                            self.assertTrue(input_item["type"])

    def test_no_form_menus_state_the_reason(self):
        for menu in set(MENUS) - FORM_MENUS:
            analysis = load_json(menu_dir(menu) / f"{menu}.json")
            self.assertIsNone(analysis["form"])
            self.assertFalse(analysis["form_status"]["available"])
            self.assertTrue(analysis["form_status"]["reason"])
            markdown = (menu_dir(menu) / f"{menu}.md").read_text(encoding="utf-8")
            self.assertTrue(
                "Tidak ada form" in markdown or "tidak memakai form tambah standar" in markdown
            )
