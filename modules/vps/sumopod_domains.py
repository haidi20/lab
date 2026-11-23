"""Sumopod edge domain API helpers (verify, list, delete)."""

import requests

API_BASE = "https://api-gate-v2.sumopod.com/webhook/sumopod"

BROWSER_HEADERS = {
    "Origin": "https://sumopod.com",
    "Referer": "https://sumopod.com/dashboard/vps",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}


class SumopodDomainsClient:
    """Talks to the Sumopod panel API that manages VPS NAT edge domains."""

    def __init__(self, access_token, session=None, base_url=API_BASE, timeout=60):
        self.access_token = access_token
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path, payload):
        headers = dict(BROWSER_HEADERS)
        headers["Authorization"] = "Bearer %s" % self.access_token
        headers["Content-Type"] = "application/json"
        response = self.session.request(
            "POST",
            self.base_url + path,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "text": response.text[:400]}

    def detail(self, vps_id):
        """Return the VPS NAT record, including ``web_domains``."""
        payload = self._post("/vpsnat/detail", {"id": vps_id})
        if isinstance(payload, list):
            return payload[0] if payload else {}
        return payload

    def verify(self, vps_id, domain_id):
        """Ask Sumopod to re-check DNS for one edge domain."""
        return self._post(
            "/vpsnat/domains/verify",
            {"id": vps_id, "domain_id": domain_id},
        )

    def delete_domain(self, vps_id, domain_id):
        """Remove one edge domain so it can be recreated cleanly."""
        return self._post(
            "/vpsnat/domains/delete",
            {"id": vps_id, "domain_id": domain_id},
        )
