import json
import unittest
from pathlib import Path

MENUS = [
    'other_payment', 'other_deposit', 'bank_transfer', 'internet_banking',
    'bank_statement', 'bank_book', 'bank_reconcile',
    'application_virtual_account', 'application_epayment',
    'sales_quotation', 'sales_order', 'delivery_order', 'sales_downpayment',
    'sales_invoice', 'sales_receipt', 'sales_return', 'customer_category',
    'price_category', 'customer', 'sellingprice_adjustment',
    'salesman_commission', 'sales_target', 'ecommerce_setting', 'sales_check_in',
]


class CashBankSalesDocumentationTests(unittest.TestCase):
    def test_menu_documentation_is_complete(self):
        for menu in MENUS:
            folder = Path('modules/accurate') / menu
            for name in (f'{menu}.md', f'{menu}.json', 'data.json'):
                self.assertTrue((folder / name).exists(), f'{menu}/{name}')
            data = json.loads((folder / 'data.json').read_text(encoding='utf-8'))
            self.assertEqual(data['table']['record_count'], len(data['table']['records']))
            self.assertEqual(data['status'], 'loaded')
            analysis = json.loads((folder / f'{menu}.json').read_text(encoding='utf-8'))
            for key in ('menu', 'menu_key', 'module', 'module_type', 'features', 'list_view', 'form', 'form_status', 'data_sources'):
                self.assertIn(key, analysis, f'{menu}: {key}')
            markdown = (folder / f'{menu}.md').read_text(encoding='utf-8')
            for section in ('## Fitur', '## Form Data Baru', '## Daftar & Filter', '## Kolom Tabel', '## Sumber Data'):
                self.assertIn(section, markdown, f'{menu}: {section}')

    def test_form_status_is_explicit(self):
        for menu in MENUS:
            analysis = json.loads((Path('modules/accurate') / menu / f'{menu}.json').read_text(encoding='utf-8'))
            self.assertEqual(isinstance(analysis['form'], dict), analysis['form_status']['available'])


if __name__ == '__main__':
    unittest.main()
