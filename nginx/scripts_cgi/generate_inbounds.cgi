#!/bin/sh

# Define una función para enviar una respuesta HTML
send_response() {
  cat <<EOF
Content-type: text/html

<!DOCTYPE html>
<html>
<head>
  <title>Resultado</title>
</head>
<body>
  <h1>$1</h1>
  <p>$2</p>
  <a href="/">Regresar al inicio</a>
</body>
</html>
EOF
}

# Ejecuta el comando sipp redirigiendo su salida a /dev/null
sipp -sn uac ${PSTN_HOSTNAME}:5070 -s test -m 1 -r 1 -d 60000 -l 1 > /dev/null 2>&1
result=$?

if [ $result -eq 0 ] || [ $result -eq 1 ] || [ $result -eq 97 ]; then
  send_response "Exito" "El comando sipp se ejecutó con exito."
else
  send_response "Fallo" "Hubo un error al ejecutar el comando sipp con el codigo de salida $result. Por favor, revisa los logs para mas detalles."
fi
