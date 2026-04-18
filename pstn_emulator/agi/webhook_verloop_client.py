#!/usr/bin/env python
"""
Script AGI para enviar webhook a Verloop con parámetros personalizados.

Este script recibe los argumentos desde variables de entorno AGI:
- agi_arg_1: customer_id (requerido) - ID del cliente
- agi_arg_2: camp_id (requerido) - ID de la campaña
- agi_arg_3: outcome (opcional) - True/False; si True se usa calificación GESTION_BOT, si False SCHEDULE_CALL_BOT
- agi_arg_4: url o callid (opcional) - Si contiene "://" es URL del webhook; si no, es callid (4º parámetro de negocio).
  Permite llamar con (customer_id, camp_id, outcome, callid) sin especificar url.
- agi_arg_5: token (opcional) - Token de autorización Bearer (si no se proporciona, se autentica)
- agi_arg_6: call_id (opcional) - ID de la llamada cuando no se usa agi_arg_4 como callid
- agi_arg_7: duration (opcional) - Duración de la llamada en segundos
- agi_arg_8: call_summary (opcional) - Resumen de la llamada
- agi_arg_9: sentiment (opcional) - Sentimiento (positive, negative, neutral)
- agi_arg_10: summary (opcional) - Resumen general
- agi_arg_11: verify_ssl (opcional) - "true", "1", "yes" o "on" para verificar SSL
- agi_arg_12: username (opcional) - Usuario para autenticación
- agi_arg_13: password (opcional) - Contraseña para autenticación
- agi_arg_14: channel (opcional) - Canal de comunicación (ej: "voice")
- agi_arg_15: intent_detected (opcional) - Intención detectada (ej: "customer_interested")
- agi_arg_16: phone (opcional) - Número de teléfono
- agi_arg_17: trigger_type (opcional) - Tipo de trigger (ej: "call_analysis")
- agi_arg_18: issue (opcional) - Issue en user_defined
- agi_arg_19: callback_slot (opcional) - Callback slot en user_defined
- agi_arg_20: work_type (opcional) - Tipo de trabajo en user_defined

Variables de entorno:
- OML_API_HOST: URL base de la API OML (requerido si no se proporciona token)
- OML_USERNAME: Usuario para autenticación (opcional, puede venir de agi_arg_12)
- OML_PASSWORD: Contraseña para autenticación (opcional, puede venir de agi_arg_13)
- OML_ID_EXTERNAL_SYSTEM: pk del sistema externo (opcional). Si camp_id (agi_arg_2) es el id_externo
  de la campaña, definir esta variable para el query idExternalSystem del GET de detalle de contacto.
- OML_CONTACT_DETAIL_REQUIRED: si es "true"/"1"/"yes"/"on", un fallo al obtener el detalle del
  contacto aborta el script; por defecto solo se registra el error y se continúa.

Flujo (tras autenticación si aplica):
1) GET /api/v1/campaign/{camp_id}/contacts/{customer_id}/ (Bearer) — solo logging AGI verbose;
   no modifica el body del webhook.
2) GET /api/v1/campaign/{camp_id}/dispositionOptions/ — obtiene id de calificación BOT según outcome.
3) POST al webhook Verloop (OML) con X-Verloop-Disposition y el resto de campos.

La disposition (X-Verloop-Disposition) se obtiene automáticamente: se consulta la API
GET /api/v1/campaign/{camp_id}/dispositionOptions/. Si agi_arg_3 (outcome) es True se usa el id de
GESTION_BOT; si es False se usa el id de SCHEDULE_CALL_BOT. Si outcome no se pasa, se usa GESTION_BOT.

En el body del webhook se envía además el campo "callid" (4º parámetro de negocio) cuando se
proporciona agi_arg_6 (call_id), para que el backend pueda proseguir la transferencia vía
comando Redis Pub/Sub voicebot_transfer_proceed sin error.

Ejemplo de uso en extensions.conf (customer_id, camp_id, outcome opcional, callid como 4º arg):
  AGI(webhook_verloop_client.py,1,26,)
  AGI(webhook_verloop_client.py,1,26,True)
  AGI(webhook_verloop_client.py,1,26,False,1771024232.107)
  AGI(webhook_verloop_client.py,1,26,False,,,1767797014.46,300,,,,,username,password)
"""

import os
import json
import requests
import sys
from typing import Optional
from urllib.parse import quote, urlencode

from asterisk.agi import AGI

# Longitud máxima del mensaje verbose para detalle de contacto (AGI / consola).
_VERBOSE_CONTACT_DETAIL_MAX = 3500


