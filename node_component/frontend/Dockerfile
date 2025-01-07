# ---------- Development Stage ----------
FROM node:20 AS dev

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the source code
COPY . .

# Start Vite development server
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---------- Production Stage ----------
FROM node:20 AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the source code
COPY . .

# Build the project
RUN npm run build

# ---------- Serve Stage ----------
FROM nginx:stable-alpine AS serve

# Copy built static files from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Use a custom NGINX config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]
