FROM node:22-alpine@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2 AS build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

FROM nginx:1.30.3-alpine3.23@sha256:0d3b80406a13a767339fbe2f41406d6c7da727ab89cf8fae399e81f780f814d1

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=nginx:nginx --from=build /app/dist /usr/share/nginx/html
COPY --chown=nginx:nginx submission-assets/contest-video-v3/video/ecogenesis-v2-scientific-walkthrough-en-subs.mp4 /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v3/video/ecogenesis-v2-scientific-walkthrough-en.srt /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v3/video/ecogenesis-v2-scientific-walkthrough-voiceover-en.txt /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v3/video/ecogenesis-v2-scientific-walkthrough-thumbnail.png /usr/share/nginx/html/submission-video/

RUN sed -i 's|pid        /run/nginx.pid;|pid        /tmp/nginx.pid;|' /etc/nginx/nginx.conf \
    && mkdir -p /var/cache/nginx \
    && chown -R nginx:nginx /var/cache/nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