def normalize_api_host(api_host: str) -> str:
    """
    Normaliza la URL del API host agregando el esquema si falta.
    
    Args:
        api_host: URL base del API (puede tener o no esquema)
    
    Returns:
        URL normalizada con esquema
    """
    if not api_host:
        return api_host
    
    api_host = api_host.strip()
    
    # Si ya tiene esquema, retornar tal cual
    if api_host.startswith('http://') or api_host.startswith('https://'):
        return api_host
    
    # Extraer el hostname (sin esquema)
    hostname = api_host.split('/')[0] if '/' in api_host else api_host
    
    # Si no tiene esquema, determinar cuál usar:
    # - http:// para localhost, 127.0.0.1, o nombres de servicio Docker (sin punto)
    # - https:// para otros hostnames (dominios con punto)
    if (hostname.startswith('localhost') or 
        hostname.startswith('127.0.0.1') or 
        '.' not in hostname):
        # Nombres de servicio Docker o localhost usan HTTP
        return f"http://{api_host}"
    else:
        # Dominios externos usan HTTPS
        return f"https://{api_host}"


def authenticate_oml(
    api_host: str,
    username: str,
    password: str,
    verify_ssl: bool = False
) -> str:
    """
    Autentica en OML y obtiene el token de acceso.
    
    Args:
        api_host: URL base de la API OML (ej: https://konecta.sephir.tech)
        username: Nombre de usuario
        password: Contraseña
        verify_ssl: Si verificar certificados SSL (por defecto False)
    
    Returns:
        Token de autenticación
    
    Raises:
        SystemExit: Si la autenticación falla
    """
    login_url = f"{api_host}/api/v1/login"
    
    try:
        response = requests.post(
            login_url,
            json={
                "username": username,
                "password": password
            },
            verify=verify_ssl,
            timeout=30
        )
        
        # Django devuelve 404 cuando las credenciales son inválidas
        if response.status_code == 404:
            try:
                error_detail = response.json()
                error_msg = error_detail.get("detail", "Credenciales inválidas o cuenta inactiva")
                print(f"Error de autenticación: {error_msg}", file=sys.stderr)
                print(f"URL: {login_url}", file=sys.stderr)
                print(f"Usuario: {username}", file=sys.stderr)
                # Sugerencia si se usa HTTPS dentro de Docker
                if login_url.startswith('https://') and '.' not in api_host.split('://')[1].split('/')[0]:
                    print(f"Sugerencia: Si estás dentro de Docker, intenta usar HTTP en lugar de HTTPS", file=sys.stderr)
                    print(f"  (configura OML_API_HOST como 'http://nginx' o simplemente 'nginx')", file=sys.stderr)
            except:
                print(f"Error de autenticación: Credenciales inválidas o cuenta inactiva", file=sys.stderr)
                print(f"URL: {login_url}", file=sys.stderr)
            sys.exit(1)
        
        response.raise_for_status()
        
        data = response.json()
        token = data.get("token")
        
        if not token:
            print(f"Error: No se recibió token en la respuesta de autenticación", file=sys.stderr)
            sys.exit(1)
        
        return token
        
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP al autenticar en OML: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Detalle del error: {error_detail}", file=sys.stderr)
            except:
                print(f"Respuesta del servidor: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al autenticar en OML: {e}", file=sys.stderr)
        print(f"URL intentada: {login_url}", file=sys.stderr)
        sys.exit(1)


