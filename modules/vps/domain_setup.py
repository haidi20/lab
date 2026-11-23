"""End-to-end edge domain setup: DNS records, then Sumopod verification."""

from modules.vps.dnscloud import DnsCloudClient
from modules.vps.sumopod_domains import SumopodDomainsClient

DEFAULT_ZONE = "haidinata.my.id"
DEFAULT_DOMAIN = "inventory.haidinata.my.id"
DEFAULT_TARGET = "vps-jkt2.sumopod.my.id"


def setup_edge_domain(
    dnscloud_token,
    sumopod_token,
    vps_id,
    zone=DEFAULT_ZONE,
    domain=DEFAULT_DOMAIN,
    target=DEFAULT_TARGET,
    dns_client=None,
    sumopod_client=None,
):
    """Create traffic + validation CNAMEs and verify the edge domain.

    Returns ``{"dns": [...], "verify": {...}}``. ``verify`` keeps whatever
    Sumopod answered so a pending DNS state is reported, not swallowed.
    """
    dns_client = dns_client or DnsCloudClient(dnscloud_token)
    sumopod_client = sumopod_client or SumopodDomainsClient(sumopod_token)

    dns_client.ensure_inventory_domain(zone=zone, domain=domain, target=target)

    domains = sumopod_client.detail(vps_id).get("web_domains", [])
    match = next(
        (item for item in domains if item.get("domain_url") == domain),
        None,
    )
    if match is None:
        raise RuntimeError("domain %s belum terdaftar di panel Sumopod" % domain)

    verify = sumopod_client.verify(vps_id, match["id"])
    return {"domain_id": match["id"], "verify": verify}
