"""Tests for the end-to-end edge domain setup flow."""

import unittest

from modules.vps.domain_setup import setup_edge_domain


class FakeDnsClient:
    def __init__(self):
        self.calls = []

    def ensure_inventory_domain(self, zone, domain, target):
        self.calls.append((zone, domain, target))


class FakeSumopodClient:
    def __init__(self, domains=None, verify_payload=None):
        self.domains = domains or []
        self.verify_payload = verify_payload or {"status": "active"}
        self.verified = []

    def detail(self, vps_id):
        return {"web_domains": self.domains}

    def verify(self, vps_id, domain_id):
        self.verified.append((vps_id, domain_id))
        return self.verify_payload


class SetupEdgeDomainTest(unittest.TestCase):
    def test_creates_dns_then_verifies_matching_domain(self):
        dns = FakeDnsClient()
        sumopod = FakeSumopodClient(domains=[
            {"id": "dom-1", "domain_url": "inventory.haidinata.my.id"},
            {"id": "dom-2", "domain_url": "other.haidinata.my.id"},
        ])

        result = setup_edge_domain(
            "dcid_x",
            "sumopod_x",
            "vps-1",
            dns_client=dns,
            sumopod_client=sumopod,
        )

        self.assertEqual(
            dns.calls,
            [("haidinata.my.id", "inventory.haidinata.my.id",
              "vps-jkt2.sumopod.my.id")],
        )
        self.assertEqual(sumopod.verified, [("vps-1", "dom-1")])
        self.assertEqual(result["domain_id"], "dom-1")
        self.assertEqual(result["verify"], {"status": "active"})

    def test_unknown_domain_raises_without_verifying(self):
        dns = FakeDnsClient()
        sumopod = FakeSumopodClient(domains=[])

        with self.assertRaises(RuntimeError):
            setup_edge_domain(
                "dcid_x", "sumopod_x", "vps-1",
                dns_client=dns, sumopod_client=sumopod,
            )

        self.assertEqual(sumopod.verified, [])
