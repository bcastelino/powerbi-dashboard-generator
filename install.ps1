<#
.SYNOPSIS
  Power BI Dashboard Generator - skills installer (Windows PowerShell / pwsh).

.DESCRIPTION
  Clones the repo into $HOME\.powerbi-dashboard-generator and links each skill
  under $HOME\.claude\skills (or the target you pass as an argument).

.EXAMPLE
  # One-liner from any PowerShell prompt:
  irm https://raw.githubusercontent.com/bcastelino/powerbi-dashboard-generator/main/install.ps1 | iex

.EXAMPLE
  # Custom target directory:
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/bcastelino/powerbi-dashboard-generator/main/install.ps1))) "$HOME\.windsurf\skills"

.NOTES
  Symlink creation on Windows requires either:
    - An elevated (Administrator) PowerShell session, OR
    - Developer Mode enabled (Settings -> Update & Security -> For developers)
  If symlinks fail, the script falls back to a full copy.
#>

param(
    [string]$Target = "$HOME\.claude\skills"
)

$ErrorActionPreference = "Stop"

$RepoOwner = "bcastelino"
$RepoName  = "powerbi-dashboard-generator"
$RepoUrl   = "https://github.com/$RepoOwner/$RepoName.git"
$RepoDir   = Join-Path $HOME ".$RepoName"

Write-Host "-> Installing $RepoName skills" -ForegroundColor Blue
Write-Host "   repo:   $RepoUrl" -ForegroundColor DarkGray
Write-Host "   target: $Target" -ForegroundColor DarkGray

# 1. Clone or update the source checkout
if (Test-Path (Join-Path $RepoDir ".git")) {
    Write-Host "-> Updating existing checkout in $RepoDir"
    git -C $RepoDir pull --ff-only --quiet
} else {
    Write-Host "-> Cloning into $RepoDir"
    git clone --depth 1 --quiet $RepoUrl $RepoDir
}

# 2. Ensure target directory exists
New-Item -ItemType Directory -Force -Path $Target | Out-Null

# 3. Link each skill into the target directory
$count = 0
Get-ChildItem (Join-Path $RepoDir "skills") -Directory | ForEach-Object {
    $dest = Join-Path $Target $_.Name
    if (Test-Path $dest) {
        Write-Host "   v $($_.Name) (already present, skipping)" -ForegroundColor DarkGray
        return
    }
    try {
        New-Item -ItemType SymbolicLink -Path $dest -Target $_.FullName -ErrorAction Stop | Out-Null
        Write-Host "   v $($_.Name)" -ForegroundColor Green
    } catch {
        # Fall back to copy if symlink fails (no admin / dev mode)
        Copy-Item -Recurse $_.FullName $dest
        Write-Host "   v $($_.Name) (copied; enable Developer Mode for symlinks)" -ForegroundColor Yellow
    }
    $count++
}

# 4. Install Python dependencies if pip is available
Write-Host ""
if (Get-Command pip -ErrorAction SilentlyContinue) {
    Write-Host "-> Installing Python dependencies"
    try {
        pip install --quiet -r (Join-Path $RepoDir "requirements.txt")
    } catch {
        Write-Host "   ! pip install failed - run it manually: pip install -r $RepoDir\requirements.txt" -ForegroundColor DarkGray
    }
} else {
    Write-Host "   ! pip not found - install Python deps manually: pip install -r $RepoDir\requirements.txt" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "v Installed $count new skills to $Target" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart your agent runtime (Claude Code, Windsurf, etc.)"
Write-Host "  2. Ask the agent: 'List the skills you have available'"
Write-Host "  3. Try it: 'Build me a sales dashboard from sales.xlsx'"
