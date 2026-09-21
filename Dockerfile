FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render injects PORT (10000 by default); fall back to 8000 for local runs.
# --proxy-headers is required so request.client.host is the real client IP
# behind Render's edge proxy, otherwise the rate limiter buckets every visitor
# under a single proxy address.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
