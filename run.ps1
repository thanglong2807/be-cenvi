# PowerShell script để chạy Cenvi Backend
Write-Host "🚀 Starting Cenvi Backend with MySQL..." -ForegroundColor Green

# Dừng containers cũ
Write-Host "📦 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down -v

# Build và khởi động mới
Write-Host "🔨 Building and starting containers..." -ForegroundColor Yellow
docker-compose up --build -d

# Đợi MySQL khởi động
Write-Host "⏳ Waiting for MySQL to start..." -ForegroundColor Yellow
Start-Sleep 10

# Test kết nối MySQL
Write-Host "🔍 Testing MySQL connection..." -ForegroundColor Yellow
$mysqlTest = docker exec -it cenvi_mysql mysql -u cenvi_user -pcenvi_pass_2024 -e "SHOW DATABASES;" 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ MySQL connection successful!" -ForegroundColor Green
} else {
    Write-Host "❌ MySQL connection failed!" -ForegroundColor Red
}

# Hiển thị logs
Write-Host "📋 Showing server logs..." -ForegroundColor Yellow
docker-compose logs -f server
