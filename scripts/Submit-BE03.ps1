[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9._-]+$')]
    [string]$RepoName = "flyrank-be03-auth-login-protect",
    [switch]$SkipGitHub
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Command $($Arguments -join ' ')" }
}

Write-Host "`n=== BE-03 Auth API submission workflow ===" -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Install Python 3.10+ with the Python launcher (py)." }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Install Git for Windows." }
if (-not (Test-Path ".env.example")) { throw "Missing .env.example." }

$ignore = Get-Content ".gitignore" -Raw
if ($ignore -notmatch '(?m)^\.env$' -or $ignore -notmatch '(?m)^\.env\.\*$' -or $ignore -notmatch '(?m)^!\.env\.example$') {
    throw ".gitignore must ignore .env and .env.* while allowing .env.example."
}
if (Test-Path ".env") {
    git check-ignore -q .env
    if ($LASTEXITCODE -ne 0) { throw "Safety stop: .env exists but is not ignored by Git." }
}

if (-not (Test-Path ".venv\Scripts\python.exe")) { Invoke-Checked "py" @("-3", "-m", "venv", ".venv") }
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
Invoke-Checked $python @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked $python @("-m", "pip", "install", "-r", "requirements.txt")

New-Item -ItemType Directory -Force -Path "artifacts" | Out-Null
$testOutput = & $python -m pytest -q --junitxml="artifacts\pytest-junit.xml" 2>&1
$testExit = $LASTEXITCODE
$testOutput | Tee-Object -FilePath "artifacts\pytest-output.txt"
if ($testExit -ne 0) { throw "Tests failed. Review artifacts\pytest-output.txt. Publishing stopped." }
Invoke-Checked $python @("-m", "compileall", "-q", "app", "tests")

$pythonVersion = (& $python --version 2>&1 | Out-String).Trim()
$gitVersion = (git --version | Out-String).Trim()
$testSummary = ($testOutput | Out-String).Trim()
$ghExe = Join-Path $env:ProgramFiles "GitHub CLI\gh.exe"
$ghUser = ""
if (-not $SkipGitHub) {
    if (-not (Test-Path $ghExe)) {
        $ghCommand = Get-Command gh -ErrorAction SilentlyContinue
        if ($ghCommand) { $ghExe = $ghCommand.Source } else { throw "Install GitHub CLI, reopen PowerShell, then run gh auth login." }
    }
    & $ghExe auth status
    if ($LASTEXITCODE -ne 0) { throw "GitHub CLI is not authenticated. Run gh auth login." }
    $ghUser = (& $ghExe api user --jq .login).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $ghUser) { throw "Could not identify authenticated GitHub user." }
}
$repoUrl = if ($ghUser) { "https://github.com/$ghUser/$RepoName" } else { "(GitHub publishing skipped)" }
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
@"
# BE-03 Submission Evidence

- Generated: $timestamp
- Project: FlyRank BE-03 â€” Auth: Login & Protect
- Runtime: $pythonVersion
- Git: $gitVersion
- Automated tests: PASS
- Static compilation: PASS
- GitHub repository: $repoUrl

## Test output

````text
$testSummary
````

## Scope and checkpoints

The automated suite uses mocked Supabase responses. It tests API behavior without a live Supabase project. Live signup/login/token revocation must be confirmed separately against your configured Supabase project.

- Public route returns 200 without a token.
- Protected profile returns 401 without a token.
- Valid/invalid token behavior is tested using the mocked provider adapter.
- Signup returns 201 on provider success; login returns 200 with access/refresh tokens.
- Logout returns 204 on successful revocation.
- Swagger UI is at `/docs`; protected routes use HTTP Bearer security.

## Secret handling

- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- Do not commit credentials, passwords, tokens, refresh tokens, or service-role keys.
"@ | Set-Content -Encoding utf8 "docs\submission-evidence.md"

# Initialize only when needed; support rerunning after a GitHub name collision.
if (-not (Test-Path ".git")) {
    git init -b main
    if ($LASTEXITCODE -ne 0) { throw "git init failed." }
} else {
    $existingRemotes = @(git remote)
    if ($existingRemotes -contains "origin") { throw "origin already exists. Inspect git remote -v before continuing." }
}

$stages = @(
    @{ Message = "Stage 0: setup FastAPI and Supabase configuration"; Files = @(".gitignore", ".env.example", "requirements.txt", "app/__init__.py", "app/config.py", "app/services/__init__.py") },
    @{ Message = "Stage 1: implement Supabase signup and login adapter"; Files = @("app/services/supabase_auth.py") },
    @{ Message = "Stage 2: add reusable bearer-token verification dependency"; Files = @("app/dependencies.py") },
    @{ Message = "Stage 3: add authentication and public API routes"; Files = @("app/routers/__init__.py", "app/routers/auth.py", "app/routers/public.py") },
    @{ Message = "Stage 4: protect profile and dashboard endpoints"; Files = @("app/routers/protected.py", "app/main.py") },
    @{ Message = "Stage 5: add API tests and security documentation"; Files = @("tests/__init__.py", "tests/test_api.py", "README.md", "docs/security.md", "docs/submission-evidence-template.md", "scripts/Run-Local.ps1", ".github/workflows/tests.yml") },
    @{ Message = "Stage 6: generate submission evidence and publishing workflow"; Files = @("scripts/Submit-BE03.ps1", "docs/submission-evidence.md", "artifacts/pytest-junit.xml", "artifacts/pytest-output.txt") }
)
foreach ($stage in $stages) {
    $paths = @($stage.Files | Where-Object { Test-Path $_ })
    if ($paths.Count -eq 0) { continue }
    git add -- $paths
    if ($LASTEXITCODE -ne 0) { throw "git add failed for $($stage.Message)" }
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Write-Host "No new files for $($stage.Message)" -ForegroundColor DarkYellow; continue }
    git -c user.name="Costas Pinto" -c user.email="costaspinto312@gmail.com" commit -m $stage.Message
    if ($LASTEXITCODE -ne 0) { throw "Commit failed: $($stage.Message)" }
}
git ls-files --error-unmatch .env 2>$null | Out-Null
$EnvTrackedExitCode = $LASTEXITCODE
if ($EnvTrackedExitCode -eq 0) {
    throw ".env is tracked by Git. Remove it from the index before continuing; do not publish secrets."
}
if ($LASTEXITCODE -eq 0) { throw "Safety stop: .env is tracked. Do not publish." }

if ($SkipGitHub) {
    Write-Host "`nLocal tests and artifacts are ready. GitHub publishing skipped." -ForegroundColor Green
    git status --short
    git log --oneline --max-count=8
    exit 0
}

# Create a new public repo. If the name is taken, rerun with a new -RepoName.
& $ghExe repo create $RepoName --public --source . --remote origin --description "FlyRank BE-03: FastAPI Supabase Auth, JWT verification, protected routes, tests, and submission evidence"
if ($LASTEXITCODE -ne 0) { throw "GitHub repository creation failed. If the name is taken, rerun with a unique -RepoName." }
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed. Inspect GitHub and origin before retrying." }

Write-Host "`n=== Submission workflow completed ===" -ForegroundColor Green
Write-Host "Repository: https://github.com/$ghUser/$RepoName" -ForegroundColor Cyan
Write-Host "Evidence: docs\submission-evidence.md"
Write-Host "JUnit report: artifacts\pytest-junit.xml"
git status --short
git log --oneline --max-count=8
git remote -v

