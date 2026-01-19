FROM python:3.11-slim

WORKDIR /app

# Dépendances système (ajouter libGL pour OpenCV)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Installer numpy en premier (requis par rt-utils) avec timeout augmenté
RUN pip install --no-cache-dir --timeout=300 numpy==1.24.3

# Copier requirements et installer avec timeout
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# Copier application
COPY app.py .

# Port
EXPOSE 5000

# Lancer avec gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "app:app"]
