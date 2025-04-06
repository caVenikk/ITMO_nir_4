FROM ubuntu:22.04

# Устанавливаем базовые пакеты и Python
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

# Устанавливаем Go
RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz && \
    rm go1.21.5.linux-amd64.tar.gz

# Добавляем Go в PATH
ENV PATH=$PATH:/usr/local/go/bin

# Создаем рабочую директорию
WORKDIR /app

# Предустанавливаем стандартные анализаторы
RUN pip3 install ruff black flake8

# Копируем файлы приложения
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Компилируем Go-сборщик метрик при сборке образа
RUN go build -o metrics_collector metrics_collector.go

# Создаем директории для данных
RUN mkdir -p /app/data/repos /app/data/metrics

# Запускаем FastAPI приложение
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]