FROM node:20-alpine AS builder

WORKDIR /build

COPY codebase/frontend/package.json codebase/frontend/package-lock.json ./
RUN npm ci

COPY codebase/frontend/ ./
RUN npm run build

FROM nginx:alpine AS runtime

COPY --from=builder /build/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
