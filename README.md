# OMniLeads QA

## Getting started

En este repositorio contamos con dos componentes implicados en las acciones de QA:

### PSTN-Emulator

Este componente nos permite simular una troncal SIP de proveedor de terminación telefónica, de manera tal que la instancia de OMniLeads podrá ser testeada en su totalidad pudiendo enviar y recibir llamadas.

Tanto en el DevEnv como en el Docker-Compose nuestro componente es lanzado como container por el docker-compose.yml de cada escenario. Ademas se cuenta con el comando de inicialización de entorno que al ser invocado entre otras cosas, deja establecido un trunk entre OML y PSTN-Emulator listo para comenzar a cursar llamadas.

#### Build

Para construir la imagen:

```
cd pstn_emulator
docker build --tag=your_tag .
```

### Nginx CGI scripts

Este container implementa CGI para poder disparar algunas acciones sobre la instancia de OMniLeads a partir de solicitudes HTTP. Principalmente utilizado por Selenium IDE.

#### Build & Run

Para construir la imagen ejecutar:

```
cd nginxcgi
docker build --tag=your_tag .
```

Para lanzar el container, debemos asegurar que exista una instancia de OMniLeads lanzada desde el docker-compose para luego lanzar el container Nginc CGI.

```
cd nginxcgi
docker-compose up -d
```
