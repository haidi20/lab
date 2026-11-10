def deploy_dist(runner, local_dist_root, remote_root):
    count = runner.upload_tree(local_dist_root, remote_root)
    stdout, _, code = runner.run('systemctl reload nginx')
    if code != 0:
        raise RuntimeError('nginx reload failed: %s' % stdout)
    return count


def deploy_site(runner, local_root, remote_root):
    return deploy_dist(runner, local_root, remote_root)


SITE_ROOTS = {
    'portfolio': '/var/www/hello',
    'karta': '/var/www/karta/public',
    'klinik': '/var/www/klinik/src/public',
    'ci-monitor': '/var/www/ci-monitor',
}


def deploy_all_sites(runner, local_roots):
    results = {}
    for name, local_root in local_roots.items():
        remote_root = SITE_ROOTS[name]
        results[name] = deploy_dist(runner, local_root, remote_root)
    stdout, _, code = runner.run('systemctl reload nginx')
    if code != 0:
        raise RuntimeError('nginx reload failed: %s' % stdout)
    return results
