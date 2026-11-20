#Requires -Version 5.1
<#
.SYNOPSIS
    Setup Codex CLI agar memakai gateway Cutad AI, lalu cek health gateway.

.DESCRIPTION
    Semua nilai (base URL, model) ditaruh di variabel pada blok CONFIG.
    API key dibaca dari environment variable CODEX_API_KEY, atau dari file lokal
    scripts/.codex_api_key.local yang di-gitignore. Jangan isi literal di file ini.

.EXAMPLE
    .\scripts\setup_codex.ps1
    .\scripts\setup_codex.ps1 -HealthOnly
    .\scripts\setup_codex.ps1 -SkipCodexTest
#>
[CmdletBinding()]
param(
    [switch]$HealthOnly,
    [switch]$SkipCodexTest,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ProgressPreference   = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ------------------------------------------------------------------ CONFIG ---
$ProviderId       = 'cutad'
$ProviderName     = 'Cutad AI'
$BaseUrl          = 'https://ai.cutad.web.id/v1'
$ApiKey           = $env:CODEX_API_KEY
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $LocalKeyFile = Join-Path $PSScriptRoot '.codex_api_key.local'
    if (Test-Path -LiteralPath $LocalKeyFile) {
        $ApiKey = (Get-Content -LiteralPath $LocalKeyFile -Raw).Trim()
    }
}
# $Model            = 'deepseek-v4-pro'
$Model            = 'glm-5.3-flash'
$WireApi          = 'responses'
$HealthPrompt     = 'Reply with exactly: PONG'
$HealthExpected   = 'PONG'
$ModelsTimeoutSec = 20
$ChatTimeoutSec   = 60
$ConfigDir        = Join-Path $env:USERPROFILE '.codex'
$ConfigPath       = Join-Path $ConfigDir 'config.toml'
# ----------------------------------------------------------------------------

$Headers = @{
    Authorization  = 'Bearer ' + $ApiKey
    'Content-Type' = 'application/json'
}

function Write-Step { param([string]$Message) Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Message) Write-Host "    [OK]   $Message" -ForegroundColor Green }
function Write-Bad  { param([string]$Message) Write-Host "    [FAIL] $Message" -ForegroundColor Red }
function Write-Note { param([string]$Message) Write-Host "    $Message" -ForegroundColor DarkGray }

function Get-MaskedKey {
    param([string]$Value)
    if ($Value.Length -le 8) { return ('*' * $Value.Length) }
    return $Value.Substring(0, 4) + ('*' * ($Value.Length - 8)) + $Value.Substring($Value.Length - 4)
}

function Get-ErrorStatus {
    param($ErrorRecord)
    $response = $ErrorRecord.Exception.Response
    if ($null -ne $response) {
        try { return [int]$response.StatusCode } catch { return $null }
    }
    return $null
}

function Invoke-GatewayGet {
    param([string]$Url, [int]$TimeoutSec)
    return Invoke-WebRequest -Uri $Url -Headers $Headers -UseBasicParsing -TimeoutSec $TimeoutSec
}

