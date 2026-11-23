"""Tests for the DNSCloud.ID and Sumopod domain helpers."""

import unittest

from modules.vps.dnscloud import DnsCloudClient
from modules.vps.sumopod_domains import SumopodDomainsClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.responses:
            return self.responses.pop(0)
        return FakeResponse(200, {"ok": True})


class DnsCloudClientTest(unittest.TestCase):
    def test_ensure_cname_puts_structured_rdata_with_trailing_dot(self):
        session = FakeSession()
        client = DnsCloudClient("dcid_test", session=session)

        client.ensure_cname(
            zone="haidinata.my.id",
            name="validation.inventory",
            target="vps-jkt2.sumopod.my.id",
            ttl=300,
            comment="Sumopod domain validation",
        )

        method, url, kwargs = session.calls[0]
        self.assertEqual(method, "PUT")
        self.assertEqual(
            url,
            "https://api.dnscloud.id/v1/zones/haidinata.my.id/rrsets/"
            "validation.inventory/CNAME",
        )
        self.assertEqual(kwargs["json"]["ttl"], 300)
        self.assertEqual(
            kwargs["json"]["records"],
            [{"target": "vps-jkt2.sumopod.my.id."}],
        )
        self.assertEqual(kwargs["json"]["comment"], "Sumopod domain validation")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer dcid_test")

    def test_ensure_inventory_domain_sets_traffic_and_validation_cnames(self):
        session = FakeSession()
        client = DnsCloudClient("dcid_test", session=session)

        client.ensure_inventory_domain(
            zone="haidinata.my.id",
            domain="inventory.haidinata.my.id",
            target="vps-jkt2.sumopod.my.id",
        )

        urls = [call[1] for call in session.calls]
        self.assertEqual(len(urls), 2)
        self.assertIn(
            "https://api.dnscloud.id/v1/zones/haidinata.my.id/rrsets/inventory/CNAME",
            urls,
        )
        self.assertIn(
            "https://api.dnscloud.id/v1/zones/haidinata.my.id/rrsets/"
            "validation.inventory/CNAME",
            urls,
        )

    def test_error_response_raises_with_code(self):
        session = FakeSession([
            FakeResponse(422, {"code": "VALIDATION_FAILED", "detail": "bad"}, "bad"),
        ])
        client = DnsCloudClient("dcid_test", session=session)

        with self.assertRaises(RuntimeError) as ctx:
            client.ensure_cname("haidinata.my.id", "inventory", "vps-jkt2.sumopod.my.id")

        self.assertIn("VALIDATION_FAILED", str(ctx.exception))

    def test_missing_token_raises_before_network(self):
        session = FakeSession()
        with self.assertRaises(RuntimeError):
            DnsCloudClient("", session=session).ensure_cname(
                "haidinata.my.id", "inventory", "vps-jkt2.sumopod.my.id"
            )
        self.assertEqual(session.calls, [])


class SumopodDomainsClientTest(unittest.TestCase):
    def test_verify_posts_ids_and_returns_payload(self):
        session = FakeSession([FakeResponse(200, {"status": "active"})])
        client = SumopodDomainsClient("token", session=session)

        result = client.verify("vps-1", "domain-1")

        method, url, kwargs = session.calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/vpsnat/domains/verify"))
        self.assertEqual(kwargs["json"], {"id": "vps-1", "domain_id": "domain-1"})
        self.assertEqual(result, {"status": "active"})

    def test_verify_returns_error_payload_on_422(self):
        session = FakeSession([
            FakeResponse(422, {"code": "DNS_NOT_READY", "message": "no cname"}),
        ])
        client = SumopodDomainsClient("token", session=session)

        result = client.verify("vps-1", "domain-1")

        self.assertEqual(result["code"], "DNS_NOT_READY")
