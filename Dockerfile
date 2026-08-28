FROM python:3.12-slim

# Install Deno for yt-dlp YouTube JavaScript challenges
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip ffmpeg \
    && curl -fsSL https://deno.land/install.sh | sh \
    && mv /root/.deno/bin/deno /usr/local/bin/deno \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
