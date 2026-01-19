FROM nginx:alpine

# Copy static files to nginx
COPY . /usr/share/nginx/html

# Copy nginx config template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Set default port
ENV PORT=80

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
