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

# Equivalente a reiniciar_estadisticas_calldata() (DB2): CALLDATA + DISPOSITIONDATA.
# No usa docker/Django: el CGI corre dentro de nginxcgi (solo redis-cli + psql).
reset_redis_calldata() {
  host="${REDIS_HOSTNAME:-${REDIS_HOST:-redis}}"
  port="${REDIS_PORT:-6379}"
  db="${REDIS_CALLDATA_DB:-2}"

  if ! command -v redis-cli >/dev/null 2>&1; then
    echo "redis-cli no disponible" >&2
    return 1
  fi

  for pattern in \
    'OML:CALLDATA:CAMP:*' \
    'OML:CALLDATA:WAIT-TIME:CAMP:*' \
    'OML:CALLDATA:ABANDON-TIME:CAMP:*' \
    'OML:WHATSAPP:CAMP:*' \
    'OML:DISPOSITIONDATA:CAMP:*'
  do
    keys=$(redis-cli -h "$host" -p "$port" -n "$db" --raw KEYS "$pattern" 2>/dev/null)
    if [ -n "$keys" ]; then
      # shellcheck disable=SC2086
      echo "$keys" | xargs redis-cli -h "$host" -p "$port" -n "$db" DEL >/dev/null 2>&1 || return 1
    fi
  done
  return 0
}

# Intenta ejecutar los comandos redirigiendo su salida a /dev/null
if
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM interactions_summary' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM interaction_transfers' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM reportes_app_agentactivityeventv2' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM ominicontacto_app_respuestaformulariogestion' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM ominicontacto_app_auditoriacalificacion' > /dev/null 2>&1 &&
   PGPASSWORD=${PGPASSWORD} psql -U omnileads -h ${PGHOST} -d omnileads -c 'DELETE FROM ominicontacto_app_calificacioncliente' > /dev/null 2>&1 &&
   reset_redis_calldata; then
  send_response "Exito" "Los registros Postgres y las stats Redis CALLDATA/DISPOSITION (DB2) fueron eliminados."
else
  send_response "Fallo" "Hubo un error al eliminar los registros. Por favor, revisa los logs para más detalles."
fi
