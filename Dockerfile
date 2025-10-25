# PDF Hunter - Multi-stage Docker build
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Playwright)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY package.json package-lock.json ./
COPY README.md ./

# Install Python dependencies (main + api group for FastAPI)
# Dev group excluded (Jupyter, IPython kernel not needed in production)
RUN uv sync --frozen --group api

# Install peepdf-3 without dependencies to avoid stpyv8 (optional dependency not needed)
# We only use 'peepdf -f' (force parsing mode) which doesn't execute JavaScript
RUN /root/.local/bin/uv pip install --system --no-deps peepdf-3==5.1.1

# Install Node.js dependencies
RUN npm ci

# Install Playwright browsers
RUN npx playwright install chromium --with-deps

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/output /app/logs /app/input

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/app/output
ENV LOG_DIR=/app/logs

# Expose port for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run FastAPI server
CMD ["uv", "run", "python", "-m", "pdf_hunter.api.server"]
