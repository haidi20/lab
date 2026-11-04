HEALTH_COMMANDS = {
    'nginx': 'systemctl is-active nginx',
    'be_service': 'systemctl is-active haidi20-be',
    'be_http': 'curl -s -o /dev/null -w %{http_code} http://127.0.0.1:3000/api/health',
    'site_http': 'curl -s -o /dev/null -w %{http_code} http://127.0.0.1/',
}


def check_health(runner):
    result = {}
    for name, command in HEALTH_COMMANDS.items():
        stdout, _, code = runner.run(command)
        result[name] = {'output': stdout.strip(), 'code': code}
    return result
