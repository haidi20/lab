from __future__ import annotations

import hashlib


def verify_digiflazz_signature(username: str, api_key: str, ref_id: str, signature: str) -> bool:
    expected = hashlib.md5(f"{username}{api_key}{ref_id}".encode()).hexdigest()
    return signature == expected
