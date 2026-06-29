# Music Watermark Bot — Docker image
FROM python:3.11-slim

# Install ffmpeg (system dependency, not available via pip)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Render (and most PaaS) inject PORT at runtime; 8080 is the local default
ENV PORT=8080
ENV PYTHONPATH=/app
EXPOSE 8080

# Make sure temp dir exists at container start
RUN mkdir -p temp

# -u = unbuffered stdout/stderr so Render shows logs in real time
CMD ["python", "-u", "main.py"]