function Invoke-GatewayPost {
    param([string]$Url, [hashtable]$Payload, [int]$TimeoutSec)
    $json  = $Payload | ConvertTo-Json -Depth 8
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    return Invoke-WebRequest -Uri $Url -Method Post -Headers $Headers -Body $bytes `
        -ContentType 'application/json' -UseBasicParsing -TimeoutSec $TimeoutSec
}

function Test-ModelsEndpoint {
    $url = "$BaseUrl/models"
    try {
        $response = Invoke-GatewayGet -Url $url -TimeoutSec $ModelsTimeoutSec
        if ([int]$response.StatusCode -ne 200) { throw "HTTP $([int]$response.StatusCode)" }
        $payload = $response.Content | ConvertFrom-Json
        $entries = @($payload.data)
        $entry   = $entries | Where-Object { $_.id -eq $Model } | Select-Object -First 1
        if ($null -eq $entry) {
            $available = ($entries | ForEach-Object { $_.id }) -join ', '
            Write-Bad "Model '$Model' tidak ada di $url. Tersedia: $available"
            return $false
        }
        Write-Ok "GET $url -> 200, $($entries.Count) model, '$Model' tersedia"
        Write-Note "context_window=$($entry.context_window)  max_output_tokens=$($entry.max_output_tokens)  owned_by=$($entry.owned_by)"
        return $true
    }
    catch {
        $code = Get-ErrorStatus -ErrorRecord $_
        if ($code -eq 401 -or $code -eq 403) {
            Write-Bad "GET $url -> HTTP $code (API key ditolak; periksa variabel ApiKey)"
        }
        elseif ($null -ne $code) {
            Write-Bad "GET $url -> HTTP $code : $($_.Exception.Message)"
        }
        else {
            Write-Bad "GET $url -> tidak terjangkau: $($_.Exception.Message)"
        }
        return $false
    }
}

function Test-ResponsesEndpoint {
    $url     = "$BaseUrl/responses"
    $payload = @{
        model             = $Model
        input             = $HealthPrompt
        max_output_tokens = 32
        stream            = $false
    }
    try {
        $response = Invoke-GatewayPost -Url $url -Payload $payload -TimeoutSec $ChatTimeoutSec
        if ([int]$response.StatusCode -ne 200) { throw "HTTP $([int]$response.StatusCode)" }
        $json = $response.Content | ConvertFrom-Json
        if ($json.status -ne 'completed') {
            Write-Bad "POST $url -> status='$($json.status)' (bukan completed)"
            return $false
        }
        $text = $null
        foreach ($item in @($json.output)) {
            foreach ($part in @($item.content)) {
                if ($part.type -eq 'output_text') { $text = [string]$part.text; break }
            }
            if ($null -ne $text) { break }
        }
        if ([string]::IsNullOrWhiteSpace($text)) {
            Write-Bad "POST $url -> 200 tapi tidak ada output_text"
            return $false
        }
        if ($text.Trim() -ne $HealthExpected) {
            Write-Bad "POST $url -> jawaban '$($text.Trim())', diharapkan '$HealthExpected'"
            return $false
        }
        Write-Ok "POST $url -> 200, status=completed, model=$($json.model), jawaban='$($text.Trim())'"
        Write-Note "usage: input=$($json.usage.input_tokens)  output=$($json.usage.output_tokens)  total=$($json.usage.total_tokens)"
        return $true
    }
    catch {
        $code = Get-ErrorStatus -ErrorRecord $_
        if ($null -ne $code) { Write-Bad "POST $url -> HTTP $code : $($_.Exception.Message)" }
        else                 { Write-Bad "POST $url -> gagal: $($_.Exception.Message)" }
        return $false
    }
}

function Test-GatewayHealth {
    Write-Step 'Health check gateway'
    $results = @()
    $results += Test-ModelsEndpoint
    $results += Test-ResponsesEndpoint
    return ($results -notcontains $false)
}

function Set-CodexConfig {
    Write-Step "Tulis config: $ConfigPath"
    if (-not (Test-Path -LiteralPath $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    }

    $original = @()
    if (Test-Path -LiteralPath $ConfigPath) {
        $original = @(Get-Content -LiteralPath $ConfigPath)
        $backup   = "$ConfigPath.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item -LiteralPath $ConfigPath -Destination $backup -Force
        Write-Note "backup: $backup"
    }

    $kept            = New-Object System.Collections.Generic.List[string]
    $seenSection     = $false
    $inManagedBlock  = $false
    $providerHeader  = '^\s*\[model_providers\.' + [regex]::Escape($ProviderId) + '\]\s*$'

    foreach ($line in $original) {
        if ($line -match '^\s*\[') {
            $seenSection = $true
            if ($line -match $providerHeader) {
                $inManagedBlock = $true
                continue
            }
            $inManagedBlock = $false
            $kept.Add($line)
            continue
        }
        if ($inManagedBlock) { continue }
        if (-not $seenSection -and $line -match '^\s*(model|model_provider)\s*=') { continue }
        $kept.Add($line)
    }

    $block = @(
        "model = `"$Model`"",
        "model_provider = `"$ProviderId`"",
        '',
        "[model_providers.$ProviderId]",
        "name = `"$ProviderName`"",
        "base_url = `"$BaseUrl`"",
        "experimental_bearer_token = `"$ApiKey`"",
        "wire_api = `"$WireApi`"",
        ''
    )

    $keptLines = New-Object System.Collections.Generic.List[string]
    $started   = $false
    foreach ($line in $kept.ToArray()) {
        if (-not $started -and [string]::IsNullOrWhiteSpace($line)) { continue }
        $started = $true
        $keptLines.Add($line)
    }

    $lines   = @($block) + @($keptLines.ToArray())
    $content = ($lines -join "`r`n") + "`r`n"
    $utf8    = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($ConfigPath, $content, $utf8)
    Write-Ok "config ditulis ($($lines.Count) baris, section lain dipreserve)"
}

function Test-WrittenConfig {
    Write-Step 'Verifikasi isi config'
    $text   = Get-Content -LiteralPath $ConfigPath -Raw
    $checks = [ordered]@{
        "model = $Model"                 = $text.Contains("model = `"$Model`"")
        "model_provider = $ProviderId"   = $text.Contains("model_provider = `"$ProviderId`"")
        'base_url'                       = $text.Contains("base_url = `"$BaseUrl`"")
        'api_key literal (bukan env)'    = $text.Contains("experimental_bearer_token = `"$ApiKey`"")
        "wire_api = $WireApi"            = $text.Contains("wire_api = `"$WireApi`"")
        'tidak ada env_key'              = -not ($text -match '(?m)^\s*env_key\s*=')
    }
    $allOk = $true
    foreach ($name in $checks.Keys) {
        if ($checks[$name]) { Write-Ok $name } else { Write-Bad $name; $allOk = $false }
    }
    return $allOk
}

function Test-CodexCli {
    Write-Step 'Smoke test codex exec'
    $command = Get-Command codex -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Write-Note 'codex tidak ada di PATH; smoke test dilewati'
        return $true
    }
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output   = (& $command.Source exec --strict-config -s read-only --skip-git-repo-check $HealthPrompt 2>&1 | Out-String)
        $exitCode = $LASTEXITCODE
        $clean    = $output -replace [regex]::Escape($ApiKey), '<API_KEY>'
        if ($exitCode -ne 0) {
            Write-Bad "codex exec exit=$exitCode"
            Write-Note $clean.Trim()
            return $false
        }
        if ($clean -notmatch [regex]::Escape($HealthExpected)) {
            Write-Bad "codex exec exit=0 tapi tidak menjawab '$HealthExpected'"
            Write-Note $clean.Trim()
            return $false
        }
        Write-Ok "codex exec -> exit 0, jawaban '$HealthExpected' diterima"
        return $true
    }
    finally { $ErrorActionPreference = $previous }
}

