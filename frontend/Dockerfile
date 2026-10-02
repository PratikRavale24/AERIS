# AERIS Frontend — Multi-stage build
# Stage 1: Build
FROM node:20.12-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

COPY . .
RUN npm run build

# Stage 2: Serve via nginx (production)
# In development, we serve via Vite dev server
# For production, static files are copied to the nginx container
FROM nginxinc/nginx-unprivileged:1.25.4-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
