FROM nginx:alpine

# Copy static files to nginx
COPY . /usr/share/nginx/html

# Copy nginx config (overwrite default)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
