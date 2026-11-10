import argparse
import json
import sys

from modules.vps.audit import collect_audit
from modules.vps.config import VPSConfig
from modules.vps.deploy import SITE_ROOTS, deploy_all_sites, deploy_dist
from modules.vps.health import check_health
from modules.vps.setup import VPSSetupper
from modules.vps.ssh import SSHRunner


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m modules.vps')
    parser.add_argument('command', choices=['audit', 'setup', 'deploy', 'health'])
    parser.add_argument('--local-dist', help='folder dist lokal untuk deploy')
    parser.add_argument('--remote-root', help='folder remote tujuan deploy')
    parser.add_argument(
        '--sites', nargs='*',
        help='nama site untuk deploy-all (portfolio, karta, klinik, ci-monitor)')
    parser.add_argument('--skip-certs', action='store_true')
    parser.add_argument('--skip-clone', action='store_true')
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
                local_roots = {}
                for site in args.sites:
                    if site not in SITE_ROOTS:
                        parser.error(
                            'site tidak dikenal: %s (pilihan: %s)'
                            % (site, ', '.join(SITE_ROOTS))
                        )
                    local_roots[site] = args.local_dist or site
                results = deploy_all_sites(runner, local_roots)
                for site, count in results.items():
                    print('deploy %s: %d file' % (site, count))
            else:
                if not args.local_dist:
                    parser.error('deploy butuh --local-dist atau --sites')
                remote_root = args.remote_root or config.deploy_root
                count = deploy_dist(runner, args.local_dist, remote_root)
                print('deploy %d file' % count)
        elif args.command == 'health':
            print(json.dumps(check_health(runner), indent=2))
    except RuntimeError as error:
        print('ERROR: %s' % error, file=sys.stderr)
        return 1
    finally:
        runner.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
