# Multi-stage build for backend
# Stage 1: builder
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: runtime
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ ./src/
COPY . .

# Default: run uvicorn when api main exists; otherwise placeholder
CMD ["python", "-c", "import sys; print('Backend ready'); sys.exit(0)"]
