param(
    [string]$DockerUser = "thanglong2807",
    [string]$ImageName = "be-cenvi",
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

$image = "$DockerUser/$ImageName`:$Tag"

Write-Host "[1/3] Building image: $image" -ForegroundColor Cyan
docker build -t $image .

Write-Host "[2/3] Pushing image: $image" -ForegroundColor Cyan
docker push $image

Write-Host "[3/3] Done. Published: $image" -ForegroundColor Green