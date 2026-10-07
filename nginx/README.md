# backendCGI

Docker Image: Nginx server with Shell script CGI integrated

## Download:

```git clone <this repo>.git```

## Build:
```bash
	cd nginxcgi
	docker build . --no-cache -t omnileads/nginxcgi
```
---

## Run:
podman run --name oml-qa-nginx -p 8081:80 omnileads/nginxcgi:latest

## Contents

* ```Dockerfile```:  describe the Docker image
* ```reset_tables_script.cgi```: reset de tablas de logs en Postgres **y** stats Redis DB2
  (`OML:CALLDATA:*`, `OML:DISPOSITIONDATA:*`, `OML:WHATSAPP:CAMP:*` — mismo efecto que
  `reiniciar_estadisticas_calldata`). Requiere `REDIS_HOSTNAME` / `REDIS_PORT` en el
  contenedor y redis-cli (paquete `redis` en la imagen).
* ```generate_inbounds.cgi```: It's the web page to load in the path **/shell**
* ```default.conf```: nginx config
* ```init```: aux shellscript
* ```main.html```: index web page
