[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'dev-common.ps1')

function Get-RequiredToolErrors {
    $errors = [System.Collections.Generic.List[string]]::new()
    $requirements = @(
        [pscustomobject]@{ Name = 'git'; Hint = 'Instala Git y vuelve a ejecutar el script.' },
        [pscustomobject]@{ Name = 'node'; Hint = 'Instala una versión de Node.js compatible con Vite 8.' },
        [pscustomobject]@{ Name = 'npm.cmd'; Hint = 'Instala npm junto con Node.js.' },
        [pscustomobject]@{ Name = 'uv'; Hint = 'Instala uv fuera del repositorio.' },
        [pscustomobject]@{ Name = 'docker'; Hint = 'Instala o inicia Docker con Compose v2.' }
    )

    foreach ($requirement in $requirements) {
        if (-not (Test-DevCommand -Name $requirement.Name)) {
            $errors.Add("No se encontró '$($requirement.Name)'. $($requirement.Hint)")
        }
    }

    if ($errors.Count -gt 0) {
        return $errors
    }

    foreach ($toolCheck in @(
        [pscustomobject]@{ Command = 'git'; Arguments = @('--version'); Label = 'Git' },
        [pscustomobject]@{ Command = 'npm.cmd'; Arguments = @('--version'); Label = 'npm' },
        [pscustomobject]@{ Command = 'uv'; Arguments = @('--version'); Label = 'uv' }
    )) {
        $toolResult = Invoke-DevCommandCapture `
            -Command $toolCheck.Command `
            -Arguments $toolCheck.Arguments `
            -AllowFailure
        if ($toolResult.ExitCode -ne 0) {
            $errors.Add("No se pudo ejecutar $($toolCheck.Label).")
        }
    }

    $nodeResult = Invoke-DevCommandCapture `
        -Command 'node' `
        -Arguments @('--version') `
        -AllowFailure
    if ($nodeResult.ExitCode -ne 0) {
        $errors.Add('No se pudo obtener la versión de Node.js.')
    }
    else {
        $nodeVersionText = ([string]($nodeResult.Output | Select-Object -First 1)).Trim().TrimStart('v')
        try {
            $nodeVersion = [version]$nodeVersionText
            $nodeCompatible = (
                ($nodeVersion.Major -eq 20 -and $nodeVersion.Minor -ge 19) -or
                ($nodeVersion.Major -eq 22 -and $nodeVersion.Minor -ge 12) -or
                $nodeVersion.Major -gt 22
            )
            if (-not $nodeCompatible) {
                $errors.Add(
                    "Node.js $nodeVersionText no es compatible con Vite 8. " +
                    'Usa 20.19+, 22.12+ o una versión posterior compatible.'
                )
            }
        }
        catch {
            $errors.Add("No se pudo interpretar la versión de Node.js: $nodeVersionText")
        }
    }

    $composeResult = Invoke-DevCommandCapture `
        -Command 'docker' `
        -Arguments @('compose', 'version', '--short') `
        -AllowFailure
    if ($composeResult.ExitCode -ne 0) {
        $errors.Add('Docker Compose v2 no está disponible.')
    }
    else {
        $composeVersionText = ([string]($composeResult.Output | Select-Object -First 1)).Trim().TrimStart('v')
        try {
            $composeVersion = [version]$composeVersionText
            if ($composeVersion.Major -lt 2) {
                $errors.Add("Se requiere Docker Compose v2; se detectó $composeVersionText.")
            }
        }
        catch {
            $errors.Add("No se pudo interpretar la versión de Docker Compose: $composeVersionText")
        }
    }

    $dockerInfoResult = Invoke-DevCommandCapture `
        -Command 'docker' `
        -Arguments @('info', '--format', '{{.ServerVersion}}') `
        -AllowFailure
    if ($dockerInfoResult.ExitCode -ne 0) {
        $errors.Add('Docker está instalado, pero su daemon no está disponible.')
    }

    return $errors
}

Write-Host 'Comprobando herramientas de desarrollo...'
$toolErrors = @(Get-RequiredToolErrors)
if ($toolErrors.Count -gt 0) {
    foreach ($toolError in $toolErrors) {
        Write-Warning $toolError
    }
    throw 'No se puede preparar el entorno hasta resolver las herramientas indicadas.'
}

$repositoryRoot = Get-DevRepositoryRoot
$null = Copy-DevEnvFileIfMissing `
    -ExamplePath (Join-Path $repositoryRoot '.env.example') `
    -DestinationPath (Join-Path $repositoryRoot '.env')
$null = Copy-DevEnvFileIfMissing `
    -ExamplePath (Join-Path $repositoryRoot 'frontend\.env.example') `
    -DestinationPath (Join-Path $repositoryRoot 'frontend\.env')
$null = Copy-DevEnvFileIfMissing `
    -ExamplePath (Join-Path $repositoryRoot 'backend\.env.example') `
    -DestinationPath (Join-Path $repositoryRoot 'backend\.env')

Assert-DevEnvironmentFiles

Write-Host 'Instalando dependencias frontend desde package-lock.json...'
Invoke-DevCommand `
    -Command 'npm.cmd' `
    -Arguments @('ci') `
    -WorkingDirectory (Join-Path $repositoryRoot 'frontend')

Write-Host 'Sincronizando dependencias backend desde uv.lock...'
Invoke-DevCommand `
    -Command 'uv' `
    -Arguments @('sync', '--locked') `
    -WorkingDirectory (Join-Path $repositoryRoot 'backend')

Write-Host 'Preparación completada sin sobrescribir archivos de entorno existentes.'
Write-Host 'Revisa .env, frontend\.env y backend\.env antes de iniciar si cambiaste puertos o credenciales.'
