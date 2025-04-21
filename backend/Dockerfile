# Use an official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (node + npx needed for MCP stdio tools)
RUN apt-get update && \
    apt-get install -y curl gnupg lsb-release ca-certificates apt-transport-https docker.io && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest && \
    rm -rf /var/lib/apt/lists/*


# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the app port
EXPOSE 8000

# Set HuggingFace cache path
ENV HF_HOME=/app/.cache/huggingface

# Pre-download the model and cache it
RUN mkdir -p $HF_HOME && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Run FastAPI via Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
