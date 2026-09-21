<#
.SYNOPSIS
    Publica os PDFs de output/ como assets de um GitHub Release, na
    organização (repo `production`, ver CLAUDE.md — nunca no fork pessoal).

.DESCRIPTION
    Versão simplificada da equivalente no folheto-ifem: aquele script lida
    com centenas de PDFs (lotes, retomada, limite de linha de comando do
    Windows). Aqui são só os pilotos (Campinas, Montes Claros) — sem essa
    complexidade por enquanto. Se este tema um dia virar nacional (todas as
    cidades acima de 80 mil habitantes), copiar a lógica de lote de
    `dadosfnp/folheto-ifem/tools/publicar_release.ps1`.

.EXAMPLE
    .\tools\publicar_release.ps1 -Tag v1 -Titulo "Folhetos Mobilidade — piloto"
    .\tools\publicar_release.ps1 -Tag v1 -Retomar
#>
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Titulo = "Folhetos Mobilidade",
    [string]$Notas = "",
    [string]$Repo = "dadosfnp/folheto-mobilidade",
    [switch]$Retomar,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$raiz = Split-Path $PSScriptRoot -Parent

function Parar($msg) {
    Write-Host $msg -ForegroundColor Red
    exit 1
}

$pdfs = Get-ChildItem (Join-Path $raiz "output") -Filter "FolhetoMobilidade_*.pdf" -File
if ($pdfs.Count -eq 0) { Parar "Nenhum PDF em output/ (rode python python/gerar.py primeiro)." }

$totalMB = [math]::Round(($pdfs | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Host "Release: $Tag  |  repo: $Repo  |  $($pdfs.Count) PDF(s)  |  $totalMB MB"

gh release view $Tag --repo $Repo *> $null
$existe = ($LASTEXITCODE -eq 0)

if ($existe -and -not $Retomar) {
    Parar "Release '$Tag' ja existe em $Repo. Use -Retomar para completar o upload, ou escolha outra tag."
}

if ($DryRun) {
    Write-Host "`n[dry-run] criaria/atualizaria o release '$Tag' em $Repo com $($pdfs.Count) arquivo(s):"
    $pdfs | ForEach-Object { Write-Host "  - $($_.Name)" }
    exit 0
}

if (-not $existe) {
    Write-Host "`nCriando o release..."
    $notasFinal = if ([string]::IsNullOrWhiteSpace($Notas)) { "Folhetos de Segurança Viária — dado piloto." } else { $Notas }
    gh release create $Tag --repo $Repo --title $Titulo --notes $notasFinal
    if ($LASTEXITCODE -ne 0) { Parar "Falha ao criar o release." }
}

Write-Host "`nSubindo $($pdfs.Count) arquivo(s)..."
$caminhos = $pdfs | ForEach-Object { $_.FullName }
gh release upload $Tag @caminhos --repo $Repo --clobber

if ($LASTEXITCODE -ne 0) {
    Parar "Falha no upload. Rode de novo com -Retomar."
}

Write-Host "`nRelease publicado: https://github.com/$Repo/releases/tag/$Tag"
Write-Host "Proximo passo: python tools/build_site.py --release-tag $Tag"
