def deploy_dist(runner, local_dist_root, remote_root):
    count = runner.upload_tree(local_dist_root, remote_root)
    stdout, _, code = runner.run('systemctl reload nginx')
    if code != 0:
        raise RuntimeError('nginx reload failed: %s' % stdout)
    return count
