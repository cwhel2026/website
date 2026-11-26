# Single Railway service: public site + FastAPI on one hostname.
# Build context must be the repository root.

FROM node:22-alpine AS webdeps
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS webbuild
WORKDIR /web
COPY --from=webdeps /web/node_modules ./node_modules
COPY apps/web .
ENV RAILWAY_COMBINED_BUILD=1
ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_GIT_COMMIT=unknown
ARG NEXT_PUBLIC_BUILD_TIME=
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_GIT_COMMIT=$NEXT_PUBLIC_GIT_COMMIT
ENV NEXT_PUBLIC_BUILD_TIME=$NEXT_PUBLIC_BUILD_TIME
RUN npm run build

FROM python:3.12-slim AS runner
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV API_INTERNAL_URL=http://127.0.0.1:8000
ENV RUN_EMBEDDED_API=1
ENV RMD_IMAGE_KIND=combined
ENV PYTHONPATH=/api

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /api/requirements.txt
RUN pip install --no-cache-dir -r /api/requirements.txt
COPY apps/api/app /api/app
COPY apps/api/scripts /api/scripts
COPY apps/api/alembic /api/alembic
COPY apps/api/alembic.ini /api/alembic.ini

COPY --from=webbuild /web/public ./public
COPY --from=webbuild /web/.next/standalone ./
COPY --from=webbuild /web/.next/static ./.next/static
COPY apps/combined/start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 3000
CMD ["/app/start.sh"]