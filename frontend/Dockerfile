FROM node:25-alpine@sha256:bdf2cca6fe3dabd014ea60163eca3f0f7015fbd5c7ee1b0e9ccb4ced6eb02ef4 AS build

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
COPY --chown=nginx:nginx submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en-subs.mp4 /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en.srt /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-english-voiceover.txt /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-transcript.md /usr/share/nginx/html/submission-video/
COPY --chown=nginx:nginx submission-assets/contest-video-v2/video/demo-thumbnail-contest-en.png /usr/share/nginx/html/submission-video/

RUN sed -i 's|pid        /run/nginx.pid;|pid        /tmp/nginx.pid;|' /etc/nginx/nginx.conf \
    && mkdir -p /var/cache/nginx \
    && chown -R nginx:nginx /var/cache/nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
