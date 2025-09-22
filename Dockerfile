# Multi-stage Dockerfile for Telegram Multi-Account Message Sender

# Build stage
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY . .

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 telegram-sender

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/telegram-sender/.local

# Copy application code
COPY --chown=telegram-sender:telegram-sender . .

# Create app data directory
RUN mkdir -p /app/app_data/sessions /app/app_data/logs /app/content && \
    chown -R telegram-sender:telegram-sender /app

# Switch to non-root user
USER telegram-sender

# Set environment variables
ENV PATH="/home/telegram-sender/.local/bin:${PATH}"
ENV PYTHONPATH="/app"
ENV QT_QPA_PLATFORM=offscreen

# Expose port (if needed for web interface)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import app; print('OK')" || exit 1

# Default command
CMD ["python", "main.py"]
