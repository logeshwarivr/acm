FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create __init__.py files
RUN touch backend/__init__.py \
    backend/physics/__init__.py \
    backend/api/__init__.py \
    backend/models/__init__.py

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]