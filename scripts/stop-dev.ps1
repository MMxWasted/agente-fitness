[CmdletBinding()]
param(
    [switch]$RemoveDatabaseVolume
)

. (Join-Path $PSScriptRoot 'dev-common.ps1')

$failures = [System.Collections.Generic.List[string]]::new()

foreach ($service in @('frontend', 'backend')) {
    try {
        Stop-DevManagedProcess -Service $service
    }
    catch {
        $failures.Add("${service}: $($_.Exception.Message)")
    }
}

if (-not (Test-DevCommand -Name 'docker')) {
    $failures.Add('Docker no está disponible; no se pudo ejecutar Docker Compose down.')
}
else {
    try {
        if ($RemoveDatabaseVolume) {
            Write-Warning 'Se solicitó explícitamente eliminar el volumen PostgreSQL y todos sus datos locales.'
            Invoke-DevDockerCompose -Arguments @('down', '--volumes')
        }
        else {
            Invoke-DevDockerCompose -Arguments @('down')
        }

        $volumeResult = Invoke-DevCommandCapture `
            -Command 'docker' `
            -Arguments @('volume', 'inspect', $script:DevDatabaseVolumeName) `
            -AllowFailure
        if ($RemoveDatabaseVolume) {
            if ($volumeResult.ExitCode -eq 0) {
                $failures.Add("El volumen $script:DevDatabaseVolumeName sigue existiendo.")
            }
            else {
                Write-Host 'El volumen PostgreSQL fue eliminado por petición explícita.'
            }
        }
        elseif ($volumeResult.ExitCode -eq 0) {
            Write-Host "Volumen PostgreSQL conservado: $script:DevDatabaseVolumeName"
        }
        else {
            Write-Host 'No existía un volumen PostgreSQL que conservar.'
        }
    }
    catch {
        $failures.Add("Docker Compose: $($_.Exception.Message)")
    }
}

if ($failures.Count -gt 0) {
    foreach ($failure in $failures) {
        Write-Warning $failure
    }
    throw 'La parada terminó con incidencias; revisa los mensajes anteriores.'
}

Write-Host "Parada completada. Los logs se conservan en $(Get-DevLogsDirectory)."
