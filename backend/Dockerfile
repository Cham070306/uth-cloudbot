# ── Build stage ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Cài dependencies vào prefix riêng để copy sang stage sau
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────
FROM python:3.12-slim

# Tạo user non-root để chạy app (bảo mật Cloud Run)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy dependencies đã cài từ build stage
COPY --from=builder /install /usr/local

# Copy toàn bộ source backend
COPY . .

# Đổi owner cho appuser
RUN chown -R appuser:appgroup /app

USER appuser

# Cloud Run sẽ inject PORT, app đọc từ env (đã có trong config.py)
ENV PORT=8080
EXPOSE 8080

# Dùng gunicorn cho production (thêm vào requirements nếu chưa có)
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]