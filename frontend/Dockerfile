FROM node:18-alpine

WORKDIR /app

# Copier package.json et yarn.lock
COPY package.json package.json
COPY yarn.lock yarn.lock

# Installer les dépendances
RUN yarn install

# Copier le projet
COPY . .

# Build
RUN yarn build

# Servir avec Vite en mode preview
EXPOSE 5173

HEALTHCHECK --interval=15s --timeout=10s --retries=5 \
    CMD wget -q -O- http://localhost:5173/ || exit 1

CMD ["yarn", "dev", "--host"]
