FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
COPY submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en-subs.mp4 /usr/share/nginx/html/submission-video/
COPY submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-en.srt /usr/share/nginx/html/submission-video/
COPY submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-english-voiceover.txt /usr/share/nginx/html/submission-video/
COPY submission-assets/contest-video-v2/video/ecogenesis-gbif-contest-demo-transcript.md /usr/share/nginx/html/submission-video/
COPY submission-assets/contest-video-v2/video/demo-thumbnail-contest-en.png /usr/share/nginx/html/submission-video/

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
