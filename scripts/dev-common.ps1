Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:DevRepositoryRoot = Split-Path -Parent $PSScriptRoot
$script:DevStateDirectory = Join-Path $script:DevRepositoryRoot '.dev-state'
$script:DevLogsDirectory = Join-Path $script:DevStateDirectory 'logs'
$script:DevDatabaseVolumeName = 'agente_fitness_postgres_data'

function Get-DevRepositoryRoot {
    return $script:DevRepositoryRoot
}

function Get-DevStateDirectory {
    return $script:DevStateDirectory
}

function Get-DevLogsDirectory {
    return $script:DevLogsDirectory
}

function Get-DevEncodingProbeMessage {
    return 'Configuración, preparación y detención.'
}

function Test-DevCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Assert-DevCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$InstallHint
    )

    if (-not (Test-DevCommand -Name $Name)) {
        throw "No se encontró '$Name'. $InstallHint"
    }
}

function Invoke-DevCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory = $script:DevRepositoryRoot
    )

    Push-Location $WorkingDirectory
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "El comando '$Command $($Arguments -join ' ')' terminó con código $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-DevCommandCapture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory = $script:DevRepositoryRoot,

        [switch]$AllowFailure
    )

    $commandInfo = Get-Command $Command -ErrorAction Stop
    $commandPath = if ($null -ne $commandInfo.PSObject.Properties['Path']) {
        [string]$commandInfo.Path
    }
    else {
        [string]$commandInfo.Source
    }
    if ([string]::IsNullOrWhiteSpace($commandPath)) {
        throw "No se pudo resolver el ejecutable nativo '$Command'."
    }

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    if ([System.IO.Path]::GetExtension($commandPath) -in @('.cmd', '.bat')) {
        $commandParts = @(
            (ConvertTo-DevCmdArgument -Value $commandPath)
        )
        $commandParts += @($Arguments | ForEach-Object {
            ConvertTo-DevCmdArgument -Value $_
        })
        $startInfo.FileName = $env:ComSpec
        $startInfo.Arguments = '/d /s /c "' + ($commandParts -join ' ') + '"'
    }
    else {
        $startInfo.FileName = $commandPath
        $startInfo.Arguments = (
            @($Arguments | ForEach-Object {
                ConvertTo-DevNativeArgument -Value $_
            }) -join ' '
        )
    }

    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $startInfo.StandardErrorEncoding = [System.Text.Encoding]::UTF8

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "No se pudo iniciar el ejecutable nativo '$Command'."
        }

        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        $exitCode = $process.ExitCode
    }
    finally {
        $process.Dispose()
    }

    $result = [pscustomobject]@{
        ExitCode = $exitCode
        StdOut = $stdout
        StdErr = $stderr
        Output = @(
            (ConvertFrom-DevCapturedText -Text $stdout)
            (ConvertFrom-DevCapturedText -Text $stderr)
        )
    }

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "El comando nativo '$Command' terminó con código $exitCode."
    }

    return $result
}

function ConvertFrom-DevCapturedText {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text
    )

    if ([string]::IsNullOrEmpty($Text)) {
        return
    }

    return @($Text -split "\r?\n" | Where-Object { $_ -ne '' })
}

function Read-DevEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "No existe el archivo de entorno requerido: $Path"
    }

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path -Encoding utf8) {
        $trimmedLine = $line.Trim()
        if (-not $trimmedLine -or $trimmedLine.StartsWith('#')) {
            continue
        }

        $separatorIndex = $trimmedLine.IndexOf('=')
        if ($separatorIndex -lt 1) {
            continue
        }

        $key = $trimmedLine.Substring(0, $separatorIndex).Trim()
        $value = $trimmedLine.Substring($separatorIndex + 1).Trim()
        if (
            $value.Length -ge 2 -and
            (
                ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'"))
            )
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        $values[$key] = $value
    }

    return $values
}

function ConvertTo-DevPort {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Value,

        [Parameter(Mandatory = $true)]
        [int]$Default,

        [Parameter(Mandatory = $true)]
        [string]$VariableName
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Default
    }

    $port = 0
    if (-not [int]::TryParse($Value, [ref]$port) -or $port -lt 1 -or $port -gt 65535) {
        throw "$VariableName debe ser un puerto válido entre 1 y 65535."
    }

    return $port
}