# ------------------------------------------------------------------- MAIN ---
Write-Step 'Konfigurasi (dari variabel, hardcoded)'
Write-Host "    provider : $ProviderId ($ProviderName)"
Write-Host "    base_url : $BaseUrl"
Write-Host "    model    : $Model"
Write-Host "    api_key  : $(Get-MaskedKey $ApiKey)  ($($ApiKey.Length) char)"
Write-Host "    wire_api : $WireApi"
Write-Host "    config   : $ConfigPath"

if ([string]::IsNullOrWhiteSpace($ApiKey)) { throw 'ApiKey kosong; isi variabel ApiKey.' }
if ($BaseUrl -notmatch '^https://')        { throw 'BaseUrl wajib HTTPS.' }
if ($BaseUrl -notmatch '/v1$')             { Write-Note 'Peringatan: BaseUrl tidak diakhiri /v1' }

$healthOk = Test-GatewayHealth

if ($HealthOnly) {
    Write-Step 'Selesai (-HealthOnly): config tidak diubah.'
    if ($healthOk) { exit 0 } else { exit 1 }
}

if (-not $healthOk -and -not $Force) {
    throw 'Health check gagal. Gunakan -Force untuk tetap menulis config.'
}

Set-CodexConfig
$configOk = Test-WrittenConfig
$cliOk    = $true
if (-not $SkipCodexTest) { $cliOk = Test-CodexCli }

Write-Step 'Ringkasan'
$summary = [ordered]@{
    'Health gateway' = $(if ($healthOk) { 'OK' } else { 'FAIL' })
    'Config'         = $(if ($configOk) { 'OK' } else { 'FAIL' })
    'Codex CLI'      = $(if ($SkipCodexTest) { 'SKIP' } elseif ($cliOk) { 'OK' } else { 'FAIL' })
}
foreach ($name in $summary.Keys) { Write-Host "    $name : $($summary[$name])" }

if ($healthOk -and $configOk -and $cliOk) {
    Write-Ok 'Semua pemeriksaan lolos.'
    exit 0
}
Write-Bad 'Ada pemeriksaan yang gagal.'
exit 1
