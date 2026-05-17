[CmdletBinding()]
param(
    [string]$MachineName = "podman-machine-default",
    [switch]$Apply,
    [string]$OutputRoot
)

. "$PSScriptRoot\windows-podman-common.ps1"

if (-not (Test-WindowsHost)) {
    throw "windows-podman-repair.ps1 must be run from Windows PowerShell or PowerShell on Windows."
}

$run = New-DiagnosticRun -Name "repair" -OutputRoot $OutputRoot
$actions = New-Object System.Collections.Generic.List[object]

function Invoke-RepairAction {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "$(if ($Apply) { 'Applying' } else { 'Would apply' }): $Name"
    if (-not $Apply) {
        $actions.Add([ordered]@{ name = $Name; applied = $false; result = $null })
        return $null
    }

    $result = & $Action
    $actions.Add([ordered]@{ name = $Name; applied = $true; result = $result })
    return $result
}

function Ensure-HostWslConfig {
    $path = Join-Path $env:USERPROFILE ".wslconfig"
    $required = "kernelCommandLine=cgroup_no_v1=all systemd.unified_cgroup_hierarchy=1"
    if (Test-Path -LiteralPath $path) {
        $content = Get-Content -LiteralPath $path -Raw
        if ($content -match [regex]::Escape($required)) {
            return [ordered]@{ ok = $true; detail = ".wslconfig already contains required kernelCommandLine" }
        }
        if ($content -match "(?m)^\s*kernelCommandLine\s*=") {
            return [ordered]@{
                ok = $false
                detail = ".wslconfig already has kernelCommandLine; edit manually to include: $required"
            }
        }
        Copy-Item -LiteralPath $path -Destination "$path.polyglot-backup-$(Get-Date -Format yyyyMMddHHmmss)" -Force
        Add-Content -LiteralPath $path -Value "`n[wsl2]`n$required"
        return [ordered]@{ ok = $true; detail = "appended [wsl2] kernelCommandLine to .wslconfig" }
    }

    "[wsl2]`n$required`n" | Set-Content -LiteralPath $path -Encoding ASCII
    return [ordered]@{ ok = $true; detail = "created .wslconfig with required kernelCommandLine" }
}

function Invoke-WslRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [int]$TimeoutSeconds = 45
    )
    return Invoke-LoggedCommand -FilePath "wsl" -ArgumentList @("-d", $MachineName, "-u", "root", "--", "sh", "-lc", $Command) -TimeoutSeconds $TimeoutSeconds
}

Invoke-RepairAction -Name "ensure host WSL cgroup v2 kernel settings" -Action {
    Ensure-HostWslConfig
} | Out-Null

Invoke-RepairAction -Name "enable systemd in Podman machine WSL distro" -Action {
    Invoke-WslRoot -Command "cp /etc/wsl.conf /etc/wsl.conf.polyglot-backup-\$(date +%Y%m%d%H%M%S) 2>/dev/null || true; printf '[boot]\nsystemd=true\n[user]\ndefault=user\n' > /etc/wsl.conf"
} | Out-Null

Invoke-RepairAction -Name "shutdown WSL so boot settings apply" -Action {
    Invoke-LoggedCommand -FilePath "wsl" -ArgumentList @("--shutdown") -TimeoutSeconds 60
} | Out-Null

Invoke-RepairAction -Name "start Podman machine" -Action {
    Invoke-LoggedCommand -FilePath "podman" -ArgumentList @("machine", "start", $MachineName) -TimeoutSeconds 180
} | Out-Null

$inspect = Invoke-LoggedCommand -FilePath "podman" -ArgumentList @("machine", "inspect", $MachineName) -TimeoutSeconds 30
$actions.Add([ordered]@{ name = "inspect Podman machine metadata"; applied = $true; result = $inspect })

