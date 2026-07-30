[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'dev-common.ps1')

function Write-DevStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Component,

        [Parameter(Mandatory = $true)]
        [ValidateSet('no iniciado', 'iniciado no disponible', 'disponible', 'desconocido')]
        [string]$State,

        [Parameter(Mandatory = $true)]
        [string]$Detail
    )

    Write-Host ('{0,-24} {1,-25} {2}' -f $Component, $State, $Detail)
}

function Get-EndpointState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [AllowNull()]
        [string]$ExpectedBody,

        [Parameter(Mandatory = $true)]
        [psobject]$ManagedProcess,

        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $portOpen = Test-DevTcpPort -Port $Port
    if (-not $portOpen) {
        if ($ManagedProcess.State -eq 'running') {
            return [pscustomobject]@{
                State = 'iniciado no disponible'
                Detail = 'El proceso gestionado existe, pero el puerto no responde.'
            }
        }

        if ($ManagedProcess.State -eq 'unknown') {
            return [pscustomobject]@{
                State = 'desconocido'
                Detail = $ManagedProcess.Detail
            }
        }

        return [pscustomobject]@{
            State = 'no iniciado'
            Detail = 'No se detectó un servicio accesible.'
        }
    }

    $contract = Test-DevHttpContract -Uri $Uri -ExpectedBody $ExpectedBody
    if ($contract.Available) {
        return [pscustomobject]@{
            State = 'disponible'
            Detail = 'HTTP 200 y contrato correcto.'
        }
    }

    if ($ManagedProcess.State -eq 'running' -or $portOpen) {
        return [pscustomobject]@{
            State = 'iniciado no disponible'
            Detail = 'Existe un proceso o puerto activo, pero la respuesta no es válida.'
        }
    }

    if ($ManagedProcess.State -eq 'unknown') {
        return [pscustomobject]@{
            State = 'desconocido'
            Detail = $ManagedProcess.Detail
        }
    }

    return [pscustomobject]@{
        State = 'no iniciado'
        Detail = 'No se detectó un servicio accesible.'
    }
}

$repositoryRoot = Get-DevRepositoryRoot
$configuration = Get-DevConfiguration
$allAvailable = $true

Write-Host ('{0,-24} {1,-25} {2}' -f 'Componente', 'Estado', 'Detalle')
Write-Host ('-' * 90)

if (-not (Test-DevCommand -Name 'docker')) {
    Write-DevStatus -Component 'Docker' -State 'desconocido' -Detail 'CLI no disponible.'
    $postgresState = [pscustomobject]@{ State = 'unknown' }
    $allAvailable = $false
}
else {
    $dockerInfo = Invoke-DevCommandCapture `
        -Command 'docker' `
        -Arguments @('info', '--format', '{{.ServerVersion}}') `
        -AllowFailure
    if ($dockerInfo.ExitCode -ne 0) {
        Write-DevStatus -Component 'Docker' -State 'iniciado no disponible' -Detail 'Daemon no disponible.'
        $postgresState = [pscustomobject]@{ State = 'unknown' }
        $allAvailable = $false
    }
    else {
        Write-DevStatus -Component 'Docker' -State 'disponible' -Detail 'CLI y daemon disponibles.'
        $postgresState = Get-DevPostgresState
    }
}

if ($postgresState.State -eq 'available') {
    Write-DevStatus -Component 'PostgreSQL' -State 'disponible' -Detail $postgresState.Detail
}
elseif ($postgresState.State -eq 'started_unavailable') {
    Write-DevStatus -Component 'PostgreSQL' -State 'iniciado no disponible' -Detail $postgresState.Detail
    $allAvailable = $false
}
elseif ($postgresState.State -eq 'not_started') {
    Write-DevStatus -Component 'PostgreSQL' -State 'no iniciado' -Detail $postgresState.Detail
    $allAvailable = $false
}
else {
    Write-DevStatus -Component 'PostgreSQL' -State 'desconocido' -Detail 'No se pudo determinar su estado.'
    $allAvailable = $false
}

$backendProcess = Get-DevManagedProcessStatus -Service 'backend'
$backendProcessState = if ($backendProcess.State -eq 'running') {
    'disponible'
}
elseif ($backendProcess.State -in @('not_started', 'stale')) {
    'no iniciado'
}
else {
    'desconocido'
}
Write-DevStatus `
    -Component 'Proceso backend' `
    -State $backendProcessState `
    -Detail $backendProcess.Detail

$frontendProcess = Get-DevManagedProcessStatus -Service 'frontend'
$frontendProcessState = if ($frontendProcess.State -eq 'running') {
    'disponible'
}
elseif ($frontendProcess.State -in @('not_started', 'stale')) {
    'no iniciado'
}
else {
    'desconocido'
}
Write-DevStatus `
    -Component 'Proceso frontend' `
    -State $frontendProcessState `
    -Detail $frontendProcess.Detail

$healthState = Get-EndpointState `
    -Uri "$($configuration.BackendBaseUrl)/health" `
    -ExpectedBody '{"status":"ok"}' `
    -ManagedProcess $backendProcess `
    -Port $configuration.BackendPort
Write-DevStatus -Component '/health' -State $healthState.State -Detail $healthState.Detail
if ($healthState.State -ne 'disponible') {
    $allAvailable = $false
}

$readyState = Get-EndpointState `
    -Uri "$($configuration.BackendBaseUrl)/ready" `
    -ExpectedBody '{"status":"ready"}' `
    -ManagedProcess $backendProcess `
    -Port $configuration.BackendPort
Write-DevStatus -Component '/ready' -State $readyState.State -Detail $readyState.Detail
if ($readyState.State -ne 'disponible') {
    $allAvailable = $false
}

$frontendState = Get-EndpointState `
    -Uri $configuration.FrontendUrl `
    -ExpectedBody $null `
    -ManagedProcess $frontendProcess `
    -Port $configuration.FrontendPort
Write-DevStatus -Component 'Frontend' -State $frontendState.State -Detail $frontendState.Detail
if ($frontendState.State -ne 'disponible') {
    $allAvailable = $false
}

if ($postgresState.State -eq 'available' -and (Test-DevCommand -Name 'uv')) {
    $alembicResult = Invoke-DevCommandCapture `
        -Command 'uv' `
        -Arguments @('run', 'alembic', 'current', '--check-heads') `
        -WorkingDirectory (Join-Path $repositoryRoot 'backend') `
        -AllowFailure
    if ($alembicResult.ExitCode -eq 0) {
        $revisionLine = @($alembicResult.Output | Where-Object {
            [string]$_ -match '^[0-9A-Za-z_]+.*\(head\)'
        } | Select-Object -Last 1)
        $revision = if ($revisionLine.Count -gt 0) {
            [string]$revisionLine[0]
        }
        else {
            'La base está en head.'
        }
        Write-DevStatus -Component 'Alembic' -State 'disponible' -Detail $revision
    }
    else {
        Write-DevStatus `
            -Component 'Alembic' `
            -State 'iniciado no disponible' `
            -Detail 'No se pudo confirmar que la revisión actual sea head.'
        $allAvailable = $false
    }
}
else {
    Write-DevStatus `
        -Component 'Alembic' `
        -State 'desconocido' `
        -Detail 'Requiere PostgreSQL saludable y uv.'
    $allAvailable = $false
}

Write-Host "Logs gestionados: $(Get-DevLogsDirectory)"

if (-not $allAvailable) {
    exit 1
}
