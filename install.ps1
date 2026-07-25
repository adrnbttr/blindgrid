<#
.SYNOPSIS
    blindgrid installer for Windows.

.DESCRIPTION
    Installs into your user profile only. It never asks for administrator
    rights, never writes outside your profile, and never installs a
    third-party tool without saying so: if neither uv nor pipx is present it
    falls back to a plain virtual environment built with the Python you
    already have.

    irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1 | iex

.PARAMETER Method
    How to install: Auto, Uv, Pipx or Venv. Default Auto, which tries uv, then
    pipx, then a virtual environment.

.PARAMETER Source
    What to install: a path or a pip requirement. Defaults to the repository.

.PARAMETER Ref
    Git ref to install. Default main.

.PARAMETER NoConfig
    Skip creating a starter configuration file.

.PARAMETER Uninstall
    Remove blindgrid, keeping your configuration and current plan.

.EXAMPLE
    .\install.ps1
.EXAMPLE
    .\install.ps1 -Method Venv
.EXAMPLE
    .\install.ps1 -Uninstall
#>

[CmdletBinding()]
param(
    [ValidateSet('Auto', 'Uv', 'Pipx', 'Venv')]
    [string] $Method = 'Auto',
    [string] $Source,
    [string] $Ref = 'main',
    [switch] $NoConfig,
    [switch] $Uninstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoUrl    = 'https://github.com/adrnbttr/blindgrid'
$MinPython  = [version]'3.11'
$Root       = Join-Path $env:LOCALAPPDATA 'blindgrid'
$VenvDir    = Join-Path $Root 'venv'
$BinDir     = Join-Path $env:LOCALAPPDATA 'Programs\blindgrid'
$ConfigDir  = Join-Path $env:APPDATA 'blindgrid'
$StateDir   = Join-Path $env:LOCALAPPDATA 'blindgrid'

if (-not $Source) { $Source = "git+$RepoUrl.git@$Ref" }

# --------------------------------------------------------------- presentation

$UseColour = $Host.UI.SupportsVirtualTerminal -and -not $env:NO_COLOR
function Paint([string] $Text, [string] $Code) {
    if ($UseColour) { "$([char]27)[${Code}m$Text$([char]27)[0m" } else { $Text }
}

function Write-Step([string] $Message) { Write-Host "$(Paint '·' '36') $Message" }
function Write-Ok([string] $Message)   { Write-Host "  $(Paint '✓' '32') $Message" }
function Write-Warn([string] $Message) { Write-Host "  $(Paint '!' '33') $Message" }
function Write-Info([string] $Message) { Write-Host "    $(Paint $Message '90')" }

function Show-Failure([string] $Message) {
    Write-Host ""
    Write-Host "  $(Paint "✗ $Message" '31')"
    Write-Host ""
    exit 1
}

function Show-Banner {
    Write-Host ""
    Write-Host "  $(Paint 'blindgrid' '1') $(Paint '· lottery grids from cryptographic randomness' '90')"
    Write-Host ""
}

function Test-Command([string] $Name) {
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# ---------------------------------------------------------------- uninstalling

function Invoke-Uninstall {
    Show-Banner
    Write-Step 'Removing blindgrid'
    $removed = $false

    if (Test-Command 'uv') {
        $tools = & uv tool list 2>$null
        if ($tools -match '^blindgrid') {
            & uv tool uninstall blindgrid *> $null
            Write-Ok 'removed the uv tool'
            $removed = $true
        }
    }

    if (Test-Command 'pipx') {
        $packages = & pipx list --short 2>$null
        if ($packages -match '^blindgrid') {
            & pipx uninstall blindgrid *> $null
            Write-Ok 'removed the pipx package'
            $removed = $true
        }
    }

    if (Test-Path $VenvDir) {
        Remove-Item -Recurse -Force $VenvDir
        Write-Ok "removed $VenvDir"
        $removed = $true
    }

    $shim = Join-Path $BinDir 'blindgrid.cmd'
    if (Test-Path $shim) {
        Remove-Item -Force $shim
        Write-Ok "removed $shim"
        $removed = $true
    }

    if (-not $removed) { Write-Warn 'nothing to remove' }

    if ((Test-Path $ConfigDir) -or (Test-Path $StateDir)) {
        Write-Host ""
        Write-Info 'Your own files are untouched:'
        if (Test-Path $ConfigDir) { Write-Info "  $ConfigDir  (your budget ceiling, lotteries and players)" }
        if (Test-Path $StateDir)  { Write-Info "  $StateDir  (the plan for the current month)" }
        Write-Info 'Delete them yourself if you want them gone.'
    }
    Write-Host ""
    exit 0
}

if ($script:Uninstall) { Invoke-Uninstall }

# --------------------------------------------------------------- python lookup

function Find-Python {
    foreach ($candidate in @('python3.13', 'python3.12', 'python3.11', 'python', 'python3')) {
        if (-not (Test-Command $candidate)) { continue }
        try {
            $raw = & $candidate -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>$null
            if ($LASTEXITCODE -ne 0 -or -not $raw) { continue }
            if ([version]$raw -ge $MinPython) { return (Get-Command $candidate).Source }
        } catch { continue }
    }

    # The Windows launcher can reach interpreters that are not on PATH.
    if (Test-Command 'py') {
        foreach ($tag in @('-3.13', '-3.12', '-3.11')) {
            try {
                & py $tag -c 'import sys' 2>$null
                if ($LASTEXITCODE -eq 0) { return "py $tag" }
            } catch { continue }
        }
    }
    return $null
}

function Show-PythonHint {
    Write-Info 'Install Python 3.11 or newer:'
    Write-Info '  winget install Python.Python.3.12'
    Write-Info 'Or install uv, which brings its own Python:'
    Write-Info '  irm https://astral.sh/uv/install.ps1 | iex'
}

# ------------------------------------------------------------------ installing

function Install-WithUv {
    Write-Step 'Installing with uv'
    & uv tool install --force --python ">=$MinPython" $Source 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -ne 0) { Show-Failure 'uv could not install blindgrid.' }
    Write-Ok 'installed'

    $binHome = if ($env:UV_TOOL_BIN_DIR) { $env:UV_TOOL_BIN_DIR }
               elseif ($env:XDG_BIN_HOME) { $env:XDG_BIN_HOME }
               else { Join-Path $env:USERPROFILE '.local\bin' }
    return (Join-Path $binHome 'blindgrid.exe')
}

function Install-WithPipx {
    Write-Step 'Installing with pipx'
    & pipx install --force $Source 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -ne 0) { Show-Failure 'pipx could not install blindgrid.' }
    Write-Ok 'installed'

    $binHome = if ($env:PIPX_BIN_DIR) { $env:PIPX_BIN_DIR }
               else { Join-Path $env:USERPROFILE '.local\bin' }
    return (Join-Path $binHome 'blindgrid.exe')
}

