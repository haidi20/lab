import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

SCAN_DIRS = (
    os.path.join(ROOT, 'modules', 'skripsi'),
    os.path.join(ROOT, 'modules', 'vps'),
)

SUSPICIOUS = re.compile(
    r"(?i)(password|passwd|pwd)\s*(=|:)\s*['\"][^'\"]{3,}['\"]"
)


def _python_files():
    for base in SCAN_DIRS:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ('__pycache__', 'panduan_pages')]
            for name in filenames:
                if name.endswith('.py'):
                    path = os.path.join(dirpath, name)
                    if os.path.basename(path).startswith('test_'):
                        continue
                    yield path


class TanpaKredensialHardcodedTest(unittest.TestCase):
    def test_tidak_ada_password_literal_di_source(self):
        offenders = []
        for path in _python_files():
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.split('#', 1)[0]
                    if SUSPICIOUS.search(stripped):
                        offenders.append('%s:%d: %s' % (
                            os.path.relpath(path, ROOT), lineno, line.strip()))
        self.assertEqual(offenders, [], 'kredensial hardcoded:\n' + '\n'.join(offenders))

    def test_env_default_tidak_berisi_password(self):
        for path in _python_files():
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            for match in re.finditer(
                r"os\.environ\.get\(\s*['\"]VPS_PASSWORD['\"]\s*,\s*([^)]*)\)", text
            ):
                default = match.group(1).strip()
                self.assertIn(default, ("''", '""'),
                              '%s memakai default password: %s' % (path, default))

    def test_helper_ssh_gagal_cepat_tanpa_env(self):
        os.environ.pop('VPS_PASSWORD', None)
        import importlib
        import modules.skripsi.ssh_diag as ssh_diag
        import modules.vps.vps_run as vps_run
        for mod in (ssh_diag, vps_run):
            importlib.reload(mod)
        for mod in (ssh_diag, vps_run):
            with self.assertRaises(RuntimeError):
                mod.password()


if __name__ == '__main__':
    unittest.main()
