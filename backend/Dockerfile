FROM python:3.10-slim

WORKDIR /app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopiowanie plików zależności
COPY requirements.txt .

# Instalacja zależności Pythona
RUN pip install --no-cache-dir -r requirements.txt

# (Opcjonalnie) instalacja modelu spaCy dla PL wymagane przez FactExtractor
# Jeśli pobranie się nie powiedzie (np. brak sieci), pozostanie heurystyczny fallback
RUN python -m spacy download pl_core_news_sm || true

# Kopiowanie kodu aplikacji
COPY . .

# Ekspozycja portu
EXPOSE 8000

# Uruchomienie aplikacji
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
