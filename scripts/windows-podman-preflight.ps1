[CmdletBinding()]
param(
    [string]$MachineName = "podman-machine-default",
    [int]$MinimumFreeGB = 100,
    [switch]$RunContainerProbe,
    [switch]$InspectMachineInternals,
    [string]$OutputRoot
)

. "$PSScriptRoot\windows-podman-common.ps1"

if (-not (Test-WindowsHost)) {
    throw "windows-podman-preflight.ps1 must be run from Windows PowerShell or PowerShell on Windows."
}

$run = New-DiagnosticRun -Name "preflight" -OutputRoot $OutputRoot
$commands = New-Object System.Collections.Generic.List[object]
$checks = New-Object System.Collections.Generic.List[object]

$driveName = (Get-Location).Drive.Name
if (-not $driveName) {
    $driveName = "C"
}
$drive = Get-PSDrive -Name $driveName
$minimumFreeBytes = [int64]$MinimumFreeGB * 1GB
$checks.Add([ordered]@{
    name = "host_disk_free"
    ok = $drive.Free -ge $minimumFreeBytes
    detail = "$($driveName): free $(ConvertTo-HumanSize $drive.Free), minimum $(ConvertTo-HumanSize $minimumFreeBytes)"
})

$podmanCommand = Get-Command podman -ErrorAction SilentlyContinue
$checks.Add([ordered]@{
    name = "podman_cli_on_path"
    ok = $null -ne $podmanCommand
    detail = if ($podmanCommand) { $podmanCommand.Source } else { "podman not found on PATH" }
})

foreach ($spec in @(
    @{ Name = "wsl_status"; Command = "wsl"; Args = @("--status"); Timeout = 20 },
    @{ Name = "wsl_list"; Command = "wsl"; Args = @("--list", "--verbose"); Timeout = 20 },
    @{ Name = "podman_version"; Command = "podman"; Args = @("--version"); Timeout = 20 },
    @{ Name = "podman_machine_list"; Command = "podman"; Args = @("machine", "list"); Timeout = 20 },
    @{ Name = "podman_connection_list"; Command = "podman"; Args = @("system", "connection", "list"); Timeout = 20 },
    @{ Name = "podman_machine_inspect"; Command = "podman"; Args = @("machine", "inspect", $MachineName); Timeout = 30 },
    @{ Name = "podman_ps"; Command = "podman"; Args = @("ps"); Timeout = 30 },
    @{ Name = "podman_info"; Command = "podman"; Args = @("info"); Timeout = 30 }
)) {
    $result = Invoke-LoggedCommand -FilePath $spec.Command -ArgumentList $spec.Args -TimeoutSeconds $spec.Timeout
    $commands.Add([ordered]@{ name = $spec.Name; result = $result })
    if ($spec.Name -eq "podman_ps") {
        $checks.Add([ordered]@{
            name = "podman_engine_reachable"
            ok = $result.ok
            detail = if ($result.ok) { "podman ps succeeded" } else { ($result.stderr + $result.error).Trim() }
        })
    }
}

if ($InspectMachineInternals) {
    $internalProbe = "systemctl is-system-running || true; systemctl status podman.socket --no-pager || true; systemctl status sshd --no-pager || true; ls -l /etc/ssh/ssh_host_* 2>/dev/null || true; ss -ltnp || true; ls -l /run/podman/podman.sock /run/user/1000/podman/podman.sock 2>/dev/null || true"
    $commands.Add([ordered]@{
        name = "podman_machine_wsl_internals"
        result = Invoke-LoggedCommand -FilePath "wsl" -ArgumentList @("-d", $MachineName, "-u", "root", "--", "sh", "-lc", $internalProbe) -TimeoutSeconds 45
    })
}

if ($RunContainerProbe) {
    $result = Invoke-LoggedCommand -FilePath "podman" -ArgumentList @("run", "--rm", "alpine:3.20", "echo", "podman-ok") -TimeoutSeconds 180
    $commands.Add([ordered]@{ name = "podman_alpine_probe"; result = $result })
    $checks.Add([ordered]@{
        name = "podman_can_run_container"
        ok = $result.ok -and $result.stdout.Contains("podman-ok")
        detail = if ($result.ok) { "alpine probe completed" } else { ($result.stderr + $result.error).Trim() }
    })
}

$overallOk = -not ($checks | Where-Object { -not $_.ok })
$payload = [ordered]@{
    name = "windows-podman-preflight"
    captured_at = (Get-Date).ToUniversalTime().ToString("o")
    machine_name = $MachineName
    minimum_free_gb = $MinimumFreeGB
    overall_ok = $overallOk
    checks = $checks
    commands = $commands
}

Write-JsonFile -Path $run.JsonPath -Payload $payload

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Windows Podman Preflight")
$lines.Add("")
$lines.Add("- captured at: ``$($payload.captured_at)``")
$lines.Add("- machine: ``$MachineName``")
$lines.Add("- overall: ``$(if ($overallOk) { 'pass' } else { 'fail' })``")
$lines.Add("")
$lines.Add("## Checks")
$lines.Add("")
foreach ($check in $checks) {
    $lines.Add("- ``$($check.name)``: ``$(if ($check.ok) { 'pass' } else { 'fail' })`` - $($check.detail)")
}
$lines.Add("")
foreach ($entry in $commands) {
    foreach ($line in (Format-CommandMarkdown -Title $entry.name -Result $entry.result)) {
        $lines.Add([string]$line)
    }
}
Write-MarkdownFile -Path $run.MarkdownPath -Lines $lines.ToArray()

Write-Host "Windows Podman preflight: $(if ($overallOk) { 'PASS' } else { 'FAIL' })"
Write-Host "JSON: $($run.JsonPath)"
Write-Host "Markdown: $($run.MarkdownPath)"

if (-not $overallOk) {
    exit 1
}
