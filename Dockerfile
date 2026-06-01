FROM python:3.12.5-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# Đặt thư mục browser ở nơi appuser có thể truy cập
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Cài Chromium cùng toàn bộ system deps cần thiết (chạy khi còn là root)
RUN playwright install --with-deps chromium && chmod -R 755 /ms-playwright

COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/credentials /app/app/data /app/logs /app/static

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]