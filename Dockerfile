# Minimal Dockerfile for the Eye Timer Flask app
FROM ghcr.io/astral-sh/uv:debian

# Create app directory
# Workdir and copy app files
WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --locked --no-dev

# Copy app source
COPY favicon.png ./favicon.png
COPY eye-timer.py ./

# Expose port
EXPOSE 5000

# Default environment
ENV HOST=0.0.0.0
ENV PORT=5000
# Ensure user-local bin is on PATH so uv (installed there) is available
ENV PATH="/root/.local/bin:${PATH}"

# Use uv to run the app (matches local development: `uv run eye-timer.py`)
CMD ["uv", "run", "eye-timer.py"]
