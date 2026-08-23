param(
    [ValidateSet("postgresql", "oracle", "all")]
    [string]$Target = "all",
    [switch]$CheckOnly,
    [switch]$SkipRuntimeGrants
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    (Join-Path $PSScriptRoot "setup_rtims_databases.py"),
    "--target",
    $Target,
    "--env-file",
    (Join-Path $projectRoot ".env")
)

if (-not $CheckOnly) {
    $arguments += "--apply"
}

if ($SkipRuntimeGrants) {
    $arguments += "--skip-runtime-grants"
}

& python @arguments
exit $LASTEXITCODE
