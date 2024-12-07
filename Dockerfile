# Use uma imagem Python slim
FROM python:3.10-slim-buster

# Atualize o sistema e instale dependências do sistema operacional
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    gfortran \
    libatlas-base-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Atualize pip, setuptools e wheel
RUN pip install --upgrade pip setuptools wheel

# Defina o diretório de trabalho no container
WORKDIR /app

# Copie os arquivos do projeto para o diretório de trabalho
COPY . /app

# Instale as dependências Python
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

# Exponha a porta onde o app será executado
EXPOSE 5000

# Defina a variável de ambiente para forçar uso de CPU com TensorFlow
ENV TF_FORCE_CPU=true

# Use Gunicorn como servidor WSGI para produção
RUN pip install gunicorn

# Defina o comando padrão para rodar o Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api-processor.main:app"]
