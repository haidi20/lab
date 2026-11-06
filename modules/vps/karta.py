"""Push karta_spa dan pantau CI/CD GitHub Actions secara live."""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

GITHUB_REPO = 'utamaweb/karta_spa'
DEFAULT_REPO_PATH = Path.home() / 'projects' / 'karta_spa'


def git(repo_path, *args):
    result = subprocess.run(
        ['git', '-C', str(repo_path), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            'git %s gagal: %s' % (' '.join(args), result.stderr.strip())
        )
    return result.stdout.strip()


def github_token(repo_path):
    result = subprocess.run(
        ['git', 'credential', 'fill'],
        input='protocol=https\nhost=github.com\n',
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    raise RuntimeError('kredensial github tidak ditemukan')


def github_api(path, token):
    request = urllib.request.Request(
        'https://api.github.com' + path,
        headers={
            'Authorization': 'Bearer %s' % token,
            'Accept': 'application/vnd.github+json',
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def push(repo_path, branch, message, paths):
    git(repo_path, 'add', '--', *paths)
    git(repo_path, 'commit', '-m', message)
    git(repo_path, 'push', 'origin', branch)
    return git(repo_path, 'rev-parse', 'HEAD')


def find_run(token, branch, head_sha):
    data = github_api(
        '/repos/%s/actions/runs?branch=%s&per_page=5' % (GITHUB_REPO, branch),
        token,
    )
    for run in data.get('workflow_runs', []):
        if run['head_sha'] == head_sha:
            return run
    return None


def print_jobs(token, run_id, seen_steps):
    jobs = github_api(
        '/repos/%s/actions/runs/%s/jobs' % (GITHUB_REPO, run_id),
        token,
    )
    for job in jobs.get('jobs', []):
        for step in job.get('steps', []):
            key = (job['name'], step['name'])
            status = step['status']
            if (key, status) in seen_steps:
                continue
            seen_steps.add((key, status))
            marker = {'in_progress': '▶', 'completed': '✓', 'queued': '…'}.get(status, '·')
            print('  [%s] %s / %s: %s' % (marker, job['name'], step['name'], status), flush=True)


def watch(repo_path, branch, head_sha, timeout=1800, interval=15):
    token = github_token(repo_path)
    deadline = time.time() + timeout
    run = None
    seen_steps = set()
    print('Menunggu run CI untuk %s (%s)...' % (branch, head_sha[:8]), flush=True)
    while time.time() < deadline:
        run = find_run(token, branch, head_sha)
        if run:
            break
        time.sleep(interval)
    if not run:
        raise RuntimeError('run CI tidak ditemukan sebelum timeout')

    run_id = run['id']
    print('Run #%s (%s) dimulai.' % (run_id, run['name']), flush=True)
    while time.time() < deadline:
        run = github_api(
            '/repos/%s/actions/runs/%s' % (GITHUB_REPO, run_id),
            token,
        )
        print_jobs(token, run_id, seen_steps)
        if run['status'] == 'completed':
            conclusion = run['conclusion']
            print('Run #%s selesai: %s' % (run_id, conclusion), flush=True)
            return conclusion
        time.sleep(interval)
    raise RuntimeError('watching CI timeout sebelum selesai')


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m modules.vps.karta')
    parser.add_argument('command', choices=['push', 'watch', 'deploy'])
    parser.add_argument('--repo', type=Path, default=DEFAULT_REPO_PATH)
    parser.add_argument('--branch', default='dev')
    parser.add_argument('--message', help='pesan commit untuk push')
    parser.add_argument('--path', action='append', dest='paths', help='path file untuk di-commit')
    parser.add_argument('--sha', help='commit sha untuk watch (default: HEAD branch)')
    parser.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args(argv)

    try:
        if args.command in ('push', 'deploy'):
            if not args.message or not args.paths:
                parser.error('push/deploy butuh --message dan --path')
            head_sha = push(args.repo, args.branch, args.message, args.paths)
            print('Push %s ke %s: %s' % (args.branch, GITHUB_REPO, head_sha[:8]))
        else:
            head_sha = args.sha or git(args.repo, 'rev-parse', 'origin/%s' % args.branch)
        if args.command in ('watch', 'deploy'):
            conclusion = watch(args.repo, args.branch, head_sha, timeout=args.timeout)
            if conclusion != 'success':
                return 1
    except RuntimeError as error:
        print('ERROR: %s' % error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
