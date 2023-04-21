# OMniLeads QA

## Getting started

En este repositorio contamos con dos componentes implicados en las acciones de QA:

## Ejecutar entorno

Antes de levantar el stack ,debemos asegurarnos de que ya tenemos corriendo OMniLeads desde su docker-compose con su entorno de pruebas arriba (oml_manage --init_env). 
Si así es entonces podemos lanzar:

```
docker-compose up -d
```

Para comprobar se puede ingresar al puerto 8081 y probar las opciones. Es más interesante si lo hacemos contando con un usuario logueado como agente.

## Build

### Pstn Emulator

Este componente nos permite simular una troncal SIP de proveedor de terminación telefónica, de manera tal que la instancia de OMniLeads podrá ser testeada en su totalidad pudiendo enviar y recibir llamadas.

Tanto en el DevEnv como en el Docker-Compose nuestro componente es lanzado como container por el docker-compose.yml de cada escenario. Ademas se cuenta con el comando de inicialización de entorno que al ser invocado entre otras cosas, deja establecido un trunk entre OML y PSTN-Emulator listo para comenzar a cursar llamadas.

Para construir la imagen del pstn_emulator:

```
cd pstn_emulator
docker build --tag=your_tag .
```

### Nginx CGI scripts

Este container implementa CGI para poder disparar algunas acciones sobre la instancia de OMniLeads a partir de solicitudes HTTP. Principalmente utilizado por Selenium IDE.


Para construir la imagen de Nginx cgi:

```
cd nginxcgi
docker build --tag=your_tag .
```