def get_bot_disposition_ids(
    camp_id: str,
    token: str,
    api_host: str,
    verify_ssl: bool = False
) -> dict:
    """
    Obtiene las opciones de calificación de la campaña y devuelve un diccionario
    con las calificaciones que terminan en _BOT y su id.

    Args:
        camp_id: ID de la campaña
        token: Token de autorización Bearer
        api_host: URL base de la API OML (ej: https://localhost)
        verify_ssl: Si verificar certificados SSL

    Returns:
        Diccionario { "NOMBRE_BOT": id, ... } solo con opciones cuyo name termina en _BOT

    Raises:
        SystemExit: Si la petición falla
    """
    url = f"{api_host.rstrip('/')}/api/v1/campaign/{camp_id}/dispositionOptions/"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=verify_ssl,
            timeout=30
        )
        response.raise_for_status()
        options = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener dispositionOptions: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None and getattr(e.response, 'text', None):
            print(f"Respuesta del servidor: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    bot_dispositions = {}
    for item in options:
        name = item.get("name") or ""
        if name.endswith("_BOT"):
            bot_dispositions[name] = item.get("id")

    return bot_dispositions


def fetch_contacto_detalle_oml(
    camp_id: str,
    contact_id: str,
    token: str,
    api_host: str,
    verify_ssl: bool = False,
    id_external_system: Optional[str] = None,
) -> Optional[dict]:
    """
    GET detalle de contacto por campaña (solo para logging en el AGI).

    GET {api_host}/api/v1/campaign/{camp_id}/contacts/{contact_id}/
    Query opcional: idExternalSystem (pk) si camp_id es id_externo.

    Returns:
        dict parseado de JSON si la respuesta es 200; None si error de red, HTTP o datos inválidos.
    """
    try:
        contact_pk = int(str(contact_id).strip())
        if contact_pk <= 0:
            raise ValueError("contact_pk must be positive")
    except (ValueError, TypeError):
        print(
            f"fetch_contacto_detalle_oml: contact_id inválido (se espera pk numérico): {contact_id!r}",
            file=sys.stderr,
        )
        return None

    query: dict = {}
    if id_external_system is not None and str(id_external_system).strip() != "":
        try:
            query["idExternalSystem"] = int(str(id_external_system).strip())
        except (ValueError, TypeError):
            print(
                f"fetch_contacto_detalle_oml: id_external_system inválido: {id_external_system!r}",
                file=sys.stderr,
            )
            return None

    camp_segment = quote(str(camp_id).strip(), safe="")
    url = f"{api_host.rstrip('/')}/api/v1/campaign/{camp_segment}/contacts/{contact_pk}/"
    if query:
        url += "?" + urlencode(query)

    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            url,
            headers=headers,
            verify=verify_ssl,
            timeout=30,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"fetch_contacto_detalle_oml HTTP: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            try:
                print(f"  URL: {url}", file=sys.stderr)
                print(f"  body: {e.response.text[:2000]}", file=sys.stderr)
            except Exception:
                pass
        return None
    except requests.exceptions.RequestException as e:
        print(f"fetch_contacto_detalle_oml: {e}", file=sys.stderr)
        return None

    try:
        return response.json()
    except ValueError:
        print("fetch_contacto_detalle_oml: respuesta no es JSON válido", file=sys.stderr)
        return None


def send_verloop_webhook(
    customer_id: str,
    camp_id: str,
    disposition: str,
    url: Optional[str] = None,
    token: Optional[str] = None,
    call_id: Optional[str] = None,
    duration: Optional[int] = None,
    call_summary: Optional[str] = None,
    sentiment: Optional[str] = None,
    summary: Optional[str] = None,
    verify_ssl: bool = False,
    channel: Optional[str] = None,
    intent_detected: Optional[str] = None,
    phone: Optional[str] = None,
    trigger_type: Optional[str] = None,
    issue: Optional[str] = None,
    callback_slot: Optional[str] = None,
    work_type: Optional[str] = None
) -> dict:
    """
    Envía un webhook a Verloop con los parámetros especificados.
    
    Args:
        customer_id: ID del cliente (X-Verloop-customerID)
        camp_id: ID de la campaña (X-Verloop-CampID)
        disposition: Disposición (X-Verloop-Disposition)
        url: URL del endpoint del webhook (si es None, se construye desde OML_API_HOST)
        token: Token de autorización Bearer
        call_id: ID de la llamada
        duration: Duración de la llamada en segundos
        call_summary: Resumen de la llamada
        sentiment: Sentimiento de la llamada
        summary: Resumen general
        verify_ssl: Si verificar certificados SSL (por defecto False)
        channel: Canal de comunicación (ej: "voice")
        intent_detected: Intención detectada (ej: "customer_interested")
        phone: Número de teléfono
        trigger_type: Tipo de trigger (ej: "call_analysis")
        issue: Issue en user_defined
        callback_slot: Callback slot en user_defined
        work_type: Tipo de trabajo en user_defined
    
    Returns:
        Respuesta de la API como diccionario
    """
    # Si no se proporciona URL, construirla desde OML_API_HOST
    if not url:
        api_host = os.environ.get('OML_API_HOST')
        if api_host:
            api_host = normalize_api_host(api_host)
            url = f"{api_host}/api/v1/webhook/verloop/"
        else:
            url = "https://localhost/api/v1/webhook/verloop/"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Preparar el body del request (formato según ejemplo: datos en el JSON, no en headers)
    body = {
        "X-Verloop-customerID": customer_id,
        "X-Verloop-CampID": camp_id,
        "X-Verloop-Disposition": disposition,
        "X-Verloop-UniqueID": call_id,
    }
    
    if call_id:
        body["call_id"] = call_id
        body["callid"] = call_id  # 4º parámetro de negocio para calificación y Redis voicebot_transfer_proceed
        # X-Verloop-UniqueID / X-Verloop-callID para compatibilidad con VerloopWebhookView
        # calificacion.callid y el comando Redis voicebot_transfer_proceed
        body["X-Verloop-UniqueID"] = call_id
        body["X-Verloop-callID"] = call_id

    if duration is not None:
        body["duration"] = duration
    
    # Campos adicionales del formato nuevo
    if channel:
        body["channel"] = channel
    
    if intent_detected:
        body["intent_detected"] = intent_detected
    
    if phone:
        body["phone"] = phone
    
    if trigger_type:
        body["trigger_type"] = trigger_type
    
    # Construir el análisis con el formato del ejemplo
    if call_summary or sentiment or summary or issue or callback_slot or work_type:
        body["analysis"] = {}
        
        # user_defined con todos los campos posibles
        user_defined = {}
        if call_summary:
            user_defined["call_summary"] = call_summary
        if issue:
            user_defined["issue"] = issue
        if callback_slot:
            user_defined["callback_slot"] = callback_slot
        if work_type:
            user_defined["work_type"] = work_type
        
        if user_defined:
            body["analysis"]["user_defined"] = user_defined
        
        if sentiment:
            body["analysis"]["sentiment"] = sentiment
        
        if summary:
            body["analysis"]["summary"] = summary
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=body,
            verify=verify_ssl
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el webhook: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None and getattr(e.response, 'text', None):
            print(f"Respuesta del servidor: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def main():
    # Inicializar AGI
    agi = AGI()
    
    # Leer argumentos desde variables de entorno AGI
    # agi_arg_1: customer_id (requerido)
    # agi_arg_2: camp_id (requerido)
    # agi_arg_3: outcome (opcional) - True → GESTION_BOT, False → SCHEDULE_CALL_BOT
    # agi_arg_4: url (opcional)
    # agi_arg_5: token (opcional)
    # agi_arg_6: call_id (opcional)
    # agi_arg_7: duration (opcional)
    # agi_arg_8: call_summary (opcional)
    # agi_arg_9: sentiment (opcional)
    # agi_arg_10: summary (opcional)
    # agi_arg_11: verify_ssl (opcional, "true" o "1" para True)
    # agi_arg_12: username (opcional, para autenticación)
    # agi_arg_13: password (opcional, para autenticación)
    # agi_arg_14: channel (opcional)
    # agi_arg_15: intent_detected (opcional)
    # agi_arg_16: phone (opcional)
    # agi_arg_17: trigger_type (opcional)
    # agi_arg_18: issue (opcional)
    # agi_arg_19: callback_slot (opcional)
    # agi_arg_20: work_type (opcional)
    
    customer_id = agi.env.get('agi_arg_1')
    camp_id = agi.env.get('agi_arg_2')
    
    # Validar parámetros requeridos
    if not customer_id:
        agi.verbose("Error: agi_arg_1 (customer_id) es requerido", 1)
        sys.exit(1)
    if not camp_id:
        agi.verbose("Error: agi_arg_2 (camp_id) es requerido", 1)
        sys.exit(1)
    
    # Parámetros opcionales
    # agi_arg_4: puede ser URL del webhook o callid (4º parámetro de negocio).
    # Si contiene "://" se interpreta como URL; si no, como call_id cuando agi_arg_6 no está definido.
    arg_4 = (agi.env.get('agi_arg_4') or '').strip()
    if arg_4 and ('://' in arg_4 or arg_4.lower().startswith('http')):
        url = arg_4
        call_id = agi.env.get('agi_arg_6')
    else:
        url = None
        call_id = agi.env.get('agi_arg_6') or (arg_4 if arg_4 else None)
    token = agi.env.get('agi_arg_5')
    
    # Convertir duration a int si está presente
    duration = None
    duration_str = agi.env.get('agi_arg_7')
    if duration_str:
        try:
            duration = int(duration_str)
        except ValueError:
            agi.verbose(f"Advertencia: agi_arg_7 (duration) no es un número válido: {duration_str}", 2)
    
    call_summary = agi.env.get('agi_arg_8')
    sentiment = agi.env.get('agi_arg_9')
    summary = agi.env.get('agi_arg_10')
    
    # Convertir verify_ssl a bool
    verify_ssl_str = agi.env.get('agi_arg_11', '').lower()
    verify_ssl = verify_ssl_str in ('true', '1', 'yes', 'on')
    
    # Obtener username y password (de agi_arg o variables de entorno)
    username = agi.env.get('agi_arg_12') or os.environ.get('OML_USERNAME')
    password = agi.env.get('agi_arg_13') or os.environ.get('OML_PASSWORD')
    
    # Nuevos parámetros opcionales del formato
    channel = agi.env.get('agi_arg_14')
    intent_detected = agi.env.get('agi_arg_15')
    phone = agi.env.get('agi_arg_16')
    trigger_type = agi.env.get('agi_arg_17')
    issue = agi.env.get('agi_arg_18')
    callback_slot = agi.env.get('agi_arg_19')
    work_type = agi.env.get('agi_arg_20')
    
    # API host para dispositionOptions (necesario para obtener id GESTION_BOT)
    api_host = os.environ.get('OML_API_HOST')
    if api_host:
        api_host = normalize_api_host(api_host)
    
    # Si no se proporciona token, autenticar primero
    if not token:
        if not api_host:
            agi.verbose("Error: OML_API_HOST no está definido y no se proporcionó token", 1)
            sys.exit(1)
        
        if not username or not password:
            agi.verbose("Error: Se requiere username y password para autenticación (agi_arg_12/13 o OML_USERNAME/OML_PASSWORD)", 1)
            sys.exit(1)
        
        agi.verbose(f"Autenticando en OML: {api_host}", 1)
        try:
            token = authenticate_oml(api_host, username, password, verify_ssl)
            agi.verbose("Autenticación exitosa", 1)
        except SystemExit:
            agi.verbose("Error en la autenticación", 1)
            sys.exit(1)

    # 1) Detalle de contacto OML (solo log; no modifica el body del webhook)
    detail_required = os.environ.get("OML_CONTACT_DETAIL_REQUIRED", "").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )
    ext_sys_raw = (os.environ.get("OML_ID_EXTERNAL_SYSTEM") or "").strip()
    ext_sys_param = ext_sys_raw if ext_sys_raw else None

    if api_host:
        contact_detail = fetch_contacto_detalle_oml(
            camp_id,
            customer_id,
            token,
            api_host,
            verify_ssl,
            id_external_system=ext_sys_param,
        )
        if contact_detail is not None:
            log_payload = json.dumps(contact_detail, ensure_ascii=False)
            if len(log_payload) > _VERBOSE_CONTACT_DETAIL_MAX:
                log_payload = log_payload[:_VERBOSE_CONTACT_DETAIL_MAX] + "...(truncado)"
            if contact_detail.get("status") == "OK":
                agi.verbose(f"OML contacto detalle: {log_payload}", 1)
            else:
                agi.verbose(f"OML contacto detalle (respuesta no OK): {log_payload}", 1)
        else:
            msg = "No se pudo obtener el detalle del contacto; se continúa con disposition y webhook"
            agi.verbose(msg, 2)
            print(msg, file=sys.stderr)
            if detail_required:
                agi.verbose("OML_CONTACT_DETAIL_REQUIRED activo: abortando", 1)
                sys.exit(1)
    else:
        agi.verbose("OML_API_HOST ausente: se omite GET detalle de contacto", 2)

    # Evaluar outcome (agi_arg_3): True → GESTION_BOT, False → SCHEDULE_CALL_BOT (por defecto GESTION_BOT)
    outcome_str = (agi.env.get('agi_arg_3') or "").strip().lower()
    outcome_false = outcome_str in ("false", "0", "no", "off")
    disposition_name = "SCHEDULE_CALL_BOT" if outcome_false else "GESTION_BOT"

    # Obtener opciones de calificación y usar el id según outcome
    if not api_host:
        agi.verbose("Error: OML_API_HOST es requerido para obtener las opciones de calificación (dispositionOptions)", 1)
        sys.exit(1)
    bot_dispositions = get_bot_disposition_ids(camp_id, token, api_host, verify_ssl)
    disposition_id = bot_dispositions.get(disposition_name)
    if disposition_id is None:
        agi.verbose(f"Error: No se encontró la opción de calificación {disposition_name} en la campaña", 1)
        sys.exit(1)
    disposition = str(disposition_id)

    # La función send_verloop_webhook construirá la URL desde OML_API_HOST si no se proporciona
    result = send_verloop_webhook(
        customer_id=customer_id,
        camp_id=camp_id,
        disposition=disposition,
        url=url,
        token=token,
        call_id=call_id,
        duration=duration,
        call_summary=call_summary,
        sentiment=sentiment,
        summary=summary,
        verify_ssl=verify_ssl,
        channel=channel,
        intent_detected=intent_detected,
        phone=phone,
        trigger_type=trigger_type,
        issue=issue,
        callback_slot=callback_slot,
        work_type=work_type
    )
    
    # Enviar resultado a AGI verbose para logging
    agi.verbose(f"Webhook enviado exitosamente: {json.dumps(result, ensure_ascii=False)}", 1)


if __name__ == "__main__":
    main()