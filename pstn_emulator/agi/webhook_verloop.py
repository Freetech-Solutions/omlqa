#!/usr/bin/env python
"""
Script AGI para enviar webhook a Verloop con parámetros personalizados.

Este script recibe los argumentos desde variables de entorno AGI:
- agi_arg_1: customer_id (requerido) - ID del cliente
- agi_arg_2: camp_id (requerido) - ID de la campaña
- agi_arg_3: disposition (requerido) - Disposición
- agi_arg_4: url (opcional) - URL del endpoint del webhook
- agi_arg_5: token (opcional) - Token de autorización Bearer (si no se proporciona, se autentica)
- agi_arg_6: call_id (opcional) - ID de la llamada
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

Ejemplo de uso en extensions.conf:
  AGI(webhook_verloop.py,1,11,Interesado)
  AGI(webhook_verloop.py,26,11,"No interesado",https://api.example.com/webhook,token123,1767797014.46,300)
  AGI(webhook_verloop.py,26,11,"Interesado",,,1767797014.46,300,,,,,username,password)
"""

import os
import json
import requests
import sys
from typing import Optional
from asterisk.agi import AGI


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
    }
    
    if call_id:
        body["call_id"] = call_id
    
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
        if hasattr(e.response, 'text'):
            print(f"Respuesta del servidor: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def main():
    # Inicializar AGI
    agi = AGI()
    
    # Leer argumentos desde variables de entorno AGI
    # agi_arg_1: customer_id (requerido)
    # agi_arg_2: camp_id (requerido)
    # agi_arg_3: disposition (requerido)
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
    disposition = agi.env.get('agi_arg_3')
    
    # Validar parámetros requeridos
    if not customer_id:
        agi.verbose("Error: agi_arg_1 (customer_id) es requerido", 1)
        sys.exit(1)
    if not camp_id:
        agi.verbose("Error: agi_arg_2 (camp_id) es requerido", 1)
        sys.exit(1)
    if not disposition:
        agi.verbose("Error: agi_arg_3 (disposition) es requerido", 1)
        sys.exit(1)
    
    # Parámetros opcionales
    url = agi.env.get('agi_arg_4')
    token = agi.env.get('agi_arg_5')
    call_id = agi.env.get('agi_arg_6')
    
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
    
    # Si no se proporciona token, autenticar primero
    if not token:
        # Obtener OML_API_HOST de variables de entorno
        api_host = os.environ.get('OML_API_HOST')
        
        if not api_host:
            agi.verbose("Error: OML_API_HOST no está definido y no se proporcionó token", 1)
            sys.exit(1)
        
        if not username or not password:
            agi.verbose("Error: Se requiere username y password para autenticación (agi_arg_12/13 o OML_USERNAME/OML_PASSWORD)", 1)
            sys.exit(1)
        
        # Normalizar la URL del API host
        api_host = normalize_api_host(api_host)
        agi.verbose(f"Autenticando en OML: {api_host}", 1)
        try:
            token = authenticate_oml(api_host, username, password, verify_ssl)
            agi.verbose("Autenticación exitosa", 1)
        except SystemExit:
            agi.verbose("Error en la autenticación", 1)
            sys.exit(1)
    
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