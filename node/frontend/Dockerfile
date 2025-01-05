# Base image for building the frontend
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

# Base image for serving the frontend
FROM nginx:stable-alpine AS serve

# Copy built static files from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]
