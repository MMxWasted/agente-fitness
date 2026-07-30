[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot 'dev-common.ps1')

$testsRun = 0
$temporaryRoot = Join-Path `
    ([System.IO.Path]::GetTempPath()) `
    "agente-fitness-dev-scripts-$([guid]::NewGuid().ToString('N'))"

function Assert-DevTest {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Condition,

        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $script:testsRun += 1
    if (-not $Condition) {
        throw "Prueba fallida: $Message"
    }
}

try {
    $null = New-Item -ItemType Directory -Path $temporaryRoot

    $examplePath = Join-Path $temporaryRoot '.env.example'
    $destinationPath = Join-Path $temporaryRoot '.env'
    @(
        '# ejemplo',
        'VALUE=first',
        'QUOTED="two words"',
        'PORT=8123'
    ) | Set-Content -LiteralPath $examplePath -Encoding utf8

    $created = Copy-DevEnvFileIfMissing `
        -ExamplePath $examplePath `
        -DestinationPath $destinationPath
    Assert-DevTest -Condition $created -Message 'Debe crear un .env inexistente.'

    'VALUE=preserved' | Set-Content -LiteralPath $destinationPath -Encoding utf8
    $createdAgain = Copy-DevEnvFileIfMissing `
        -ExamplePath $examplePath `
        -DestinationPath $destinationPath
    Assert-DevTest -Condition (-not $createdAgain) -Message 'No debe sobrescribir un .env existente.'
    $preservedContent = Get-Content -LiteralPath $destinationPath -Raw -Encoding utf8
    Assert-DevTest `
        -Condition ($preservedContent.Trim() -eq 'VALUE=preserved') `
        -Message 'El contenido local debe conservarse.'

    $parsedValues = Read-DevEnvFile -Path $examplePath
    Assert-DevTest `
        -Condition ($parsedValues['QUOTED'] -eq 'two words') `
        -Message 'Debe interpretar valores entre comillas.'
    Assert-DevTest `
        -Condition ($parsedValues['PORT'] -eq '8123') `
        -Message 'Debe leer variables por nombre.'

    $backendEnvPath = Join-Path $temporaryRoot 'backend.env'
    @(
        'JWT_SECRET_KEY=local-development-only-replace-with-at-least-32-random-bytes'
    ) | Set-Content -LiteralPath $backendEnvPath -Encoding utf8
    $jwtCreated = Initialize-DevJwtSecret -Path $backendEnvPath
    $generatedValues = Read-DevEnvFile -Path $backendEnvPath
    Assert-DevTest `
        -Condition (
            $jwtCreated -and
            $generatedValues['JWT_SECRET_KEY'].Length -ge 32 -and
            $generatedValues['JWT_SECRET_KEY'] -notmatch 'local-development'
        ) `
        -Message 'Debe sustituir el marcador JWT por un secreto local aleatorio.'
    $generatedSecret = $generatedValues['JWT_SECRET_KEY']
    $jwtCreatedAgain = Initialize-DevJwtSecret -Path $backendEnvPath
    $preservedValues = Read-DevEnvFile -Path $backendEnvPath
    Assert-DevTest `
        -Condition (
            -not $jwtCreatedAgain -and
            $preservedValues['JWT_SECRET_KEY'] -eq $generatedSecret
        ) `
        -Message 'Debe conservar un secreto JWT local ya configurado.'

    Assert-DevTest `
        -Condition ((ConvertTo-DevPort -Value '8123' -Default 8000 -VariableName 'TEST_PORT') -eq 8123) `
        -Message 'Debe aceptar puertos válidos.'
    Assert-DevTest `
        -Condition ((ConvertTo-DevPort -Value '' -Default 8000 -VariableName 'TEST_PORT') -eq 8000) `
        -Message 'Debe aplicar el puerto predeterminado.'

    Assert-DevTest `
        -Condition ((ConvertTo-DevCmdArgument -Value 'two words') -eq '"two words"') `
        -Message 'Debe citar argumentos seguros para el proceso gestionado.'

    $unsafeArgumentRejected = $false
    try {
        $null = ConvertTo-DevCmdArgument -Value 'unsafe&command'
    }
    catch {
        $unsafeArgumentRejected = $true
    }
    Assert-DevTest `
        -Condition $unsafeArgumentRejected `
        -Message 'Debe rechazar metacaracteres del shell.'

    $errorActionPreferenceBeforeCapture = $ErrorActionPreference
    $nativeSuccess = Invoke-DevCommandCapture `
        -Command 'powershell.exe' `
        -Arguments @(
            '-NoProfile',
            '-Command',
            "[Console]::OutputEncoding = [Text.Encoding]::UTF8; " +
            "[Console]::Out.WriteLine('salida correcta'); " +
            "[Console]::Error.WriteLine('mensaje informativo'); exit 0"
        )
    Assert-DevTest `
        -Condition ($nativeSuccess.ExitCode -eq 0) `
        -Message 'Debe conservar el código cero aunque el comando escriba en stderr.'
    Assert-DevTest `
        -Condition ($nativeSuccess.StdOut -match 'salida correcta') `
        -Message 'Debe capturar stdout por separado.'
    Assert-DevTest `
        -Condition ($nativeSuccess.StdErr -match 'mensaje informativo') `
        -Message 'Debe capturar stderr informativo sin NativeCommandError.'
    Assert-DevTest `
        -Condition ($ErrorActionPreference -eq $errorActionPreferenceBeforeCapture) `
        -Message 'La captura no debe alterar ErrorActionPreference.'

    $nativeFailure = Invoke-DevCommandCapture `
        -Command 'powershell.exe' `
        -Arguments @(
            '-NoProfile',
            '-Command',
            "[Console]::Error.WriteLine('fallo esperado'); exit 7"
        ) `
        -AllowFailure
    Assert-DevTest `
        -Condition ($nativeFailure.ExitCode -eq 7) `
        -Message 'Debe devolver el código de salida nativo real cuando se permite inspeccionarlo.'
    Assert-DevTest `
        -Condition ($nativeFailure.StdErr -match 'fallo esperado') `
        -Message 'Debe conservar un diagnóstico de stderr para un fallo nativo.'

    $controlledFailureThrown = $false
    $controlledFailureMessage = ''
    try {
        $null = Invoke-DevCommandCapture `
            -Command 'powershell.exe' `
            -Arguments @('-NoProfile', '-Command', 'exit 9')
    }
    catch {
        $controlledFailureThrown = $true
        $controlledFailureMessage = $_.Exception.Message
    }
    Assert-DevTest `
        -Condition $controlledFailureThrown `
        -Message 'Debe lanzar un error controlado cuando el proceso nativo falla.'
    Assert-DevTest `
        -Condition (
            $controlledFailureMessage -match 'código 9' -and
            $controlledFailureMessage -notmatch 'NativeCommandError'
        ) `
        -Message 'El error nativo debe indicar el código sin exponer un NativeCommandError.'

    $emptyComposeServices = ConvertFrom-DevComposePsJson -Json ''
    Assert-DevTest `
        -Condition (
            $emptyComposeServices -is [array] -and
            $emptyComposeServices.Count -eq 0
        ) `
        -Message 'La salida vacía de Compose debe normalizarse como colección vacía.'

    $singleComposeServices = ConvertFrom-DevComposePsJson -Json (
        '{"Service":"postgres","ID":"one","State":"running","Health":"healthy"}'
    )
    Assert-DevTest `
        -Condition (
            $singleComposeServices -is [array] -and
            $singleComposeServices.Count -eq 1
        ) `
        -Message 'Un único servicio JSON de Compose debe normalizarse como colección.'

    $multipleComposeServices = ConvertFrom-DevComposePsJson -Json (
        '[' +
        '{"Service":"postgres","ID":"one","State":"running","Health":"healthy"},' +
        '{"Service":"other","ID":"two","State":"exited","Health":""}' +
        ']'
    )
    Assert-DevTest `
        -Condition (
            $multipleComposeServices -is [array] -and
            $multipleComposeServices.Count -eq 2
        ) `
        -Message 'Varios servicios JSON de Compose deben conservarse como colección.'

    $availablePostgresState = Get-DevPostgresStateFromServices `
        -Services $multipleComposeServices
    Assert-DevTest `
        -Condition (
            $availablePostgresState.State -eq 'available' -and
            $availablePostgresState.ContainerId -eq 'one'
        ) `
        -Message 'Debe reconocer PostgreSQL saludable desde el JSON de Compose.'

    $noPostgresState = Get-DevPostgresStateFromServices -Services @(
        [pscustomobject]@{
            Service = 'other'
            ID = 'two'
            State = 'running'
            Health = 'healthy'
        }
    )
    Assert-DevTest `
        -Condition ($noPostgresState.State -eq 'not_started') `
        -Message 'La ausencia del contenedor PostgreSQL debe ser un estado controlado.'

    $nullComposeHandled = $true
    try {
        $nullComposeServices = ConvertFrom-DevComposePsJson -Json 'null'
        $nullPostgresState = Get-DevPostgresStateFromServices `
            -Services $nullComposeServices
        $nullComposeHandled = (
            $nullComposeServices -is [array] -and
            $nullComposeServices.Count -eq 0 -and
            $nullPostgresState.State -eq 'not_started'
        )
    }
    catch {
        $nullComposeHandled = $false
    }
    Assert-DevTest `
        -Condition $nullComposeHandled `
        -Message 'Los estados nulos no deben provocar invocaciones de métodos sobre null.'

    $originalStateDirectory = $script:DevStateDirectory
    try {
        $script:DevStateDirectory = Join-Path $temporaryRoot 'missing-state'
        $backendWithoutPid = Get-DevManagedProcessStatus -Service 'backend'
        $frontendWithoutPid = Get-DevManagedProcessStatus -Service 'frontend'
        Assert-DevTest `
            -Condition (
                $backendWithoutPid.State -eq 'not_started' -and
                $frontendWithoutPid.State -eq 'not_started'
            ) `
            -Message 'La ausencia de archivos PID debe producir estados no iniciados.'
    }
    finally {
        $script:DevStateDirectory = $originalStateDirectory
    }

    $expectedEncodingMessage = (
        'Configuraci' + [char]0x00F3 + 'n, preparaci' + [char]0x00F3 +
        'n y detenci' + [char]0x00F3 + 'n.'
    )
    Assert-DevTest `
        -Condition (
            (Get-DevEncodingProbeMessage) -ceq $expectedEncodingMessage
        ) `
        -Message 'PowerShell 5.1 debe interpretar correctamente los mensajes con acentos.'

    foreach ($scriptPath in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1') {
        $scriptBytes = [System.IO.File]::ReadAllBytes($scriptPath.FullName)
        Assert-DevTest `
            -Condition (
                $scriptBytes.Length -ge 3 -and
                $scriptBytes[0] -eq 0xEF -and
                $scriptBytes[1] -eq 0xBB -and
                $scriptBytes[2] -eq 0xBF
            ) `
            -Message "$($scriptPath.Name) debe usar UTF-8 con BOM para PowerShell 5.1."
    }

    $invalidPortRejected = $false
    try {
        $null = ConvertTo-DevPort -Value '70000' -Default 8000 -VariableName 'TEST_PORT'
    }
    catch {
        $invalidPortRejected = $true
    }
    Assert-DevTest -Condition $invalidPortRejected -Message 'Debe rechazar puertos fuera de rango.'

    $currentProcess = Get-Process -Id $PID
    $validRecord = [pscustomobject]@{
        pid = $PID
        processStartTimeUtc = $currentProcess.StartTime.ToUniversalTime().ToString('o')
    }
    $validStatus = Test-DevProcessRecord -Record $validRecord
    Assert-DevTest `
        -Condition ($validStatus.State -eq 'running') `
        -Message 'Debe reconocer un PID con la misma hora de inicio.'

    $reusedRecord = [pscustomobject]@{
        pid = $PID
        processStartTimeUtc = [datetime]::UtcNow.AddDays(-1).ToString('o')
    }
    $reusedStatus = Test-DevProcessRecord -Record $reusedRecord
    Assert-DevTest `
        -Condition ($reusedStatus.State -eq 'stale') `
        -Message 'Debe rechazar un PID reutilizado.'

    $originalStateDirectory = $script:DevStateDirectory
    $script:DevStateDirectory = Join-Path $temporaryRoot 'port-test-state'
    $listener = [System.Net.Sockets.TcpListener]::new(
        [System.Net.IPAddress]::Loopback,
        0
    )
    try {
        $listener.Start()
        $occupiedPort = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
        Assert-DevTest `
            -Condition (Test-DevTcpPort -Port $occupiedPort) `
            -Message 'Debe detectar un puerto ocupado sin terminar su proceso propietario.'

        $occupiedPortRejected = $false
        try {
            $null = Assert-DevServiceCanStart `
                -Service 'frontend' `
                -Port $occupiedPort
        }
        catch {
            $occupiedPortRejected = $true
        }
        Assert-DevTest `
            -Condition $occupiedPortRejected `
            -Message 'Debe impedir iniciar un servicio sobre un puerto ajeno.'
    }
    finally {
        $listener.Stop()
        $script:DevStateDirectory = $originalStateDirectory
    }

    Write-Host "$testsRun pruebas de scripts superadas."
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot -PathType Container) {
        $resolvedTemporaryRoot = (Resolve-Path -LiteralPath $temporaryRoot).Path
        $resolvedSystemTemp = [System.IO.Path]::GetFullPath(
            [System.IO.Path]::GetTempPath()
        ).TrimEnd('\')
        if (-not $resolvedTemporaryRoot.StartsWith(
            "$resolvedSystemTemp\agente-fitness-dev-scripts-",
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Se rechaza limpiar una ruta temporal inesperada: $resolvedTemporaryRoot"
        }

        Remove-Item -LiteralPath $resolvedTemporaryRoot -Recurse -Force
    }
}
