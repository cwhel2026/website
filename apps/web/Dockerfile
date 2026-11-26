# Fail fast: Root Directory apps/web must not build this file for production.
# Railway → Build → Dockerfile path: apps/combined/Dockerfile (repository root).
# Local web-only build: docker build -f apps/web/Dockerfile.web-only apps/web

FROM alpine:3.20
RUN echo "Wrong Dockerfile for production. Set Railway Dockerfile path to apps/combined/Dockerfile — see RAILWAY_LOGIN_FIX.md" >&2 && exit 1