# Epic Games Multiplayer QA Toolkit
# Multi-stage Docker build for optimized image size

# Build stage
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements-base.txt .
COPY */requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --user -r requirements-base.txt && \
    for req in $(find . -name requirements.txt); do \
        pip install --user -r $req || true; \
    done

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat \
    tcpdump \
    iperf3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make Python packages available
ENV PATH=/root/.local/bin:$PATH

# Create results directory
RUN mkdir -p /app/results

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV QA_TOOLKIT_CONFIG=/app/config.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "quickstart.py"]

# Expose ports for various tools
# API Load Test Dashboard
EXPOSE 8080
# Packet Analyzer Web UI
EXPOSE 8081
# Chaos Testing Control Panel
EXPOSE 8082

# Volume for results
VOLUME ["/app/results"]

# Labels
LABEL maintainer="Epic Games QA Team"
LABEL version="1.0.0"
LABEL description="Comprehensive multiplayer game testing toolkit"