function Install-WithVenv {
    $python = Find-Python
    if (-not $python) {
        Write-Host ""
        Write-Warn "No Python $MinPython or newer found."
        Show-PythonHint
        Show-Failure 'Cannot continue without a suitable Python.'
    }

    Write-Step 'Installing into a dedicated virtual environment'
    Write-Info "using $python"

    if (Test-Path $VenvDir) { Remove-Item -Recurse -Force $VenvDir }
    New-Item -ItemType Directory -Force -Path $Root, $BinDir | Out-Null

    # "py -3.12" arrives as one string and has to be split back into a command.
    $parts = $python -split ' '
    & $parts[0] @($parts[1..($parts.Length - 1)]) -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Show-Failure 'Could not create a virtual environment.' }

    $venvPython = Join-Path $VenvDir 'Scripts\python.exe'
    & $venvPython -m pip install --quiet --upgrade pip *> $null
    & $venvPython -m pip install --quiet $Source 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -ne 0) { Show-Failure 'pip could not install blindgrid.' }

    # A .cmd shim rather than a symlink: symlinks need developer mode or admin.
    $shim = Join-Path $BinDir 'blindgrid.cmd'
    "@echo off`r`n`"$(Join-Path $VenvDir 'Scripts\blindgrid.exe')`" %*" |
        Set-Content -Path $shim -Encoding ASCII

    Write-Ok "installed into $VenvDir"
    Write-Ok "created $shim"
    return $shim
}

# ----------------------------------------------------------------- post-install

function Test-OnPath([string] $Directory) {
    $entries = ($env:PATH -split ';') | Where-Object { $_ }
    return $entries -contains $Directory.TrimEnd('\')
}

function Show-PathAdvice([string] $Executable) {
    $directory = Split-Path -Parent $Executable
    if (Test-OnPath $directory) {
        Write-Ok "$directory is already on your PATH"
        return
    }

    Write-Warn "$directory is not on your PATH"
    Write-Info 'Add it for your user, then open a new terminal:'
    Write-Host ""
    Write-Host "      $(Paint "[Environment]::SetEnvironmentVariable('PATH', ""`$env:PATH;$directory"", 'User')" '1')"
    Write-Host ""
}

