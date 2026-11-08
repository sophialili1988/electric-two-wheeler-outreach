$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$credentialFile = Join-Path $root '.zoho_app_password.secure'
$senderScript = Join-Path $root 'make_test_development_email.py'
$python = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

if (-not (Test-Path -LiteralPath $credentialFile)) {
    throw 'No saved encrypted Zoho credential is available. Open the Zoho test development email form and save it first.'
}
if (-not (Test-Path -LiteralPath $python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) { throw 'Python 3 was not found.' }
    $python = $pythonCommand.Source
}

$encrypted = (Get-Content -LiteralPath $credentialFile -Raw).Trim()
$secure = ConvertTo-SecureString -String $encrypted
$password = [System.Net.NetworkCredential]::new('', $secure).Password

$start = [System.Diagnostics.ProcessStartInfo]::new()
$start.FileName = $python
$start.Arguments = "-X utf8 `"$senderScript`" --send"
$start.WorkingDirectory = $root
$start.UseShellExecute = $false
$start.RedirectStandardInput = $true
$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $start
try {
    if (-not $process.Start()) { throw 'Could not start the mail sender.' }
    $process.StandardInput.WriteLine($password)
    $process.StandardInput.Close()
    $password = ''
    $process.WaitForExit()
    exit $process.ExitCode
} finally {
    $password = ''
    $process.Dispose()
}
