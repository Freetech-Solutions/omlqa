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

# Intenta ejecutar los comandos redirigiendo su salida a /dev/null
if PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM queue_log' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM reportes_app_llamadalog' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM reportes_app_actividadagentelog' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM ominicontacto_app_respuestaformulariogestion' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM ominicontacto_app_auditoriacalificacion' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM ominicontacto_app_calificacioncliente' > /dev/null 2>&1; then
  send_response "Exito" "Los registros fueron eliminados con exito."
else
  send_response "Fallo" "Hubo un error al eliminar los registros. Por favor, revisa los logs para más detalles."
fi