function Write-StarterConfig([string] $Executable) {
    if ($script:NoConfig) { return }

    Write-Step 'Configuration'
    $configFile = Join-Path $ConfigDir 'config.toml'
    if (Test-Path $configFile) {
        Write-Ok "keeping the existing $configFile"
        return
    }

    New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
    & $Executable config init --config $configFile *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "wrote a starter config to $configFile"
        Write-Info 'It ships three French games as examples. Check the prices, the draw'
        Write-Info 'days and above all max_monthly_budget before you play.'
    } else {
        Write-Warn 'could not write a starter config'
        Write-Info "Run 'blindgrid config init' once blindgrid is on your PATH."
    }
}

function Show-Farewell([string] $Executable) {
    $version = & $Executable version 2>$null
    if (-not $version) { $version = 'blindgrid' }

    Write-Host ""
    Write-Host "  $(Paint "$version installed" '1')"
    Write-Host ""
    Write-Host '  Next:'
    Write-Host "    $(Paint 'blindgrid config show' '1')      $(Paint '· see what is configured' '90')"
    Write-Host "    $(Paint 'blindgrid player add' '1')       $(Paint '· add someone who plays' '90')"
    Write-Host "    $(Paint 'blindgrid generate' '1')         $(Paint '· plan this month' '90')"
    Write-Host ""
    Write-Host "  $(Paint 'This tool predicts nothing. Lottery draws are independent events,' '90')"
    Write-Host "  $(Paint 'and no combination is more likely than another.' '90')"
    Write-Host ""
    Write-Host "  Docs: $RepoUrl"
    Write-Host ""
}

# ------------------------------------------------------------------------ main

Show-Banner

Write-Step 'Checking your environment'
if (Test-Command 'uv')   { Write-Ok 'uv found' }
if (Test-Command 'pipx') { Write-Ok 'pipx found' }
$found = Find-Python
if ($found) { Write-Ok "Python found: $found" } else { Write-Warn "no Python $MinPython or newer on PATH" }

$chosen = switch ($Method) {
    'Uv'   { if (Test-Command 'uv')   { 'Uv' }   else { Show-Failure 'uv is not installed. See https://docs.astral.sh/uv/' } }
    'Pipx' { if (Test-Command 'pipx') { 'Pipx' } else { Show-Failure 'pipx is not installed. See https://pipx.pypa.io/' } }
    'Venv' { 'Venv' }
    default {
        if (Test-Command 'uv') { 'Uv' } elseif (Test-Command 'pipx') { 'Pipx' } else { 'Venv' }
    }
}

$executable = switch ($chosen) {
    'Uv'   { Install-WithUv }
    'Pipx' { Install-WithPipx }
    'Venv' { Install-WithVenv }
}

if (-not (Test-Path $executable)) {
    Show-Failure "Installation finished but $executable is missing."
}

Write-Step 'Verifying'
& $executable version *> $null
if ($LASTEXITCODE -ne 0) { Show-Failure 'The installed command does not run.' }
Write-Ok 'blindgrid runs'

Write-StarterConfig $executable
Show-PathAdvice $executable
Show-Farewell $executable