function Get-DevConfiguration {
    $rootEnvPath = Join-Path $script:DevRepositoryRoot '.env'
    $values = @{}
    if (Test-Path -LiteralPath $rootEnvPath -PathType Leaf) {
        $values = Read-DevEnvFile -Path $rootEnvPath
    }

    $backendValue = if ($values.ContainsKey('BACKEND_PORT')) {
        $values['BACKEND_PORT']
    }
    else {
        $null
    }
    $frontendValue = if ($values.ContainsKey('FRONTEND_PORT')) {
        $values['FRONTEND_PORT']
    }
    else {
        $null
    }
    $postgresValue = if ($values.ContainsKey('POSTGRES_PORT')) {
        $values['POSTGRES_PORT']
    }
    else {
        $null
    }

    $backendPort = ConvertTo-DevPort `
        -Value $backendValue `
        -Default 8000 `
        -VariableName 'BACKEND_PORT'
    $frontendPort = ConvertTo-DevPort `
        -Value $frontendValue `
        -Default 5173 `
        -VariableName 'FRONTEND_PORT'
    $postgresPort = ConvertTo-DevPort `
        -Value $postgresValue `
        -Default 5432 `
        -VariableName 'POSTGRES_PORT'

    return [pscustomobject]@{
        BackendPort = $backendPort
        FrontendPort = $frontendPort
        PostgresPort = $postgresPort
        BackendBaseUrl = "http://127.0.0.1:$backendPort"
        FrontendUrl = "http://127.0.0.1:$frontendPort"
    }
}

function Copy-DevEnvFileIfMissing {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ExamplePath,

        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )

    if (Test-Path -LiteralPath $DestinationPath -PathType Leaf) {
        Write-Host "Se conserva la configuración existente: $DestinationPath"
        return $false
    }

    if (-not (Test-Path -LiteralPath $ExamplePath -PathType Leaf)) {
        throw "No existe el archivo de ejemplo requerido: $ExamplePath"
    }

    Copy-Item -LiteralPath $ExamplePath -Destination $DestinationPath
    Write-Host "Configuración local creada desde el ejemplo: $DestinationPath"
    return $true
}

function Initialize-DevJwtSecret {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $values = Read-DevEnvFile -Path $Path
    $developmentPlaceholder = (
        'local-development-only-replace-with-at-least-32-random-bytes'
    )
    if (
        $values.ContainsKey('JWT_SECRET_KEY') -and
        -not [string]::IsNullOrWhiteSpace($values['JWT_SECRET_KEY']) -and
        $values['JWT_SECRET_KEY'] -ne $developmentPlaceholder
    ) {
        Write-Host "Se conserva el secreto JWT local existente: $Path"
        return $false
    }

    $secretBytes = New-Object byte[] 48
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($secretBytes)
    }
    finally {
        $generator.Dispose()
    }
    $secret = [Convert]::ToBase64String($secretBytes)

    $lines = [System.Collections.Generic.List[string]]::new()
    $replaced = $false
    foreach ($line in Get-Content -LiteralPath $Path -Encoding utf8) {
        if ($line -match '^JWT_SECRET_KEY=') {
            $lines.Add("JWT_SECRET_KEY=$secret")
            $replaced = $true
        }
        else {
            $lines.Add($line)
        }
    }
    if (-not $replaced) {
        $lines.Add("JWT_SECRET_KEY=$secret")
    }

    $utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllLines($Path, $lines, $utf8WithoutBom)
    Write-Host "Se generó un secreto JWT exclusivo para el entorno local: $Path"
    return $true
}

function Assert-DevEnvironmentFiles {
    $requiredFiles = @(
        (Join-Path $script:DevRepositoryRoot '.env'),
        (Join-Path $script:DevRepositoryRoot 'frontend\.env'),
        (Join-Path $script:DevRepositoryRoot 'backend\.env')
    )

    $missingFiles = @($requiredFiles | Where-Object {
        -not (Test-Path -LiteralPath $_ -PathType Leaf)
    })

    if ($missingFiles.Count -gt 0) {
        throw (
            "Faltan archivos de entorno: $($missingFiles -join ', '). " +
            "Ejecuta .\scripts\setup-dev.ps1 y revisa los valores locales."
        )
    }

    $rootValues = Read-DevEnvFile -Path $requiredFiles[0]
    $frontendValues = Read-DevEnvFile -Path $requiredFiles[1]
    $backendValues = Read-DevEnvFile -Path $requiredFiles[2]

    $requiredValues = @(
        [pscustomobject]@{ Values = $rootValues; Key = 'POSTGRES_DB'; File = '.env' },
        [pscustomobject]@{ Values = $rootValues; Key = 'POSTGRES_USER'; File = '.env' },
        [pscustomobject]@{ Values = $rootValues; Key = 'POSTGRES_PASSWORD'; File = '.env' },
        [pscustomobject]@{ Values = $frontendValues; Key = 'VITE_API_BASE_URL'; File = 'frontend\.env' },
        [pscustomobject]@{ Values = $backendValues; Key = 'DATABASE_URL'; File = 'backend\.env' },
        [pscustomobject]@{ Values = $backendValues; Key = 'JWT_SECRET_KEY'; File = 'backend\.env' }
    )

    foreach ($requiredValue in $requiredValues) {
        if (
            -not $requiredValue.Values.ContainsKey($requiredValue.Key) -or
            [string]::IsNullOrWhiteSpace($requiredValue.Values[$requiredValue.Key])
        ) {
            throw (
                "Falta $($requiredValue.Key) en $($requiredValue.File). " +
                "Edita ese archivo antes de continuar."
            )
        }
    }

    $null = Get-DevConfiguration
}

function Get-DevComposeEnvFile {
    param(
        [switch]$RequireLocal
    )

    $localEnv = Join-Path $script:DevRepositoryRoot '.env'
    if (Test-Path -LiteralPath $localEnv -PathType Leaf) {
        return $localEnv
    }

    if ($RequireLocal) {
        throw "Falta .env. Ejecuta .\scripts\setup-dev.ps1 antes de continuar."
    }

    return (Join-Path $script:DevRepositoryRoot '.env.example')
}

function Invoke-DevDockerCompose {
    param(
        [string[]]$Arguments = @(),

        [switch]$Capture,

        [switch]$RequireLocalEnv,

        [switch]$AllowFailure
    )

    $envFile = Get-DevComposeEnvFile -RequireLocal:$RequireLocalEnv
    $composeArguments = @('compose', '--env-file', $envFile) + $Arguments

    if ($Capture) {
        return Invoke-DevCommandCapture `
            -Command 'docker' `
            -Arguments $composeArguments `
            -WorkingDirectory $script:DevRepositoryRoot `
            -AllowFailure:$AllowFailure
    }

    Invoke-DevCommand `
        -Command 'docker' `
        -Arguments $composeArguments `
        -WorkingDirectory $script:DevRepositoryRoot
}

