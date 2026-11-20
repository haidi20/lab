#Requires -Version 5.1
<#
.SYNOPSIS
    Jalankan shim Responses Codex -> CutadAI di latar belakang (Windows).

.DESCRIPTION
    Shim WAJIB hidup sebelum Codex dipakai, karena ~/.codex/config.toml
    menunjuk http://127.0.0.1:8787/v1. Skrip ini idempoten: kalau port sudah
    listening, proses baru tidak dibuat.

    Token TIDAK pernah ditulis di sini. Shim membacanya sendiri dari
    environment CODEX_CUTAD_API_KEY (fallback CUTAD_API_KEY).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File modules\codex_cutad\start_shim.ps1
    powershell -ExecutionPolicy Bypass -File modules\codex_cutad\start_shim.ps1 -Stop
    powershell -ExecutionPolicy Bypass -File modules\codex_cutad\start_shim.ps1 -Status
#>
[CmdletBinding()]
param(
    [int]$Port = 8787,
    [switch]$Stop,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'

# Root repo = dua level di atas folder modul ini.
$ModuleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent (Split-Path -Parent $ModuleDir)
$LogDir    = Join-Path $env:LOCALAPPDATA 'codex-cutad-shim'
$LogPath   = Join-Path $LogDir 'shim.log'

function Test-PortAktif {
    param([int]$Nomor)
    # Cek port manual via TcpClient: cmdlet bawaan Windows untuk ini memberi
    # hasil salah di mesin ini (lapor tertutup padahal LISTENING).
    $klien = New-Object System.Net.Sockets.TcpClient
    try {
        $tugas = $klien.ConnectAsync('127.0.0.1', $Nomor)
        if (-not $tugas.Wait(1000)) { return $false }
        return $klien.Connected
    } catch {
        return $false
    } finally {
        $klien.Dispose()
    }
}

function Get-PemilikPort {
    param([int]$Nomor)
    $baris = netstat -ano | Select-String ":$Nomor\s" | Select-Object -First 1
    if ($null -eq $baris) { return $null }
    $bagian = ($baris.ToString() -split '\s+') | Where-Object { $_ }
    return [int]$bagian[-1]
}

if ($Status) {
    if (Test-PortAktif -Nomor $Port) {
        $pid_ = Get-PemilikPort -Nomor $Port
        Write-Host "shim AKTIF di 127.0.0.1:$Port (PID $pid_)" -ForegroundColor Green
        Write-Host "log: $LogPath"
        exit 0
    }
    Write-Host "shim TIDAK jalan di 127.0.0.1:$Port" -ForegroundColor Yellow
    exit 1
}

if ($Stop) {
    $pemilik = Get-PemilikPort -Nomor $Port
    if ($null -eq $pemilik) {
        Write-Host "tidak ada proses di port $Port" -ForegroundColor Yellow
        exit 0
    }
    Stop-Process -Id $pemilik -Force
    Write-Host "shim dihentikan (PID $pemilik)" -ForegroundColor Green
    exit 0
}

if (Test-PortAktif -Nomor $Port) {
    $pid_ = Get-PemilikPort -Nomor $Port
    Write-Host "shim sudah jalan di 127.0.0.1:$Port (PID $pid_); tidak spawn ulang." `
        -ForegroundColor Green
    exit 0
}

if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$python = (Get-Command python -ErrorAction SilentlyContinue)
if ($null -eq $python) {
    Write-Host "python tidak ditemukan di PATH" -ForegroundColor Red
    exit 1
}

$argumen = @('-m', 'modules.codex_cutad.shim', '--port', $Port)
Start-Process -FilePath $python.Source -ArgumentList $argumen `
    -WorkingDirectory $RepoRoot -WindowStyle Hidden `
    -RedirectStandardError $LogPath -RedirectStandardOutput "$LogPath.out"

$tunggu = 0
while ($tunggu -lt 20 -and -not (Test-PortAktif -Nomor $Port)) {
    Start-Sleep -Milliseconds 500
    $tunggu++
}

if (Test-PortAktif -Nomor $Port) {
    Write-Host "shim jalan di http://127.0.0.1:$Port/v1" -ForegroundColor Green
    Write-Host "log: $LogPath"
    exit 0
}

Write-Host "shim gagal start; cek log: $LogPath" -ForegroundColor Red
if (Test-Path -LiteralPath $LogPath) {
    Get-Content -LiteralPath $LogPath -Tail 20
}
exit 1
