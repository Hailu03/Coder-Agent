FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json .
RUN npm install --legacy-peer-deps

# For development, we stop here
# In production build, we would continue with the steps below
# Copy the rest of the application
# COPY . .

# Build the application
# RUN npm run build

# Production stage - only used when target is not specified
FROM nginx:alpine

# Copy the build from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]