function ConvertFrom-DevComposePsJson {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Json
    )

    if ([string]::IsNullOrWhiteSpace($Json)) {
        Write-Output -NoEnumerate ([object[]]@())
        return
    }

    try {
        $parsed = $Json | ConvertFrom-Json
    }
    catch {
        throw 'Docker Compose devolvió un estado JSON no válido.'
    }

    if ($null -eq $parsed) {
        Write-Output -NoEnumerate ([object[]]@())
        return
    }

    Write-Output -NoEnumerate ([object[]]@($parsed))
}

function Get-DevObjectPropertyText {
    param(
        [AllowNull()]
        [psobject]$InputObject,

        [Parameter(Mandatory = $true)]
        [string]$Name,

        [string]$Default = ''
    )

    if ($null -eq $InputObject) {
        return $Default
    }

    $property = $InputObject.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) {
        return $Default
    }

    $text = [string]$property.Value
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $Default
    }

    return $text.Trim()
}

function Get-DevPostgresStateFromServices {
    param(
        [AllowNull()]
        [object[]]$Services
    )

    $serviceItems = if ($null -eq $Services) {
        @()
    }
    else {
        @($Services)
    }
    $postgresServices = @($serviceItems | Where-Object {
        (Get-DevObjectPropertyText -InputObject $_ -Name 'Service') -eq 'postgres'
    })

    if ($postgresServices.Count -eq 0) {
        return [pscustomobject]@{
            State = 'not_started'
            ContainerStatus = 'not_started'
            Health = 'not_started'
            ContainerId = $null
            Detail = 'El contenedor PostgreSQL no está iniciado.'
        }
    }

    $postgres = $postgresServices[0]
    $containerId = Get-DevObjectPropertyText -InputObject $postgres -Name 'ID'
    $containerStatus = Get-DevObjectPropertyText `
        -InputObject $postgres `
        -Name 'State' `
        -Default 'unknown'
    $health = Get-DevObjectPropertyText `
        -InputObject $postgres `
        -Name 'Health' `
        -Default 'unknown'
    $state = if ($containerStatus -eq 'running' -and $health -eq 'healthy') {
        'available'
    }
    elseif ($containerStatus -eq 'running') {
        'started_unavailable'
    }
    elseif ($containerStatus -eq 'unknown') {
        'unknown'
    }
    else {
        'not_started'
    }

    return [pscustomobject]@{
        State = $state
        ContainerStatus = $containerStatus
        Health = $health
        ContainerId = if ($containerId) { $containerId } else { $null }
        Detail = "Contenedor: $containerStatus; health: $health."
    }
}

