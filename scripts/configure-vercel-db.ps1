param(
    [string]$Scope = "fabio-anselmos-projects",
    [switch]$SetDatabaseUrl,
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando '$Name' nao encontrado no PATH."
    }
}

function Set-VercelEnv {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$ScopeValue
    )

    vercel env add $Name production --scope $ScopeValue --yes --force --value $Value | Out-Host
}

Require-Command "vercel"

Write-Host "Configurando variaveis de banco para Vercel..." -ForegroundColor Cyan
Write-Host ""

$dbHost = Read-Host "DB_HOST"
$dbPort = Read-Host "DB_PORT (padrao 5432)"
if ([string]::IsNullOrWhiteSpace($dbPort)) { $dbPort = "5432" }
$dbName = Read-Host "DB_NAME"
$dbUser = Read-Host "DB_USER"
$dbPasswordSecure = Read-Host "DB_PASSWORD" -AsSecureString
$dbPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPasswordSecure)
)
$dbSslMode = Read-Host "DB_SSLMODE (padrao require)"
if ([string]::IsNullOrWhiteSpace($dbSslMode)) { $dbSslMode = "require" }

if ([string]::IsNullOrWhiteSpace($dbHost) -or
    [string]::IsNullOrWhiteSpace($dbName) -or
    [string]::IsNullOrWhiteSpace($dbUser) -or
    [string]::IsNullOrWhiteSpace($dbPasswordPlain)) {
    throw "Todos os campos DB_* obrigatorios precisam ser preenchidos."
}

Set-VercelEnv -Name "DB_HOST" -Value $dbHost -ScopeValue $Scope
Set-VercelEnv -Name "DB_PORT" -Value $dbPort -ScopeValue $Scope
Set-VercelEnv -Name "DB_NAME" -Value $dbName -ScopeValue $Scope
Set-VercelEnv -Name "DB_USER" -Value $dbUser -ScopeValue $Scope
Set-VercelEnv -Name "DB_PASSWORD" -Value $dbPasswordPlain -ScopeValue $Scope
Set-VercelEnv -Name "DB_SSLMODE" -Value $dbSslMode -ScopeValue $Scope

if ($SetDatabaseUrl) {
    $escapedUser = [System.Uri]::EscapeDataString($dbUser)
    $escapedPass = [System.Uri]::EscapeDataString($dbPasswordPlain)
    $databaseUrl = "postgresql://${escapedUser}:${escapedPass}@${dbHost}:${dbPort}/${dbName}?sslmode=${dbSslMode}"
    Set-VercelEnv -Name "DATABASE_URL" -Value $databaseUrl -ScopeValue $Scope
}

Write-Host ""
Write-Host "Variaveis configuradas com sucesso." -ForegroundColor Green

if ($Deploy) {
    Write-Host "Iniciando deploy de producao..." -ForegroundColor Cyan
    vercel deploy --prod -y --scope $Scope | Out-Host
}
