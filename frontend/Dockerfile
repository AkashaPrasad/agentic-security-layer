# ==============================================================================
# Frontend — React / Vite → Nginx
# Stage 1: build   Stage 2: serve
# ==============================================================================

# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_API_URL is baked into the JS bundle at build time.
# On Railway set this to: https://<your-backend>.up.railway.app/api/v1
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build          # outputs to /app/dist


# ── Stage 2: Serve with Nginx ────────────────────────────────────────────────
FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf

# Copy template — PORT is substituted at container startup
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

# Railway injects $PORT; falls back to 80 for local use
EXPOSE 80

# envsubst '$PORT' only replaces $PORT — leaves nginx vars ($uri etc) untouched
CMD ["/bin/sh", "-c", "envsubst '$PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
