#!/usr/bin/env bash
set -euo pipefail

DESTINO="${1:-}"
CANTIDAD="${2:-}"
PASO="${3:-}"
CONTAINER="${CONTAINER:-pstn_emulator}"
SIPP_TARGET="${SIPP_TARGET:-127.0.0.1:5070}"
DURACION_MS="${DURACION_MS:-60000}"

if [[ -z "$DESTINO" || -z "$CANTIDAD" || -z "$PASO" ]]; then
  echo "Uso: $0 <numero_destino> <cantidad> <paso_segundos>" >&2
  echo "Ejemplo: $0 01177660010 2 5" >&2
  exit 1
fi

if ! [[ "$DESTINO" =~ ^[0-9]+$ ]]; then
  echo "El numero destino debe ser numerico." >&2
  exit 1
fi
if ! [[ "$CANTIDAD" =~ ^[1-9][0-9]*$ ]]; then
  echo "La cantidad debe ser un entero positivo." >&2
  exit 1
fi
if ! [[ "$PASO" =~ ^[0-9]+$ ]]; then
  echo "El paso debe ser segundos (entero, 0 o mas)." >&2
  exit 1
fi

if (( PASO > 0 )); then
  RATE=(-r 1 -rp "$((PASO * 1000))")
else
  RATE=(-r "$CANTIDAD")
fi

docker exec -t "$CONTAINER" sipp -sn uac "$SIPP_TARGET" \
  -s "999${DESTINO}" \
  -m "$CANTIDAD" \
  "${RATE[@]}" \
  -d "$DURACION_MS" \
  -l "$CANTIDAD"