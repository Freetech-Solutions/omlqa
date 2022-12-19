# PSTN EMULATOR

Este componente nos permite emular llamadas salientes y entrantes. 

## Build

```
docker build --tag=omnileads/pstn_emulator:dev .
```

## Softphone de testing

Se puede trabajar con un softphone IAX2 tanto para generar llamadas con destino en OMniLeads (llamadas entrantes), asi como tambien recibir llamadas salientes desde OMniLeads. 

```
Softphone ----> Emulator ----> OMniLeads
OMniLeads ----> Emulator ----> Softphone
```

Para registrar el softphone se debe configurar los parametros:

```
username: 1234567
password: omnileads
port: 4569
hostname: localhost or your_host_ip
```

Con respecto al URL de registracion se debe considerar si se va a registrar desde un softphone ejecutado en un smartphone o desde uno corriendo en su workstation. En el primer caso debera utilizar la direccion de la workstation donde corre el emulador, en el segundo caso puede utilizar localhost.

## Llamadas salientes:

Dependiendo de la variable de entorno "INBOUND_CALL_MODE" cada llamada recibida sera procesada de acuerdo a:

- **default**: se atienden el 100% de las llamadas.
- **dial2softphone**: se mandan el 100% de las llamadas hacia el softphone de testing.
- **ans_busy**: se atienden el 50% de las llamadas, mientras que se devuelve BUSY al otro 50%.
- **ans_busy_congestion_noans**: se atienden el 25% de las llamadas, mientras que el otro 25% da BUSY, 25% CONGESTION y 25 NO ANSWER.
- **advanced**: en esta modalidad se procesan las llamadas de acuerdo a digito final:

Si termina en:

* 0: BUSY
* 2: Atiende una llamada de 15 segundos.
* 3: Espera 35 segundos y luego atiende una llamada de 100 segundos.
* 5: NO ANSWER
* 7: Atiende una llamada de 27 segundos.
* 9: CONGESTION

En el modo default puede marcar al 1234567 para que se envie la llamada hacia el Softphone.

## Llamadas entrantes:

Se pueden generar llamadas entrantes hacia OMniLeads utilizando el softphone IAX2 o bien generando desde la linea de comandos. 

* **Llamadas desde el softphone**: puede marcar a los numeros 01177660010 al 01177660019. Esos numeros van a ser enviados a OMniLeads, donde debera configurar pertinenmente sus rutas entrantes. 

* **Llamadas de la terminal**: lanzando el comando citado a continuacion, va a generar una llamada entrante hacia el DID 01177660010 de OMniLeads.

```
docker exec -it oml-pstn-emulator sipp -sn uac pbxemulator:5070 -s test -m 1 -r 1 -d 60000 -l 1
```

## Deploy

### Docker network host:

```
docker run \
  --name pstn_emulator \
  --net=host \
  --env INBOUND_CALL_MODE=default \
  omnileads/pstn_emulator:$VERSION
```

### Docker network bridge:

```
docker network create \
  --subnet=10.12.12.0/24 \
  pstn_emulator
```

```
docker run \
  --name pstn_emulator \
  --net pstn_emulator \
  --ip 10.12.12.99 \
  --env INBOUND_CALL_MODE=default \
  -p 5060:5060/udp  \
  -p 4569:4569/udp  \
  omnileads/pstn_emulator:$VERSION
```

```
iptables -t nat -A PREROUTING -p udp --dport 10000:20000 -j DNAT --to-destination 10.12.12.99
iptables -A FORWARD -p udp -d 10.12.12.99 --dport 10000:20000 -j ACCEPT
```

### Montar archivos .conf para trabajar con pruebas

```
docker run \
  --name pstn_emulator \
  --net=host \
  --env INBOUND_CALL_MODE=default \
  --env RTP_PORT_FROM=10000 \
  --env RTP_PORT_TO=20000 \
  --env SIP_EXTERNAL_ADDR=$YOUR_IPV4_OR_FQDN \
  --env SIP_EXTERNAL_PORT=$YOUR_PUBLIC_SIP_PORT \
  -v extensions.conf:/etc/asterisk/extensions.conf:ro \
  -v pjsip_wizard.conf:/etc/asterisk/pjsip_wizard.conf:ro \
  omnileads/pstn_emulator:$VERSION
```

## Environment variables

* RTP_PORT_FROM - Rango inferior de puertos RTP.
* RTP_PORT_TO - Rango superrior de puertos RTP.
* SIP_EXTERNAL_ADDR - IPADDR que se utiliza para advertir el NAT de los paquetes SIP que salgan hacia el exterior.
* SIP_EXTERNAL_PORT - Puerto UDP que se utiliza para advertir el NAT de los paquetes SIP que salgan hacia el exterior.
  