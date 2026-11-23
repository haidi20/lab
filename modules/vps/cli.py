import argparse
import json
import os
import sys

from modules.vps.audit import collect_audit
from modules.vps.config import VPSConfig
from modules.vps.domain_setup import (
    DEFAULT_DOMAIN,
    DEFAULT_TARGET,
    DEFAULT_ZONE,
    setup_edge_domain,
)
from modules.vps.deploy import deploy_all_sites, deploy_dist, deploy_from_git
from modules.vps.health import check_health
from modules.vps.setup import VPSSetupper
from modules.vps.ssh import SSHRunner


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m modules.vps')
    parser.add_argument(
        'command',
        choices=['audit', 'setup', 'deploy', 'health', 'domain'],
    )
    parser.add_argument('--local-dist', help='folder dist lokal untuk deploy')
    parser.add_argument('--remote-root', help='folder remote tujuan deploy')
    parser.add_argument(
        '--sites', nargs='*',
        help='nama site untuk deploy-all (portfolio, karta, klinik, ci-monitor)')
    parser.add_argument('--skip-certs', action='store_true')
    parser.add_argument('--skip-clone', action='store_true')
    parser.add_argument('--vps-id', help='ID VPS NAT Sumopod untuk command domain')
    parser.add_argument('--domain', default=DEFAULT_DOMAIN, help='domain edge')
    parser.add_argument('--zone', default=DEFAULT_ZONE, help='zona DNSCloud')
    parser.add_argument('--target', default=DEFAULT_TARGET, help='target CNAME')
    args = parser.parse_args(argv)

    config = VPSConfig.from_env()
    runner = SSHRunner(config)
    try:
        if args.command == 'audit':
            print(json.dumps(collect_audit(runner), indent=2))
        elif args.command == 'setup':
            VPSSetupper(config, runner=runner).run(
                skip_certs=args.skip_certs, skip_clone=args.skip_clone
            )
            print('setup selesai')
        elif args.command == 'deploy':
            if args.sites:
                deploy_all_sites(runner, config, args.sites)
                print('deploy %s selesai' % ', '.join(args.sites))
            else:
                if not args.local_dist:
                    parser.error('deploy butuh --local-dist atau --sites')
                remote_root = args.remote_root or config.deploy_root
                count = deploy_dist(runner, args.local_dist, remote_root)
                print('deploy %d file' % count)
        elif args.command == 'health':
            print(json.dumps(check_health(runner), indent=2))
        elif args.command == 'domain':
            if not args.vps_id:
                parser.error('domain butuh --vps-id')
            result = setup_edge_domain(
                dnscloud_token=os.environ.get('DNSCLOUD_TOKEN', ''),
                sumopod_token=os.environ.get('SUMOPOD_ACCESS_TOKEN', ''),
                vps_id=args.vps_id,
                zone=args.zone,
                domain=args.domain,
                target=args.target,
            )
            print(json.dumps(result, indent=2))
    except RuntimeError as error:
        print('ERROR: %s' % error, file=sys.stderr)
        return 1
    finally:
        runner.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
