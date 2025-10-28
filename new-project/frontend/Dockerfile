FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --silent || npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /appn
ENV NODE_ENV=production
# lightweight static server
RUN npm install -g serve@14
COPY --from=builder /app/dist /app/dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]