[CmdletBinding()]
param(
    [switch]$SkipDeepSize,
    [switch]$SkipVhdxScan,
    [string]$OutputRoot
)

. "$PSScriptRoot\windows-podman-common.ps1"

if (-not (Test-WindowsHost)) {
    throw "windows-podman-cleanup-report.ps1 must be run from Windows PowerShell or PowerShell on Windows."
}

$run = New-DiagnosticRun -Name "cleanup-report" -OutputRoot $OutputRoot
$knownPaths = @(
    "$env:USERPROFILE\.local\share\containers",
    "$env:USERPROFILE\.local\share\containers\podman",
    "$env:USERPROFILE\.local\share\containers\podman\machine",
    "$env:USERPROFILE\.local\share\containers\storage",
    "$env:LOCALAPPDATA\Docker\wsl",
    "$env:LOCALAPPDATA\rancher-desktop"
)

$pathReports = New-Object System.Collections.Generic.List[object]
foreach ($path in $knownPaths) {
    $exists = Test-Path -LiteralPath $path
    $bytes = $null
    if ($exists -and -not $SkipDeepSize) {
        $bytes = Get-DirectorySizeBytes -Path $path
    }
    $pathReports.Add([ordered]@{
        path = $path
        exists = $exists
        bytes = $bytes
        human = if ($null -ne $bytes) { ConvertTo-HumanSize $bytes } else { $null }
    })
}

$vhdxReports = New-Object System.Collections.Generic.List[object]
if (-not $SkipVhdxScan) {
    Get-ChildItem -LiteralPath $env:LOCALAPPDATA -Recurse -Filter "*.vhdx" -Force -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending |
        Select-Object -First 30 |
        ForEach-Object {
            $vhdxReports.Add([ordered]@{
                path = $_.FullName
                bytes = $_.Length
                human = ConvertTo-HumanSize $_.Length
            })
        }
}

$commands = New-Object System.Collections.Generic.List[object]
foreach ($spec in @(
    @{ Name = "podman_system_df"; Command = "podman"; Args = @("system", "df"); Timeout = 45 },
    @{ Name = "podman_machine_list"; Command = "podman"; Args = @("machine", "list"); Timeout = 20 },
    @{ Name = "wsl_list"; Command = "wsl"; Args = @("--list", "--verbose"); Timeout = 20 },
    @{ Name = "fsutil_diskfree_c"; Command = "fsutil"; Args = @("volume", "diskfree", "c:"); Timeout = 20 }
)) {
    $commands.Add([ordered]@{
        name = $spec.Name
        result = Invoke-LoggedCommand -FilePath $spec.Command -ArgumentList $spec.Args -TimeoutSeconds $spec.Timeout
    })
}

$payload = [ordered]@{
    name = "windows-podman-cleanup-report"
    captured_at = (Get-Date).ToUniversalTime().ToString("o")
    skip_deep_size = [bool]$SkipDeepSize
    skip_vhdx_scan = [bool]$SkipVhdxScan
    paths = $pathReports
    vhdx_files = $vhdxReports
    commands = $commands
    safe_cleanup_guidance = @(
        "Prefer podman system prune only while the runtime is healthy.",
        "Prefer podman machine reset over manual deletion when a full reset is intended.",
        "Do not delete the whole user .local directory.",
        "If deleting Podman machine storage manually, stop Podman and run wsl --shutdown first."
    )
}

Write-JsonFile -Path $run.JsonPath -Payload $payload

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Windows Podman Cleanup Report")
$lines.Add("")
$lines.Add("- captured at: ``$($payload.captured_at)``")
$lines.Add("- deep size: ``$(if ($SkipDeepSize) { 'skipped' } else { 'enabled' })``")
$lines.Add("")
$lines.Add("## Known Runtime Paths")
$lines.Add("")
$lines.Add("| Path | Exists | Size |")
$lines.Add("| --- | --- | ---: |")
foreach ($pathReport in $pathReports) {
    $lines.Add("| ``$($pathReport.path)`` | ``$($pathReport.exists)`` | ``$($pathReport.human)`` |")
}
$lines.Add("")
$lines.Add("## VHDX Files")
$lines.Add("")
if ($vhdxReports.Count -eq 0) {
    $lines.Add("No VHDX files reported, or VHDX scan was skipped.")
} else {
    $lines.Add("| Path | Size |")
    $lines.Add("| --- | ---: |")
    foreach ($vhdx in $vhdxReports) {
        $lines.Add("| ``$($vhdx.path)`` | ``$($vhdx.human)`` |")
    }
}
$lines.Add("")
$lines.Add("## Safe Cleanup Guidance")
$lines.Add("")
foreach ($item in $payload.safe_cleanup_guidance) {
    $lines.Add("- $item")
}
$lines.Add("")
foreach ($entry in $commands) {
    foreach ($line in (Format-CommandMarkdown -Title $entry.name -Result $entry.result)) {
        $lines.Add([string]$line)
    }
}
Write-MarkdownFile -Path $run.MarkdownPath -Lines $lines.ToArray()

Write-Host "Windows Podman cleanup report complete."
Write-Host "JSON: $($run.JsonPath)"
Write-Host "Markdown: $($run.MarkdownPath)"