$sshPort = $null
try {
    if ($inspect.ok -and $inspect.stdout.Trim()) {
        $machine = ($inspect.stdout | ConvertFrom-Json)[0]
        $sshPort = [string]$machine.SSHConfig.Port
    }
} catch {
    $sshPort = $null
}

if ($sshPort) {
    Invoke-RepairAction -Name "align sshd and podman socket services to machine metadata port $sshPort" -Action {
        $command = @"
ssh-keygen -A
if grep -q '^Port ' /etc/ssh/sshd_config; then
  sed -i 's/^Port .*/Port $sshPort/' /etc/ssh/sshd_config
else
  printf '\nPort $sshPort\n' >> /etc/ssh/sshd_config
fi
systemctl enable --now sshd
systemctl restart sshd
systemctl enable --now podman.socket
systemctl restart podman.socket
ss -ltnp | grep '$sshPort' || true
ls -l /run/podman/podman.sock /run/user/1000/podman/podman.sock 2>/dev/null || true
"@
        Invoke-WslRoot -Command $command -TimeoutSeconds 90
    } | Out-Null
} else {
    $actions.Add([ordered]@{
        name = "align sshd and podman socket services"
        applied = $false
        result = [ordered]@{ ok = $false; error = "could not resolve SSH port from podman machine inspect" }
    })
}

Invoke-RepairAction -Name "select rootful Podman connection" -Action {
    Invoke-LoggedCommand -FilePath "podman" -ArgumentList @("system", "connection", "default", "$MachineName-root") -TimeoutSeconds 20
} | Out-Null

$podmanPs = Invoke-LoggedCommand -FilePath "podman" -ArgumentList @("ps") -TimeoutSeconds 30
$actions.Add([ordered]@{ name = "verify podman ps"; applied = $true; result = $podmanPs })

$payload = [ordered]@{
    name = "windows-podman-repair"
    captured_at = (Get-Date).ToUniversalTime().ToString("o")
    machine_name = $MachineName
    applied = [bool]$Apply
    overall_ok = $podmanPs.ok
    actions = $actions
    next_steps_if_unhealthy = @(
        "Run scripts/windows-podman-preflight.ps1 -InspectMachineInternals.",
        "If the machine is still unhealthy, use podman machine reset -f rather than deleting user profile directories.",
        "If Docker API forwarding is blocked by \\\\.\\pipe\\docker_engine, use devcontainer --docker-path podman."
    )
}

Write-JsonFile -Path $run.JsonPath -Payload $payload

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Windows Podman Repair")
$lines.Add("")
$lines.Add("- captured at: ``$($payload.captured_at)``")
$lines.Add("- machine: ``$MachineName``")
$lines.Add("- applied: ``$($payload.applied)``")
$lines.Add("- overall: ``$(if ($payload.overall_ok) { 'pass' } else { 'fail' })``")
$lines.Add("")
foreach ($action in $actions) {
    $lines.Add("## $($action.name)")
    $lines.Add("")
    $lines.Add("- applied: ``$($action.applied)``")
    if ($action.result) {
        if ($action.result.PSObject.Properties.Name -contains "command") {
            foreach ($line in (Format-CommandMarkdown -Title "result" -Result $action.result)) {
                $lines.Add([string]$line)
            }
        } else {
            $lines.Add("")
            $lines.Add("````json")
            $lines.Add(($action.result | ConvertTo-Json -Depth 10))
            $lines.Add("````")
        }
    }
}
$lines.Add("## Next Steps If Unhealthy")
$lines.Add("")
foreach ($step in $payload.next_steps_if_unhealthy) {
    $lines.Add("- $step")
}
Write-MarkdownFile -Path $run.MarkdownPath -Lines $lines.ToArray()

Write-Host "Windows Podman repair: $(if ($podmanPs.ok) { 'PASS' } else { 'FAIL' })"
Write-Host "JSON: $($run.JsonPath)"
Write-Host "Markdown: $($run.MarkdownPath)"

if (-not $podmanPs.ok) {
    exit 1
}
