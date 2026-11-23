"""DNSCloud.ID record automation (zone ``haidinata.my.id``).

DNSCloud stores record data as structured rdata, not presentation strings.
Names inside rdata must be fully qualified and end with a dot, so the target
is normalised here before it is sent.
"""

import requests

API_BASE = "https://api.dnscloud.id/v1"


def _fqdn(name):
    """Return a fully qualified DNS name with a single trailing dot."""
    return name.rstrip(".") + "."


class DnsCloudClient:
    """Minimal DNSCloud.ID v1 client limited to RRset upserts."""

    def __init__(self, token, session=None, base_url=API_BASE, timeout=30):
        self.token = token
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method, path, payload):
        if not self.token:
            raise RuntimeError("DNSCLOUD_TOKEN belum diisi")
        response = self.session.request(
            method,
            self.base_url + path,
            json=payload,
            headers={
                "Authorization": "Bearer %s" % self.token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "klinik-vps-toolkit/1.0",
            },
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            try:
                body = response.json()
            except ValueError:
                body = {}
            code = body.get("code") or response.text[:200]
            detail = body.get("detail") or body.get("message") or ""
            raise RuntimeError(
                "DNSCloud %s gagal: %s %s" % (method, code, detail)
            )
        try:
            return response.json()
        except ValueError:
            return {}

    def ensure_cname(self, zone, name, target, ttl=300, comment=None):
        """Create or replace one CNAME RRset inside ``zone``."""
        payload = {"ttl": ttl, "records": [{"target": _fqdn(target)}]}
        if comment:
            payload["comment"] = comment
        return self._request(
            "PUT",
            "/zones/%s/rrsets/%s/CNAME" % (zone, name),
            payload,
        )

    def ensure_inventory_domain(self, zone, domain, target):
        """Point ``domain`` at ``target`` and add Sumopod's validation CNAME.

        Sumopod verifies ownership with ``validation.<domain>``, so both the
        traffic record and the validation record have to exist.
        """
        label = domain[: -len(zone)].rstrip(".") if domain.endswith(zone) else domain
        self.ensure_cname(
            zone,
            label,
            target,
            comment="Sumopod traffic untuk %s" % domain,
        )
        self.ensure_cname(
            zone,
            "validation.%s" % label,
            target,
            comment="Sumopod domain validation untuk %s" % domain,
        )
