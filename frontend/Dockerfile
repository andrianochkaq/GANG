# Development image for the Vite dev server.
FROM node:20-alpine

WORKDIR /app
RUN chown node:node /app
USER node

COPY --chown=node:node package.json package-lock.json ./
# npm ci fails while package-lock.json lacks the lint tools added by
# FC-005; npm install then fills the gap. Use plain npm ci once the lock
# file is regenerated.
RUN npm ci || npm install

COPY --chown=node:node . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
