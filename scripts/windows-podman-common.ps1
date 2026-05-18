Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-PolyglotRepositoryRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function ConvertTo-HumanSize {
    param(
        [Parameter(Mandatory = $true)]
        [Int64]$Bytes
    )

    $units = @("B", "KiB", "MiB", "GiB", "TiB")
    $value = [double]$Bytes
    foreach ($unit in $units) {
        if ($value -lt 1024 -or $unit -eq $units[-1]) {
            if ($unit -eq "B") {
                return "{0} {1}" -f [int64]$value, $unit
            }
            return "{0:N1} {1}" -f $value, $unit
        }
        $value = $value / 1024
    }
}

function New-DiagnosticRun {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [string]$OutputRoot
    )

    $root = Get-PolyglotRepositoryRoot
    if (-not $OutputRoot) {
        $OutputRoot = Join-Path $root ".artifacts\diagnostics\windows-podman"
    }
    New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    return [ordered]@{
        Name = $Name
        Timestamp = $timestamp
        RepositoryRoot = $root
        OutputRoot = (Resolve-Path $OutputRoot).Path
        JsonPath = Join-Path $OutputRoot "$Name-$timestamp.json"
        MarkdownPath = Join-Path $OutputRoot "$Name-$timestamp.md"
    }
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [int]$TimeoutSeconds = 30,
        [string]$WorkingDirectory = $null
    )

    $startedAt = (Get-Date).ToUniversalTime().ToString("o")
    $result = [ordered]@{
        command = @($FilePath) + $ArgumentList
        started_at = $startedAt
        timeout_seconds = $TimeoutSeconds
        ok = $false
        timed_out = $false
        exit_code = $null
        stdout = ""
        stderr = ""
        error = $null
    }

    try {
        $processInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $processInfo.FileName = $FilePath
        $quotedArguments = foreach ($argument in $ArgumentList) {
            if ($argument -match '^[A-Za-z0-9_./:=@%+\-]+$') {
                $argument
            } else {
                '"' + ($argument -replace '"', '\"') + '"'
            }
        }
        $processInfo.Arguments = ($quotedArguments -join " ")
        if ($WorkingDirectory) {
            $processInfo.WorkingDirectory = $WorkingDirectory
        }
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true

        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $processInfo
        [void]$process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()

        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $result.timed_out = $true
            try {
                $process.Kill($true)
            } catch {
                try { $process.Kill() } catch { }
            }
        } else {
            $result.exit_code = $process.ExitCode
            $result.ok = ($process.ExitCode -eq 0)
        }

        $result.stdout = $stdoutTask.GetAwaiter().GetResult()
        $result.stderr = $stderrTask.GetAwaiter().GetResult()
    } catch {
        $result.error = $_.Exception.Message
    }

    return $result
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [object]$Payload
    )

    $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Write-MarkdownFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string[]]$Lines
    )

    $Lines | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Format-CommandMarkdown {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [object]$Result
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("## $Title")
    $lines.Add("")
    $lines.Add("- command: ``$($Result.command -join ' ')``")
    $lines.Add("- status: ``$(if ($Result.ok) { 'ok' } elseif ($Result.timed_out) { 'timeout' } else { 'failed' })``")
    if ($null -ne $Result.exit_code) {
        $lines.Add("- exit code: ``$($Result.exit_code)``")
    }
    if ($Result.error) {
        $lines.Add("- error: ``$($Result.error)``")
    }
    if ($Result.stdout.Trim()) {
        $lines.Add("")
        $lines.Add("stdout:")
        $lines.Add("")
        $lines.Add("````text")
        $lines.Add($Result.stdout.Trim())
        $lines.Add("````")
    }
    if ($Result.stderr.Trim()) {
        $lines.Add("")
        $lines.Add("stderr:")
        $lines.Add("")
        $lines.Add("````text")
        $lines.Add($Result.stderr.Trim())
        $lines.Add("````")
    }
    $lines.Add("")
    return $lines.ToArray()
}

function Get-DirectorySizeBytes {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $total = [int64]0
    Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            $total += $_.Length
        }
    return $total
}

function Test-WindowsHost {
    if ($PSVersionTable.ContainsKey("Platform")) {
        return $PSVersionTable.Platform -eq "Win32NT" -or $env:OS -eq "Windows_NT"
    }
    return $env:OS -eq "Windows_NT"
}
