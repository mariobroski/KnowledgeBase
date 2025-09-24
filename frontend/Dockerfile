FROM node:16-alpine

WORKDIR /app

# Kopiowanie plików zależności
COPY package.json package-lock.json* ./

# Instalacja zależności
RUN npm install

# Kopiowanie kodu aplikacji
COPY . .

# Ekspozycja portu
EXPOSE 3000

# Uruchomienie aplikacji
CMD ["npm", "start"]