# OMniLeads QA

## Getting started

En este repositorio contamos con dos componentes implicados en las acciones de QA:

* Nginx CGI: para servir algunas acciones que selenium necesita disparar sobre el entorno.
* PSTN emulator: para simular la interaccion con la PSTN en todos los tipos de llamadas que comprueban los tests.

## Ejecutar entorno

Antes de levantar el stack ,debemos asegurarnos de que ya tenemos corriendo OMniLeads desde su docker-compose con su entorno de pruebas arriba (oml_manage --init_env). 
Si así es entonces podemos lanzar:

```
docker run -d \
  --name oml-nginx-cgi \
  --hostname nginxcgi \
  --dns 8.8.8.8 \
  -e PGHOST=${PGHOST} \
  -e PGPASSWORD=${PGPASSWORD} \
  -e PSTN_HOSTNAME=${PSTN_HOSTNAME} \
  --network oml_omnileads \
  -p 8888:8888 \
  --privileged \
  --restart on-failure \
  --stop-timeout 90 \
  -i -t \
  omnileads/nginxqa:latest
```

Si deseas usar docker-compose:

```
docker-compose up -d
```

Para comprobar se puede ingresar al puerto 8888 y probar las opciones. Es más interesante si lo hacemos contando con un usuario logueado como agente.

## Build

Run:

```
docker buildx build --file=Dockerfile --tag=$REPOSITORY/nginxqa:$TAG --target=run .
```

### Pstn Emulator

Este componente nos permite simular una troncal SIP de proveedor de terminación telefónica, de manera tal que la instancia de OMniLeads podrá ser testeada en su totalidad pudiendo enviar y recibir llamadas.

Tanto en el DevEnv como en el Docker-Compose nuestro componente es lanzado como container por el docker-compose.yml de cada escenario. Ademas se cuenta con el comando de inicialización de entorno que al ser invocado entre otras cosas, deja establecido un trunk entre OML y PSTN-Emulator listo para comenzar a cursar llamadas.

Para construir la imagen del pstn_emulator:

```
cd pstn_emulator
docker build --tag=your_tag .
```

Docker run:

docker run \
  -p 6060:6060/udp \
  -p 10000-10020:10000-10020/udp \
  --network=host \
  docker.io/omnileads/pstn_emulator:latest


podman run \
  -p 6060:6060/udp \
  -p 10000-10020:10000-10020/udp \
  --network=host \
  docker.io/omnileads/pstn_emulator:latest


### Nginx CGI scripts

Este container implementa CGI para poder disparar algunas acciones sobre la instancia de OMniLeads a partir de solicitudes HTTP. Principalmente utilizado por Selenium IDE.


Para construir la imagen de Nginx cgi:

```
cd nginxcgi
docker build --tag=your_tag .
```


### WebRTC phone & video caller 

Para lanzar un cliente que consume la canalidad de video permitiendo generar video-llamadas hacia OMniLeads, se debe invocar el comando:

```
docker run \
  --name=oml-videocalls-widget \
  --dns=8.8.8.8 \
  --env=CLIENT_USERNAME=your_omnileads_username \
  --env=CLIENT_PASSWORD=your_omnileads_user_password \
  --env=KAMAILIO_HOST=localhost \
  --env=OML_HOST=omnileads_hostname.com \
  --env=WEBSOCKET_PORT=443 \
  --publish=8889:5000 \
  --privileged \
  --restart=on-failure \
  --tty \
  docker.io/omnileads/videocalls_widget:240224.01
```

Se debe considerar que si estamos frente a una instancia AIO el valor de KAMAILIO_HOST debe ser "localhost", mientras que si la instancia es del tipo cluster el valor de KAMAILIO_HOST debe ser igual a la dirección IP privada de la instancia APP del cluster.

Una vez que el contenedor es lanzado sin errores, se accede a la dirección del host donde fue lanzado: https://host_video_calls.com y desde allí puede lanzar llamadas de video utilizando el botón correspondiente. Esta acción va a lanzar una llamada hacia la instancia de OMniLeads configurada "OML_HOST", puntualmente sobre el DID: 01177660011, por lo que deberá contar con un DID con ese número apuntando a una campaña entrante con la canalidad de video habilitada. 


Para construir la imagen de WebRTC video caller:

```
cd web_video_calls
docker build --tag=your_tag .
```
