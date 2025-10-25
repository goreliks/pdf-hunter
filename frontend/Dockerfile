# Multi-stage build for PDF Hunter Frontend
# Stage 1: Build the React application
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Set API base URL for production (uses Nginx proxy)
ENV VITE_API_BASE_URL=/api

# Build the application
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy dev mode mock data for frontend development
COPY --from=builder /app/dev /usr/share/nginx/html/dev

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
