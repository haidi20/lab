<?php
$token = '';
foreach (file('/etc/environment', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
    if (strpos($line, 'KARTA_GIT_TOKEN=') === 0) {
        $token = trim(substr($line, strlen('KARTA_GIT_TOKEN=')));
    }
}
$targets = [
    ['utamaweb/karta_spa', 'dev', 'karta_spa'],
    ['haidi20/haidi20', 'main', 'haidi20'],
];
$active = $_GET['tab'] ?? 'karta_spa';
$validTabs = array_column($targets, 2);
if (!in_array($active, $validTabs, true)) {
    $active = $validTabs[0];
}

function api($path, $token)
{
    $ctx = stream_context_create(['http' => [
        'header' => "Authorization: Bearer $token\r\nUser-Agent: ci-monitor\r\n",
        'ignore_errors' => true,
    ]]);
    return json_decode(file_get_contents("https://api.github.com$path", false, $ctx), true);
}

function badge($run)
{
    $state = $run['status'] === 'completed' ? $run['conclusion'] : $run['status'];
    return '<span class="badge ' . htmlspecialchars($state) . '">' . htmlspecialchars($state) . '</span>';
}
?>
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>CI/CD Monitor — haidinata</title>
<style>
  body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:24px}
  h1{font-size:20px;margin:0 0 4px} .sub{color:#8b949e;font-size:13px;margin-bottom:20px}
  h2{font-size:14px;margin:28px 0 8px;color:#e6edf3}
  h2 .branch{color:#8b949e;font-weight:400}
  table{width:100%;border-collapse:collapse;background:#161b22;border-radius:8px;overflow:hidden}
  th,td{padding:9px 14px;text-align:left;font-size:13px;border-bottom:1px solid #21262d}
  th{background:#1c2128;color:#8b949e;font-weight:600}
  tr:last-child td{border-bottom:none}
  .badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}
  .success{background:#1a4731;color:#4ade80}.failure{background:#5c1a24;color:#f87171}
  .in_progress{background:#1c3a5e;color:#60a5fa}.queued{background:#3b2f10;color:#fbbf24}
  .startup_failure,.timed_out,.cancelled{background:#4a2b0f;color:#fb923c}
  a{color:#58a6ff;text-decoration:none} a:hover{text-decoration:underline}
  .commit{font-family:ui-monospace,monospace;color:#58a6ff}
  .msg{color:#8b949e;font-size:12px}
  .time{color:#8b949e;font-size:12px;white-space:nowrap}
  .empty{color:#8b949e;text-align:center;padding:20px}
  .tabs{display:flex;gap:8px;margin-bottom:16px}
  .tab{padding:6px 16px;border-radius:8px;background:#161b22;color:#8b949e;font-size:13px;font-weight:600;border:1px solid #21262d;text-decoration:none}
  .tab:hover{color:#e6edf3}
  .tab.active{background:#1f6feb;color:#fff;border-color:#1f6feb}
</style>
</head>
<body>
<h1>🚀 CI/CD Monitor</h1>
<div class="sub">5 run terakhir · auto-refresh 60 detik · <?= date('d M Y H:i') ?> WITA</div>
<nav class="tabs">
<?php foreach ($targets as [$repo, $branch, $tabId]): ?>
  <a class="tab <?= $tabId === $active ? 'active' : '' ?>" href="?tab=<?= $tabId ?>"><?= htmlspecialchars($tabId) ?></a>
<?php endforeach; ?>
</nav>
<?php if (!$token): ?>
<table><tr><td class="empty">Token GitHub tidak ditemukan di server</td></tr></table>
<?php endif; ?>
<?php foreach ($targets as [$repo, $branch, $tabId]):
    if ($tabId !== $active) continue;
    $data = $token ? api("/repos/$repo/actions/runs?branch=$branch&per_page=5", $token) : [];
    $runs = $data['workflow_runs'] ?? []; ?>
<h2><?= htmlspecialchars(explode('/', $repo)[1]) ?> <span class="branch">· branch <?= htmlspecialchars($branch) ?></span></h2>
<table>
<?php if (!$runs): ?>
<tr><td class="empty">Belum ada run CI</td></tr>
<?php else: ?>
<tr><th>Commit</th><th>Workflow</th><th>Status</th><th>Waktu</th><th></th></tr>
<?php foreach ($runs as $run): ?>
<tr>
  <td><span class="commit"><?= substr($run['head_sha'], 0, 7) ?></span><br><span class="msg"><?= htmlspecialchars(mb_strimwidth($run['head_commit']['message'] ?? '', 0, 60, '…')) ?></span></td>
  <td><?= htmlspecialchars($run['name']) ?></td>
  <td><?php $s = $run['status'] === 'completed' ? $run['conclusion'] : $run['status']; ?>
    <span class="badge <?= htmlspecialchars($s) ?>"><?= htmlspecialchars($s) ?></span></td>
  <td class="time"><?= date('d M H:i', strtotime($run['created_at'])) ?></td>
  <td><a href="https://github.com/<?= $repo ?>/actions/runs/<?= $run['id'] ?>" target="_blank">detail ↗</a></td>
</tr>
<?php endforeach; endif; ?>
</table>
<?php endforeach; ?>
</body>
</html>
