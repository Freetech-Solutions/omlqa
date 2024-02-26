/* Copyright (C) 2018 Freetech Solutions */

class PhoneJS {
    constructor(sipExtension, sipSecret,
                KamailioHost, WebSocketPort, WebSocketHost,
                extra_headers, audios, video_channel) {
        /* Config */
        this.sipExtension = sipExtension;
        this.sipSecret = sipSecret;
        this.KamailioHost = KamailioHost;
        this.WebSocketPort = WebSocketPort;
        this.WebSocketHost = WebSocketHost;
        this.extra_headers = extra_headers;
        this.video_channel = video_channel;

        /* Components / Colaborators */
        this.userAgent = undefined;
        this.currentSession = undefined;

        this.audios = audios;

        /* Local Variables */
        this.callTimeoutHandler = undefined;
// this.transferTimeoutHandler = undefined;

        /* eventsCallbacks */
        this.eventsCallbacks = {
            onUserAgentRegistered: jQuery.Callbacks(),
            onUserAgentDisconnect: jQuery.Callbacks(),
            onUserAgentRegisterFail: jQuery.Callbacks(),

            onCallConnected:  jQuery.Callbacks(),
            onCallAccepted: jQuery.Callbacks(),
            onOutCallFailed: jQuery.Callbacks(),
            onCallEnded: jQuery.Callbacks(),

            onSessionFailed: jQuery.Callbacks(),

        }
    }

    startSipSession() {
        var socket = new JsSIP.WebSocketInterface('wss://' + this.WebSocketHost + ':' + this.WebSocketPort + '/ws' );
        var config = {
                sockets: [ socket ],
                uri: "sip:" + this.sipExtension + "@" + this.KamailioHost,
                password: this.sipSecret,
                realm: this.KamailioHost,
                hack_ip_in_contact: true,
                session_timers: false,
                register_expires: 120,
                pcConfig: {
                    rtcpMuxPolicy: 'negotiate'
                }
            };

        // Inicializar Sesion de Websocket con Kamailio  "Hacer Login"
        if (this.sipExtension && this.sipSecret) {
            this.userAgent = new JsSIP.UA(config);
            this.userAgent.start();
            this.subscribeToUserAgentEvents();
        }
    }

    logout() {
        var options = {
            all: true
        };
        this.userAgent.unregister(options);
    }

    /******  Eventos User Agent  *******/
    subscribeToUserAgentEvents() {
        var self = this;
        //Connects to the WebSocket server
        this.userAgent.on("registered", function(e) { // cuando se registra la entidad SIP
            console.log('User Agent: registered');
            self.eventsCallbacks.onUserAgentRegistered.fire();
        });

        this.userAgent.on("disconnected", function(e) {
            console.log('User Agent: disconnected');
            self.eventsCallbacks.onUserAgentDisconnect.fire();
        });

        this.userAgent.on("registrationFailed", function(e) { // cuando falla la registracion
            console.log('User Agent: registrationFailed');
            console.log(e);
            self.eventsCallbacks.onUserAgentRegisterFail.fire();
        });

        /*
           La sesion se crea al: Llamar, Hacer Login
        */
        this.userAgent.on("newRTCSession", function(e) {
            console.log('newRTCSession');
            self.invite_request = e.request;
            self.currentSession = e.session;

            //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            // Session Events
            self.currentSession.on("failed", function(e) {
                console.log('session: failed');
                self.eventsCallbacks.onSessionFailed.fire();
            });

            self.currentSession.on("confirmed", function(e) {
                // Aca si puedo decir que esta establecida
                console.log('session: confirmed');
                self.eventsCallbacks.onCallConnected.fire();
            });

            self.currentSession.on("accepted", function() { // cuando se establece una llamada
                self.eventsCallbacks.onCallAccepted.fire();
                console.log('session: accepted');
            });

            self.currentSession.on("ended", function() { 
                // Cuando Finaliza la llamada. Ya se maneja desde el evento de la llamada
                console.log('session: ended');
            });
        });
    };

    /* FUNCTIONS */

    makeCall(number_to_call, is_video_call) {
        var self = this;
        console.log('makeCall: ' + number_to_call);

        // Luego de 60 segundos sin respuesta, stop al ringback y cuelga discado
        this.callTimeoutHandler = setTimeout(function() {self.hangUp();}, 61000);

        var eventHandlers = {
            // TODO: Verificar si no hay otros posibles eventos.
            // Asegurarse de que cualquier finalizacion termina llamando al clearTimeout(...)
            'confirmed': function(e) {
                console.log('makeCall: confirmed');
                clearTimeout(self.callTimeoutHandler);
            },
            'addstream': function(e) {
                console.log('makeCall: addstream');
                clearTimeout(self.callTimeoutHandler);
            },
            'failed': function(data) {
                console.log('makeCall: failed - ' + number_to_call);
                clearTimeout(self.callTimeoutHandler);
                self.eventsCallbacks.onOutCallFailed.fire(data.cause);
                if (data.cause === JsSIP.C.causes.BUSY) {
                }
            },
            'ended': function(data) {
                console.log('Call ENDED')
                self.eventsCallbacks.onCallEnded.fire();
            },
        };
        var opciones = {
            'eventHandlers': eventHandlers,
            'mediaConstraints': {
                'audio': true,
                'video': false
            },
            pcConfig: {
                rtcpMuxPolicy: 'negotiate'
            }
        };
        if (this.extra_headers !== undefined || is_video_call)
            opciones['extraHeaders'] = this.extra_headers;
        if(is_video_call && this.extra_headers == undefined)
            opciones['extraHeaders'] = [];
        if(is_video_call)
            opciones['extraHeaders'].push('OMLVIDEO: ' + this.video_channel);

        // Finalmente Mando el invite/llamada
        this.userAgent.call("sip:" + number_to_call + "@" + this.KamailioHost, opciones);
        this.subscribeToSessionConnectionEvents();
    }

    subscribeToSessionConnectionEvents() {
        var self = this;
        this.currentSession.connection.addEventListener('addstream', function (event) {
            console.log('currentSession.connection: addstream');
            self.audios.remote[0].srcObject = event.stream;
        });
    }

    cleanLastCallData() {
        self.currentSession = undefined;
    }

    hangUp() {
        this.userAgent.terminateSessions();
    }

};
