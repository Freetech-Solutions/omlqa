#!/bin/sh

# Iniciar spawn-fcgi
spawn-fcgi -s /var/run/fcgiwrap.socket /usr/bin/fcgiwrap 

chmod 777 /var/run/fcgiwrap.socket

# Iniciar nginx en primer plano
nginx -g 'daemon off;'
