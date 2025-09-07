# services/ai-core/Dockerfile

FROM python:3.11-slim
WORKDIR /app

# Install git and other system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# services/ai-core/Dockerfile

FROM python:3.11-slim
WORKDIR /app

# NEW: Install git so we can clone repositories
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install PyTorch with CPU support first
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
