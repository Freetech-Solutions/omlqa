## Levantar el webphone client demo

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