function Get-DevPostgresState {
    if (-not (Test-DevCommand -Name 'docker')) {
        return [pscustomobject]@{
            State = 'unknown'
            ContainerStatus = 'unknown'
            Health = 'unknown'
            ContainerId = $null
            Detail = 'Docker no está disponible.'
        }
    }

    $containerResult = Invoke-DevDockerCompose `
        -Arguments @('ps', '--format', 'json', 'postgres') `
        -Capture `
        -AllowFailure
    if ($containerResult.ExitCode -ne 0) {
        return [pscustomobject]@{
            State = 'unknown'
            ContainerStatus = 'unknown'
            Health = 'unknown'
            ContainerId = $null
            Detail = 'No se pudo consultar Docker Compose.'
        }
    }

    try {
        $services = ConvertFrom-DevComposePsJson -Json $containerResult.StdOut
        return (Get-DevPostgresStateFromServices -Services $services)
    }
    catch {
        return [pscustomobject]@{
            State = 'unknown'
            ContainerStatus = 'unknown'
            Health = 'unknown'
            ContainerId = $null
            Detail = $_.Exception.Message
        }
    }
}

function Initialize-DevStateDirectories {
    $null = New-Item -ItemType Directory -Path $script:DevStateDirectory -Force
    $null = New-Item -ItemType Directory -Path $script:DevLogsDirectory -Force
}

function Get-DevProcessStatePath {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service
    )

    return (Join-Path $script:DevStateDirectory "$Service.json")
}

function Get-DevManagedProcessRecord {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service
    )

    $statePath = Get-DevProcessStatePath -Service $Service
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        return $null
    }

    try {
        return (Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json)
    }
    catch {
        return [pscustomobject]@{
            service = $Service
            invalid = $true
        }
    }
}

function Test-DevProcessRecord {
    param(
        [AllowNull()]
        [psobject]$Record
    )

    if ($null -eq $Record) {
        return [pscustomobject]@{
            State = 'not_started'
            Process = $null
            Detail = 'No existe un proceso registrado.'
        }
    }

    if (
        $null -ne $Record.PSObject.Properties['invalid'] -or
        $null -eq $Record.PSObject.Properties['pid'] -or
        $null -eq $Record.PSObject.Properties['processStartTimeUtc']
    ) {
        return [pscustomobject]@{
            State = 'unknown'
            Process = $null
            Detail = 'El archivo de estado no es válido.'
        }
    }

    $process = Get-Process -Id ([int]$Record.pid) -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        return [pscustomobject]@{
            State = 'stale'
            Process = $null
            Detail = 'El PID registrado ya no existe.'
        }
    }

    try {
        $expectedStartTime = [datetime]::Parse(
            [string]$Record.processStartTimeUtc,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::RoundtripKind
        ).ToUniversalTime()
        $actualStartTime = $process.StartTime.ToUniversalTime()
    }
    catch {
        return [pscustomobject]@{
            State = 'unknown'
            Process = $process
            Detail = 'No se pudo verificar la identidad del proceso.'
        }
    }

    if ($expectedStartTime.Ticks -ne $actualStartTime.Ticks) {
        return [pscustomobject]@{
            State = 'stale'
            Process = $process
            Detail = 'El PID fue reutilizado por otro proceso.'
        }
    }

    return [pscustomobject]@{
        State = 'running'
        Process = $process
        Detail = "Proceso gestionado con PID $($process.Id)."
    }
}

function Get-DevManagedProcessStatus {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service
    )

    $record = Get-DevManagedProcessRecord -Service $Service
    $status = Test-DevProcessRecord -Record $record

    return [pscustomobject]@{
        Service = $Service
        Record = $record
        State = $status.State
        Process = $status.Process
        Detail = $status.Detail
    }
}

function Remove-DevProcessState {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service
    )

    $statePath = Get-DevProcessStatePath -Service $Service
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        Remove-Item -LiteralPath $statePath -Force
    }
}

function Clear-DevStaleProcessState {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service
    )

    $status = Get-DevManagedProcessStatus -Service $Service
    if ($status.State -eq 'stale') {
        Write-Warning "${Service}: $($status.Detail) Se elimina únicamente el registro obsoleto."
        Remove-DevProcessState -Service $Service
        return (Get-DevManagedProcessStatus -Service $Service)
    }

    return $status
}

function Assert-DevServiceCanStart {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service,

        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $status = Clear-DevStaleProcessState -Service $Service
    if ($status.State -eq 'running') {
        return $status
    }

    if ($status.State -eq 'unknown') {
        throw "${Service}: $($status.Detail)"
    }

    if (Test-DevTcpPort -Port $Port) {
        throw (
            "El puerto $Port ya está ocupado por un proceso no gestionado por estos scripts. " +
            'No se detendrá automáticamente; libera el puerto o ajusta la configuración.'
        )
    }

    return $status
}

function ConvertTo-DevNativeArgument {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Value
    )

    if ($Value.IndexOf([char]0) -ge 0) {
        throw 'Un argumento del proceso contiene un carácter nulo no admitido.'
    }

    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    $builder = [System.Text.StringBuilder]::new()
    $null = $builder.Append('"')
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') {
            $backslashes += 1
            continue
        }

        if ($character -eq '"') {
            $null = $builder.Append('\' * (($backslashes * 2) + 1))
            $null = $builder.Append('"')
        }
        else {
            if ($backslashes -gt 0) {
                $null = $builder.Append('\' * $backslashes)
            }
            $null = $builder.Append($character)
        }
        $backslashes = 0
    }

    if ($backslashes -gt 0) {
        $null = $builder.Append('\' * ($backslashes * 2))
    }
    $null = $builder.Append('"')

    return $builder.ToString()
}

function ConvertTo-DevCmdArgument {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    if ($Value -match '["&|<>^%\r\n]') {
        throw 'Un argumento del proceso contiene caracteres no admitidos por el lanzador local.'
    }

    return '"' + $Value + '"'
}

function Start-DevManagedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service,

        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    Initialize-DevStateDirectories

    $stdoutPath = Join-Path $script:DevLogsDirectory "$Service.stdout.log"
    $stderrPath = Join-Path $script:DevLogsDirectory "$Service.stderr.log"
    [System.IO.File]::WriteAllText($stdoutPath, '')
    [System.IO.File]::WriteAllText($stderrPath, '')

    $process = $null
    try {
        $commandParts = @(
            (ConvertTo-DevCmdArgument -Value $FilePath)
        )
        $commandParts += @($ArgumentList | ForEach-Object {
            ConvertTo-DevCmdArgument -Value $_
        })
        $commandLine = (
            ($commandParts -join ' ') +
            ' 1>' + (ConvertTo-DevCmdArgument -Value $stdoutPath) +
            ' 2>' + (ConvertTo-DevCmdArgument -Value $stderrPath)
        )

        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $env:ComSpec
        $startInfo.Arguments = '/d /s /c "' + $commandLine + '"'
        $startInfo.WorkingDirectory = $WorkingDirectory
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        $process = [System.Diagnostics.Process]::Start($startInfo)
        if ($null -eq $process) {
            throw "No se pudo iniciar el proceso gestionado para $Service."
        }

        $processStartTime = $process.StartTime.ToUniversalTime().ToString(
            'o',
            [System.Globalization.CultureInfo]::InvariantCulture
        )
        $record = [ordered]@{
            service = $Service
            pid = $process.Id
            processStartTimeUtc = $processStartTime
            startedAtUtc = [datetime]::UtcNow.ToString(
                'o',
                [System.Globalization.CultureInfo]::InvariantCulture
            )
            stdoutLog = ".dev-state/logs/$Service.stdout.log"
            stderrLog = ".dev-state/logs/$Service.stderr.log"
        }

        $statePath = Get-DevProcessStatePath -Service $Service
        $record | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
        return (Get-DevManagedProcessRecord -Service $Service)
    }
    catch {
        if ($null -ne $process -and -not $process.HasExited) {
            & taskkill.exe /PID $process.Id /T /F | Out-Null
        }
        throw
    }
}

function Stop-DevManagedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service
    )

    $status = Get-DevManagedProcessStatus -Service $Service
    if ($status.State -eq 'not_started') {
        Write-Host "${Service}: no existe un proceso gestionado."
        return
    }

    if ($status.State -eq 'stale') {
        Write-Warning "${Service}: $($status.Detail) No se detiene ningún proceso."
        Remove-DevProcessState -Service $Service
        return
    }

    if ($status.State -ne 'running') {
        throw "${Service}: $($status.Detail) Se rechaza la detención por seguridad."
    }

    Assert-DevCommand `
        -Name 'taskkill.exe' `
        -InstallHint 'Este script de PowerShell requiere Windows.'

    & taskkill.exe /PID $status.Process.Id /T /F
    $taskkillExitCode = $LASTEXITCODE

    for ($attempt = 1; $attempt -le 20; $attempt += 1) {
        if ($null -eq (Get-Process -Id $status.Process.Id -ErrorAction SilentlyContinue)) {
            break
        }
        Start-Sleep -Milliseconds 250
    }

    if ($null -ne (Get-Process -Id $status.Process.Id -ErrorAction SilentlyContinue)) {
        throw "${Service}: no se pudo detener el árbol del PID $($status.Process.Id)."
    }

    if ($taskkillExitCode -ne 0) {
        Write-Warning "${Service}: taskkill terminó con código $taskkillExitCode, pero el PID ya no existe."
    }

    Remove-DevProcessState -Service $Service
    Write-Host "${Service}: proceso gestionado detenido."
}

function Show-DevServiceLogTail {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service,

        [int]$Lines = 40
    )

    foreach ($stream in @('stderr', 'stdout')) {
        $path = Join-Path $script:DevLogsDirectory "$Service.$stream.log"
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $content = @(Get-Content -LiteralPath $path -Tail $Lines -Encoding utf8)
            if ($content.Count -gt 0) {
                Write-Host "Últimas líneas de $Service ($stream):"
                $content | ForEach-Object { Write-Host $_ }
            }
        }
    }
}

function Test-DevTcpPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [int]$TimeoutMilliseconds = 500
    )

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $connection.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) {
            return $false
        }

        $client.EndConnect($connection)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Get-DevHttpResponse {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [int]$TimeoutSeconds = 3
    )

    try {
        $response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri $Uri `
            -TimeoutSec $TimeoutSeconds
        return [pscustomobject]@{
            Succeeded = $true
            StatusCode = [int]$response.StatusCode
            Content = [string]$response.Content
            Detail = 'Solicitud completada.'
        }
    }
    catch {
        $statusCode = $null
        if (
            $null -ne $_.Exception.Response -and
            $null -ne $_.Exception.Response.StatusCode
        ) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }

        return [pscustomobject]@{
            Succeeded = $false
            StatusCode = $statusCode
            Content = $null
            Detail = 'No se obtuvo una respuesta HTTP válida.'
        }
    }
}

