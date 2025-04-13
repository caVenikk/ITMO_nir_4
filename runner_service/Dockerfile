FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    build-essential \
    time \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && \
    rm go1.21.5.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin

WORKDIR /app

RUN pip3 install ruff black flake8

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN go build -o metrics_collector metrics_collector.go

RUN mkdir -p /app/data/repos /app/data/metrics

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]