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

# Copie os arquivos do projeto
COPY . . 

# Instale as dependências Python
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

# Exponha a porta para o Flask
EXPOSE 5000

# Defina o comando padrão
CMD ["python", "api-processor/main.py"]
