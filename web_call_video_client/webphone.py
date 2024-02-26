# -*- coding: utf-8 -*-
from flask import Flask, render_template
import requests
import os
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

nginx_host = os.environ.get('OML_HOST', 'nginx')
kamailio_host = os.environ.get('KAMAILIO_HOST', 'nginx')
websocket_port = os.environ.get('WEBSOCKET_PORT', '443')  
websocket_host = os.environ.get('OML_HOST', 'nginx')
webphone_user = os.environ.get('CLIENT_USERNAME', 'webphone_user')
webphone_pass = os.environ.get('CLIENT_PASSWORD', 'webphone*123') 

config = {
    'URL_API_CREDENTIALS': f'https://{nginx_host}/api/v1/webphone/credentials/',
    'client_username': webphone_user,
    'client_password': webphone_pass,
}

def get_credentials(username, password):
    res = requests.post(config['URL_API_CREDENTIALS'],
                        auth=HTTPBasicAuth(username, password),
                        verify=False)
    if res.status_code == 200:
        response = res.json()
        if response['status'] == 'OK':
            return (response['sip_user'], response['sip_password'], response['video_domain'])

    return (None, None, None)

@app.route('/')
def index():
    sip_user, sip_password, video_domain = get_credentials(config['client_username'], config['client_password'])
    return render_template(
        'index.html',
        sip_user=sip_user,
        sip_password=sip_password,
        video_domain=video_domain,  # Corregido: Coma añadida
        kamailio_host=kamailio_host,
        websocket_port=websocket_port,
        websocket_host=websocket_host
    )

if __name__ == "__main__":
    app.run(ssl_context='adhoc')
