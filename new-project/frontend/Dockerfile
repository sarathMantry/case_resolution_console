# FROM node:20-alpine AS builder
# WORKDIR /app
# COPY package.json package-lock.json* ./
# RUN npm ci --silent || npm install --no-audit --no-fund
# COPY . .
# RUN npm run build

# FROM node:20-alpine AS runner
# WORKDIR /appn
# ENV NODE_ENV=production
# # lightweight static server
# RUN npm install -g serve@14
# COPY --from=builder /app/dist /app/dist
# EXPOSE 5173
# CMD ["serve", "-s", "dist", "-l", "5173"]
# FROM node:20-alpine AS builder
# WORKDIR /app
# COPY package*.json ./
# RUN npm install --no-audit --no-fund
# COPY . .
# RUN npm install -D tailwindcss postcss autoprefixer && \
#     npm run build

# FROM node:20-alpine AS runner
# WORKDIR /app
# ENV NODE_ENV=production
# RUN npm install -g serve@14
# COPY --from=builder /app/dist /app/dist
# EXPOSE 5173
# CMD ["serve", "-s", "dist", "-l", "5173"]
FROM node:20-alpine
WORKDIR /app

# Install dependencies for both production and development
COPY package*.json ./
RUN npm install --no-audit --no-fund && \
    npm install -D vite @vitejs/plugin-react tailwindcss postcss autoprefixer

# Copy application files
COPY . .

# Development mode by default
ENV NODE_ENV=development

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host"]