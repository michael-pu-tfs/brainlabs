# # Use a newer Node.js version (18 or 20)
# FROM node:20-alpine AS builder

# WORKDIR /app

# # Copy package files and install dependencies
# COPY package.json package-lock.json ./
# RUN npm install

# # Copy the rest of the project
# COPY . .

# # TypeScript resolution check (optional)
# RUN npx tsc --noEmit --traceResolution || echo "TypeScript resolution errors occurred"

# # Run the build process
# RUN npm run build

# # Use Nginx to serve the static files
# FROM nginx:alpine

# # Copy the built files to Nginx
# COPY --from=builder /app/dist /usr/share/nginx/html
# # COPY --from=builder /app/dist /usr/share/nginx/html

# # Copy custom Nginx configuration
# COPY nginx.conf /etc/nginx/nginx.conf

# EXPOSE 8080

# CMD ["nginx", "-g", "daemon off;"]


# Use a newer Node.js version (20)
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install --frozen-lockfile

# Copy the rest of the project
COPY . .

# TypeScript resolution check (optional)
RUN npx tsc --noEmit --traceResolution || echo "TypeScript resolution errors occurred"

# Run the build process
RUN npm run build

# Use Nginx to serve the static files
FROM nginx:alpine

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy the built files to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Set permissions (avoid permission errors in Cloud Run)
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]

