FROM nginx:stable-alpine3.17 as run

# Instala el paquete fcgiwrap para soportar CGI en Nginx
RUN apk add --no-cache fcgiwrap spawn-fcgi sipp postgresql-client

# Copia la configuración de Nginx y el script CGI
COPY nginx.conf /etc/nginx/nginx.conf
COPY scripts_cgi/shell scripts_cgi/generate_inbounds.cgi scripts_cgi/reset_tables_script.cgi /usr/share/nginx/html/
COPY index.html /usr/share/nginx/html/

COPY docker-entrypoint.sh /

# Dar permisos de ejecución al script
RUN chmod +x /usr/share/nginx/html/shell /usr/share/nginx/html/generate_inbounds.cgi /usr/share/nginx/html/reset_tables_script.cgi

# Comando para ejecutar spawn-fcgi y nginx
CMD ["/docker-entrypoint.sh"]
