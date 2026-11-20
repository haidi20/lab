"""Tests untuk modules/codex_cutad/start_shim.ps1 (autostart shim di Windows).

Skrip diuji secara statis: argumen, port default, dan pemanggilan modul yang
benar. Menjalankan proses latar belakang tidak dilakukan di test agar suite
tetap cepat dan deterministik (proses nyata diverifikasi manual lewat
`codex exec`).
"""
import importlib
import os
import unittest

base = importlib.import_module("modules.codex_cutad")
ROOT = os.path.dirname(os.path.abspath(base.__file__))
SKRIP = os.path.join(ROOT, "start_shim.ps1")


class TestStartShimScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open(SKRIP, encoding="utf-8") as f:
            cls.isi = f.read()

    def test_file_ada(self) -> None:
        self.assertTrue(os.path.isfile(SKRIP))

    def test_memakai_port_8787(self) -> None:
        self.assertIn("8787", self.isi)

    def test_menjalankan_modul_shim(self) -> None:
        self.assertIn("modules.codex_cutad.shim", self.isi)

    def test_tidak_menulis_token_literal(self) -> None:
        self.assertNotIn("cag_", self.isi)

    def test_mencegah_dua_instance(self) -> None:
        """Skrip harus idempoten: kalau port sudah listening, jangan spawn."""
        self.assertIn("TcpClient", self.isi)

    def test_tidak_memakai_test_netconnection(self) -> None:
        """`Test-NetConnection` tidak andal di mesin ini (lapor salah)."""
        self.assertNotIn("Test-NetConnection", self.isi)

    def test_mlog_tidak_membocorkan_token(self) -> None:
        """Log dipisah dari stdout agar prompt codex tidak tercampur."""
        self.assertIn("shim.log", self.isi)


if __name__ == "__main__":
    unittest.main()