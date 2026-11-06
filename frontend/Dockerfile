# ---- build stage ----
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com \
  && npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- run stage ----
FROM nginx:1.27-alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/nginx.conf

RUN addgroup -S app && adduser -S app -G app \
  && chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/log/nginx \
  && touch /var/run/nginx.pid \
  && chown app:app /var/run/nginx.pid

USER app
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
