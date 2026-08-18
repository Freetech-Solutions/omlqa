#!/usr/bin/env python
"""
AGI para agendar un callback via POST /api/v1/webhook/voicebot/agenda/.

Califica el contacto con la opción reservada Agenda y, si callback_valid=true
y la fecha/hora son válidas, crea o actualiza la AgendaContacto.

Este es el paso 1 del flujo de emulación agenda+summary. El dialplan debe
llamar después a webhook_verloop_client.py con outcome=agenda para anexar el
call_summary a las observaciones de esta agenda (paso 2; sin transfer ACD).

Argumentos AGI:
- agi_arg_1: contact_id (requerido) — X-OML-Contact-ID
- agi_arg_2: camp_id (requerido) — X-OML-Campaign-ID
- agi_arg_3: call_id (requerido) — X-OML-Call-ID
- agi_arg_4: phone (opcional) — si falta, agi_callerid o OML_PHONE
- agi_arg_5: callback_date (opcional, YYYY-MM-DD; default: mañana)
- agi_arg_6: callback_time (opcional, HH:MM:SS o HH:MM; default: 15:00:00)
- agi_arg_7: callback_request (opcional; default: PSTN emulator voicebot agenda)
- agi_arg_8: callback_rule (opcional; default: emulator_default)
- agi_arg_9: callback_valid (opcional; default: true)
- agi_arg_10: token Bearer (opcional; si falta, se autentica)
- agi_arg_11: username (opcional; si no, OML_USERNAME)
- agi_arg_12: password (opcional; si no, OML_PASSWORD)
- agi_arg_13: verify_ssl (opcional: true/1/yes/on)

Variables de entorno:
- OML_API_HOST: URL base de la API (requerido si no hay token)
- OML_USERNAME / OML_PASSWORD: credenciales de login
- OML_PHONE: teléfono de fallback

Ejemplo en extensions.conf (flujo completo agenda + summary):
  AGI(agenda.py,${oml_contactid},${oml_campid},${oml_uniqueid},${oml_telnum},,,PSTN emulator voicebot agenda,explicit_time)
  AGI(webhook_verloop_client.py,${oml_contactid},${oml_campid},agenda,${oml_uniqueid})

Ejemplo con fecha/hora explícitas:
  AGI(agenda.py,31,13,1786632922.31,1230003,2026-08-16,11:59:00,estoy interesado,explicit_time)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import requests
from asterisk.agi import AGI


def normalize_api_host(api_host: str) -> str:
    if not api_host:
        return api_host

    api_host = api_host.strip()
    if api_host.startswith("http://") or api_host.startswith("https://"):
        return api_host

    hostname = api_host.split("/")[0] if "/" in api_host else api_host
    if (
        hostname.startswith("localhost")
        or hostname.startswith("127.0.0.1")
        or "." not in hostname
    ):
        return f"http://{api_host}"
    return f"https://{api_host}"


def authenticate_oml(api_host: str, username: str, password: str, verify_ssl: bool = False) -> str:
    login_url = f"{api_host.rstrip('/')}/api/v1/login"
    try:
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            verify=verify_ssl,
            timeout=30,
        )
        if response.status_code == 404:
            try:
                error_msg = response.json().get(
                    "detail", "Credenciales inválidas o cuenta inactiva"
                )
            except ValueError:
                error_msg = "Credenciales inválidas o cuenta inactiva"
            print(f"Error de autenticación: {error_msg}", file=sys.stderr)
            print(f"URL: {login_url}", file=sys.stderr)
            sys.exit(1)

        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            print("Error: No se recibió token en la respuesta de autenticación", file=sys.stderr)
            sys.exit(1)
        return token
    except requests.exceptions.RequestException as exc:
        print(f"Error al autenticar en OML: {exc}", file=sys.stderr)
        print(f"URL intentada: {login_url}", file=sys.stderr)
        if getattr(exc, "response", None) is not None:
            print(f"Respuesta: {exc.response.text}", file=sys.stderr)
        sys.exit(1)


def send_agenda_webhook(
    api_host: str,
    token: str,
    camp_id: str,
    contact_id: str,
    call_id: str,
    phone: str,
    callback_valid: str,
    callback_date: str,
    callback_time: str,
    callback_request: str,
    callback_rule: str,
    verify_ssl: bool = False,
) -> dict:
    url = f"{api_host.rstrip('/')}/api/v1/webhook/voicebot/agenda/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "X-OML-Campaign-ID": str(camp_id),
        "X-OML-Contact-ID": str(contact_id),
        "X-OML-Call-ID": str(call_id),
        "phone": str(phone),
        "callback_valid": callback_valid,
        "callback_date": callback_date,
        "callback_time": callback_time,
        "callback_request": callback_request,
        "callback_rule": callback_rule,
    }
    try:
        response = requests.post(
            url, json=body, headers=headers, verify=verify_ssl, timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        print(f"Error enviando webhook agenda: {exc}", file=sys.stderr)
        print(f"URL: {url}", file=sys.stderr)
        print(f"Body: {json.dumps(body, ensure_ascii=False)}", file=sys.stderr)
        if getattr(exc, "response", None) is not None:
            print(f"Respuesta: {exc.response.text}", file=sys.stderr)
        sys.exit(1)


def _truthy(value: Optional[str], default: bool = True) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def main():
    agi = AGI()

    contact_id = (agi.env.get("agi_arg_1") or "").strip()
    camp_id = (agi.env.get("agi_arg_2") or "").strip()
    call_id = (agi.env.get("agi_arg_3") or "").strip()
    phone = (agi.env.get("agi_arg_4") or "").strip()
    callback_date = (agi.env.get("agi_arg_5") or "").strip()
    callback_time = (agi.env.get("agi_arg_6") or "").strip()
    callback_request = (agi.env.get("agi_arg_7") or "").strip()
    callback_rule = (agi.env.get("agi_arg_8") or "").strip()
    callback_valid_raw = (agi.env.get("agi_arg_9") or "").strip()
    token = (agi.env.get("agi_arg_10") or "").strip()
    username = (agi.env.get("agi_arg_11") or "").strip() or os.environ.get("OML_USERNAME")
    password = (agi.env.get("agi_arg_12") or "").strip() or os.environ.get("OML_PASSWORD")
    verify_ssl = _truthy(agi.env.get("agi_arg_13"), default=False)

    if not contact_id:
        agi.verbose("Error: agi_arg_1 (contact_id / X-OML-Contact-ID) es requerido", 1)
        sys.exit(1)
    if not camp_id:
        agi.verbose("Error: agi_arg_2 (camp_id / X-OML-Campaign-ID) es requerido", 1)
        sys.exit(1)
    if not call_id:
        agi.verbose("Error: agi_arg_3 (call_id / X-OML-Call-ID) es requerido", 1)
        sys.exit(1)

    phone = phone or (agi.env.get("agi_callerid") or "").strip() or os.environ.get("OML_PHONE", "")
    if not phone:
        agi.verbose("Error: phone es requerido (agi_arg_4, agi_callerid o OML_PHONE)", 1)
        sys.exit(1)

    if not callback_date:
        callback_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    if not callback_time:
        callback_time = "15:00:00"
    if not callback_request:
        callback_request = "PSTN emulator voicebot agenda"
    if not callback_rule:
        callback_rule = "emulator_default"

    callback_valid = "true" if _truthy(callback_valid_raw, default=True) else "false"

    api_host = os.environ.get("OML_API_HOST")
    if api_host:
        api_host = normalize_api_host(api_host)

    if not token:
        if not api_host:
            agi.verbose("Error: OML_API_HOST no está definido y no se proporcionó token", 1)
            sys.exit(1)
        if not username or not password:
            agi.verbose(
                "Error: se requiere username y password (agi_arg_11/12 o OML_USERNAME/OML_PASSWORD)",
                1,
            )
            sys.exit(1)
        agi.verbose(f"Autenticando en OML: {api_host}", 1)
        token = authenticate_oml(api_host, username, password, verify_ssl)
        agi.verbose("Autenticación exitosa", 1)
    elif not api_host:
        agi.verbose("Error: OML_API_HOST es requerido para POST /webhook/voicebot/agenda/", 1)
        sys.exit(1)

    agi.verbose(
        f"Enviando webhook agenda: contact={contact_id} camp={camp_id} "
        f"call={call_id} phone={phone} date={callback_date} time={callback_time}",
        1,
    )
    result = send_agenda_webhook(
        api_host=api_host,
        token=token,
        camp_id=camp_id,
        contact_id=contact_id,
        call_id=call_id,
        phone=phone,
        callback_valid=callback_valid,
        callback_date=callback_date,
        callback_time=callback_time,
        callback_request=callback_request,
        callback_rule=callback_rule,
        verify_ssl=verify_ssl,
    )
    agi.verbose(f"Webhook agenda enviado: {json.dumps(result, ensure_ascii=False)}", 1)


if __name__ == "__main__":
    main()
