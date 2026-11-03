"""Ekspos modul 9router.

Nama paket diawali digit sehingga tidak bisa dipakai di pernyataan
`from ... import ...` (invalid identifier); gunakan importlib.
"""
import importlib

_ping = importlib.import_module("modules.9router.ping")

TARGETS = _ping.TARGETS
kirim_chat = _ping.kirim_chat
bandingkan = _ping.bandingkan
format_ringkasan = _ping.format_ringkasan

__all__ = ["TARGETS", "kirim_chat", "bandingkan", "format_ringkasan"]
