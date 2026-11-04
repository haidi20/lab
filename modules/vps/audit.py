AUDIT_COMMANDS = {
    'os': 'cat /etc/os-release | head -2; uname -m',
    'runtimes': 'node -v; bun --version; python3 -V; git --version',
    'packages': 'dpkg -l | grep -E "nginx|certbot|supervisor|ufw" | awk \'{print $2, $3}\'',
    'services': 'systemctl list-units --type=service --state=running --no-pager --no-legend',
    'www': 'ls /var/www',
    'nginx_files': 'ls /etc/nginx/sites-available/',
    'certs': 'certbot certificates 2>/dev/null | grep -E "Certificate Name|Domains|Expiry"',
    'ports': 'ss -tlnp',
}


def collect_audit(runner):
    result = {}
    for name, command in AUDIT_COMMANDS.items():
        stdout, _, _ = runner.run(command)
        result[name] = stdout.strip().splitlines()
    return result