function Test-DevHttpContract {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [AllowNull()]
        [string]$ExpectedBody
    )

    $response = Get-DevHttpResponse -Uri $Uri
    $bodyMatches = [string]::IsNullOrEmpty($ExpectedBody)
    if (-not [string]::IsNullOrEmpty($ExpectedBody) -and $null -ne $response.Content) {
        $bodyMatches = $response.Content.Trim() -eq $ExpectedBody
    }

    return [pscustomobject]@{
        Available = (
            $response.Succeeded -and
            $response.StatusCode -eq 200 -and
            $bodyMatches
        )
        Response = $response
    }
}

function Wait-DevHttpContract {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('backend', 'frontend')]
        [string]$Service,

        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [AllowNull()]
        [string]$ExpectedBody,

        [int]$Attempts = 30
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt += 1) {
        $processStatus = Get-DevManagedProcessStatus -Service $Service
        if ($processStatus.State -ne 'running') {
            throw "$Service terminó antes de estar disponible. $($processStatus.Detail)"
        }

        $contract = Test-DevHttpContract -Uri $Uri -ExpectedBody $ExpectedBody
        if ($contract.Available) {
            return
        }

        if ($attempt -lt $Attempts) {
            Start-Sleep -Seconds 1
        }
    }

    throw "$Service no respondió correctamente en $Uri después de $Attempts intentos."
}
