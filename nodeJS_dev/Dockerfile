FROM node:18-alpine as vuejs

RUN apk add --no-cache python3 make g++ && \
    npm install -g npm@latest && \
    npm set strict-ssl false && \
    npm set registry https://registry.npmjs.org/ && \
    export NODE_OPTIONS=--openssl-legacy-provider && \
    npm ci --no-progress && \
