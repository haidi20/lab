SITE_ROOTS = {
    'portfolio': '/var/www/hello',
    'karta': '/var/www/karta/public',
    'klinik': '/var/www/klinik/src/public',
}


def _reload_nginx(runner):
    stdout, _, code = runner.run('systemctl reload nginx')
    if code != 0:
        raise RuntimeError('nginx reload failed: %s' % stdout)


def deploy_dist(runner, local_dist_root, remote_root):
    count = runner.upload_tree(local_dist_root, remote_root)
    _reload_nginx(runner)
    return count


def deploy_site(runner, local_root, remote_root):
    return deploy_dist(runner, local_root, remote_root)


def _deploy_portfolio_from_git(runner, config):
    runner.run('cd %s && git pull' % config.repo_dir)
    runner.run(
        'cd %s/fe && bun install && bun run build' % config.repo_dir, timeout=1200
    )
    runner.run('rm -rf %s && mkdir -p %s' % (config.deploy_root, config.deploy_root))
    runner.run(
        'cp -r %s/fe/dist/. %s/' % (config.repo_dir, config.deploy_root)
    )
    _reload_nginx(runner)


def _deploy_laravel_from_git(runner, repo_dir, web_root, branch):
    runner.run('cd %s && git pull origin %s' % (repo_dir, branch))
    runner.run('cd %s && composer install --no-dev --optimize-autoloader' % repo_dir, timeout=600)
    runner.run('cd %s && php artisan migrate --force' % repo_dir, timeout=300)
    runner.run('cd %s && php artisan config:cache && php artisan route:cache' % repo_dir)
    _reload_nginx(runner)


def _deploy_ci_monitor_from_git(runner, config):
    runner.run('git -C %s fetch --prune origin' % config.lab_repo_dir)
    runner.run('git -C %s reset --hard origin/%s' % (config.lab_repo_dir, config.portfolio_branch))
    runner.run('test -f %s/index.php' % config.ci_monitor_root)
    _reload_nginx(runner)


def deploy_from_git(runner, config, site):
    if site == 'portfolio':
        _deploy_portfolio_from_git(runner, config)
    elif site == 'karta':
        _deploy_laravel_from_git(
            runner, config.karta_repo_dir, SITE_ROOTS['karta'], config.karta_branch)
    elif site == 'klinik':
        _deploy_laravel_from_git(
            runner, '%s/src' % config.klinik_repo_dir, SITE_ROOTS['klinik'], config.klinik_branch)
    elif site == 'ci-monitor':
        _deploy_ci_monitor_from_git(runner, config)
    else:
        raise ValueError('site tidak dikenal: %s' % site)


def deploy_all_sites(runner, config, sites):
    for site in sites:
        deploy_from_git(runner, config, site)
