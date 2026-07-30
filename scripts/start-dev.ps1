[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'dev-common.ps1')

function Wait-ForPostgres {
    param(
        [int]$Attempts = 30
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt += 1) {
        $state = Get-DevPostgresState
        if ($state.State -eq 'available') {
            Write-Host 'PostgreSQL está saludable.'
            return
        }

        if ($attempt -lt $Attempts) {
            Start-Sleep -Seconds 1
        }
    }

    Write-Host 'Estado de Docker Compose:'
    Invoke-DevDockerCompose -Arguments @('ps') -RequireLocalEnv
    Write-Host 'Últimas líneas de PostgreSQL:'
    Invoke-DevDockerCompose -Arguments @('logs', '--tail', '50', 'postgres') -RequireLocalEnv
    throw "PostgreSQL no alcanzó el estado healthy después de $Attempts intentos."
}

function Stop-StartedServices {
    param(
        [string[]]$Services
    )

    for ($index = $Services.Count - 1; $index -ge 0; $index -= 1) {
        try {
            Stop-DevManagedProcess -Service $Services[$index]
        }
        catch {
            Write-Warning "No se pudo revertir $($Services[$index]): $($_.Exception.Message)"
        }
    }
}

$repositoryRoot = Get-DevRepositoryRoot
$configuration = Get-DevConfiguration
$startedServices = [System.Collections.Generic.List[string]]::new()
$postgresStartedThisRun = $false
$startupCompleted = $false

try {
    Assert-DevEnvironmentFiles
    Assert-DevCommand -Name 'docker' -InstallHint 'Instala o inicia Docker con Compose v2.'
    Assert-DevCommand -Name 'uv' -InstallHint 'Ejecuta .\scripts\setup-dev.ps1 después de instalar uv.'
    Assert-DevCommand -Name 'npm.cmd' -InstallHint 'Ejecuta .\scripts\setup-dev.ps1 después de instalar Node.js.'

    $dockerInfo = Invoke-DevCommandCapture `
        -Command 'docker' `
        -Arguments @('info', '--format', '{{.ServerVersion}}') `
        -AllowFailure
    if ($dockerInfo.ExitCode -ne 0) {
        throw 'Docker está instalado, pero su daemon no está disponible.'
    }

    Write-Host 'Validando Docker Compose...'
    Invoke-DevDockerCompose -Arguments @('config', '--quiet') -RequireLocalEnv

    $postgresBeforeStart = Get-DevPostgresState
    $postgresWasRunning = $postgresBeforeStart.ContainerStatus -eq 'running'

    Write-Host 'Iniciando únicamente PostgreSQL...'
    Invoke-DevDockerCompose -Arguments @('up', '-d', 'postgres') -RequireLocalEnv
    $postgresStartedThisRun = -not $postgresWasRunning
    Wait-ForPostgres

    Write-Host 'Aplicando migraciones Alembic...'
    Invoke-DevCommand `
        -Command 'uv' `
        -Arguments @('run', 'alembic', 'upgrade', 'head') `
        -WorkingDirectory (Join-Path $repositoryRoot 'backend')

    $backendStatus = Assert-DevServiceCanStart `
        -Service 'backend' `
        -Port $configuration.BackendPort
    if ($backendStatus.State -eq 'running') {
        $healthContract = Test-DevHttpContract `
            -Uri "$($configuration.BackendBaseUrl)/health" `
            -ExpectedBody '{"status":"ok"}'
        $readyContract = Test-DevHttpContract `
            -Uri "$($configuration.BackendBaseUrl)/ready" `
            -ExpectedBody '{"status":"ready"}'
        if (-not $healthContract.Available -or -not $readyContract.Available) {
            throw 'El backend gestionado ya estaba iniciado, pero no cumple /health y /ready.'
        }
        Write-Host 'Backend ya iniciado por estos scripts; no se crea un duplicado.'
    }
    else {
        Write-Host 'Iniciando backend FastAPI...'
        $uvPath = (Get-Command 'uv' -ErrorAction Stop).Source
        $null = Start-DevManagedProcess `
            -Service 'backend' `
            -FilePath $uvPath `
            -ArgumentList @(
                'run',
                'uvicorn',
                'app.main:app',
                '--reload',
                '--host',
                '127.0.0.1',
                '--port',
                [string]$configuration.BackendPort
            ) `
            -WorkingDirectory (Join-Path $repositoryRoot 'backend')
        $startedServices.Add('backend')

        try {
            Wait-DevHttpContract `
                -Service 'backend' `
                -Uri "$($configuration.BackendBaseUrl)/health" `
                -ExpectedBody '{"status":"ok"}'
            Wait-DevHttpContract `
                -Service 'backend' `
                -Uri "$($configuration.BackendBaseUrl)/ready" `
                -ExpectedBody '{"status":"ready"}'
        }
        catch {
            Show-DevServiceLogTail -Service 'backend'
            throw
        }
    }

    $frontendStatus = Assert-DevServiceCanStart `
        -Service 'frontend' `
        -Port $configuration.FrontendPort
    if ($frontendStatus.State -eq 'running') {
        $frontendContract = Test-DevHttpContract -Uri $configuration.FrontendUrl
        if (-not $frontendContract.Available) {
            throw 'El frontend gestionado ya estaba iniciado, pero no está disponible.'
        }
        Write-Host 'Frontend ya iniciado por estos scripts; no se crea un duplicado.'
    }
    else {
        Write-Host 'Iniciando frontend Vite...'
        $npmPath = (Get-Command 'npm.cmd' -ErrorAction Stop).Source
        $null = Start-DevManagedProcess `
            -Service 'frontend' `
            -FilePath $npmPath `
            -ArgumentList @(
                'run',
                'dev',
                '--',
                '--host',
                '127.0.0.1',
                '--port',
                [string]$configuration.FrontendPort,
                '--strictPort'
            ) `
            -WorkingDirectory (Join-Path $repositoryRoot 'frontend')
        $startedServices.Add('frontend')

        try {
            Wait-DevHttpContract `
                -Service 'frontend' `
                -Uri $configuration.FrontendUrl `
                -ExpectedBody $null
        }
        catch {
            Show-DevServiceLogTail -Service 'frontend'
            throw
        }
    }

    $startupCompleted = $true
    Write-Host ''
    Write-Host 'Entorno local disponible:'
    Write-Host "Frontend: $($configuration.FrontendUrl)"
    Write-Host "Backend: $($configuration.BackendBaseUrl)"
    Write-Host "OpenAPI: $($configuration.BackendBaseUrl)/docs"
    Write-Host "Liveness: $($configuration.BackendBaseUrl)/health"
    Write-Host "Readiness: $($configuration.BackendBaseUrl)/ready"
    Write-Host "Logs: $(Get-DevLogsDirectory)"
    Write-Host 'Detención: .\scripts\stop-dev.ps1'
}
finally {
    if (-not $startupCompleted) {
        Write-Warning 'El arranque no se completó; se revierten únicamente los recursos iniciados por esta ejecución.'
        Stop-StartedServices -Services $startedServices.ToArray()

        if ($postgresStartedThisRun -and (Test-DevCommand -Name 'docker')) {
            try {
                Invoke-DevDockerCompose -Arguments @('down')
            }
            catch {
                Write-Warning "No se pudo detener PostgreSQL durante la reversión: $($_.Exception.Message)"
            }
        }
    }
}
