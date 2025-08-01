FROM python:3.10-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg2 \
    chromium-driver chromium && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Define variáveis de ambiente
ENV CHROME_BIN=/usr/bin/chromium \
    PATH=$PATH:/usr/lib/chromium

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando padrão
CMD ["python", "blog.py"]
