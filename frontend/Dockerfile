FROM python:3.11-alpine

WORKDIR /app

# Copy static files
COPY . .

# Set default port
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run simple Python HTTP server
CMD python -m http.server $PORT
