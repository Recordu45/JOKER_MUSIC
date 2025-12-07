# Use Python 3.10.12 official slim image
FROM python:3.10.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# system deps (ffmpeg + nodejs)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     ca-certificates \
     curl \
     ffmpeg \
     git \
     build-essential \
  && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && npm install -g npm@latest \
  && rm -rf /var/lib/apt/lists/*

# app dir
WORKDIR /app

# copy only requirements first to use docker cache
COPY requirements.txt /app/requirements.txt

# pip install
RUN pip install --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r /app/requirements.txt

# copy source
COPY . /app

# create non-root user and give ownership
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# default command (if your entrypoint is main.py)
CMD ["python3", "main.py"]
