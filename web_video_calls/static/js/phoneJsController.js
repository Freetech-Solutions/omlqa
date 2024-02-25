/* Copyright (C) 2018 Freetech Solutions */

/* Requirements:            */
/*      - phoneJsFSM.js     */
/*      - miniPhoneJs.js    */



class PhoneJSController {
    // Connects PhoneJS with a PhoneJSView.
    constructor(miniPhoneConfig) {
        var sip_extension = miniPhoneConfig.sip_user;
        var sip_secret = miniPhoneConfig.sip_password;
        var KamailioHost = miniPhoneConfig.KamailioHost;
        var WebSocketPort = miniPhoneConfig.WebSocketPort;
        var WebSocketHost = miniPhoneConfig.WebSocketHost;
        var container_id = miniPhoneConfig.container_id;
        var container_class = miniPhoneConfig.container_class;
        var key_pad_buttons = miniPhoneConfig.key_pad_buttons;
        var buttons_class = miniPhoneConfig.buttons_class;
        var non_phone_actions_id = miniPhoneConfig.non_phone_actions_id;
        var show_keypad_button_id = miniPhoneConfig.show_keypad_button_id;
        var webphone_keys_id = miniPhoneConfig.webphone_keys_id;
        var phone_key_pad_id = miniPhoneConfig.phone_key_pad_id;
        var phone_actions_id = miniPhoneConfig.phone_actions_id;
        var footer_img_id = miniPhoneConfig.footer_img_id;
        var video_container_id = miniPhoneConfig.video_container_id;
        var reload_video_id = miniPhoneConfig.reload_video_id;
        // TODO: think if we can remove this nodes or parameterized it
        var webphone_title = miniPhoneConfig.webphone_title;
        var images = miniPhoneConfig.images;
        var webphone_status_id = 'webphone_status';
        var webphone_display_id = 'webphone_display';
        var extra_headers;

        if (miniPhoneConfig.hasOwnProperty('extra_headers')){
            extra_headers = miniPhoneConfig.extra_headers;
        }

        var destinations = miniPhoneConfig.destinations;
        var video_channels = miniPhoneConfig.video_channels;
        this.video_domain = miniPhoneConfig.video.domain;
        this.video_channel = sip_extension + sip_secret.substr(0, 15);
        this.video_channel = this.video_channel.replace(/[^a-zA-Z0-9-_]/g, '');

        this.view = new PhoneJSView(
            destinations, video_channels, container_id, key_pad_buttons,
            container_class, buttons_class, non_phone_actions_id, show_keypad_button_id,
            webphone_keys_id, phone_key_pad_id, phone_actions_id, footer_img_id, webphone_title,
            webphone_status_id, webphone_display_id, video_container_id, reload_video_id, images);
        this.phone = new PhoneJS(sip_extension, sip_secret,
                                 KamailioHost, WebSocketPort, WebSocketHost,
                                 extra_headers, this.view.audios, this.video_channel);
        this.phone_fsm = new PhoneFSM();
        this.number_to_call = undefined;

        // Load jitsi api options
        jitsi_options.roomName = this.video_channel
        jitsi_options.width = miniPhoneConfig.video.width;
        jitsi_options.height = miniPhoneConfig.video.height;
        jitsi_options.parentNode = jQuery('#' + video_container_id)[0];
        this.jitsi_api = undefined;

        this.subscribeToViewEvents();
        this.subscribeToFSMEvents();
        this.subscribeToPhoneEvents();
        this.view.setInputDisabledStatus('Inactive');
    }

    subscribeToViewEvents() {
        var self = this;

        // askForMediaPermission();

        this.view.onCallButtonClick.add(function(number_to_call, is_video_call) {
            self.askForMediaPermission();
            self.makeCall(number_to_call, is_video_call);
        });

        this.view.hang_up_button.click(function() {
            self.phone.hangUp();
        });

        this.view.onKeypadButtonClick.add(function(pressed_key) {
            if (self.phone_fsm.state == 'OnCall'){
                self.phone.currentSession.sendDTMF(pressed_key);
                var display_value = self.view.webphone_display.value;
                self.view.webphone_display.value = display_value + pressed_key;
            }
        });

        this.view.reload_video_button.click(function() {
            self.reloadVideo();
        });
    }

    subscribeToKeypadEvents() {
        /* Botones de telefono */
        // TODO: Va a tener teclado?
        var self = this;
        jQuery(".key").click(function(e) {
            var pressed_key = e.currentTarget.childNodes[0].data;
            if (self.phone_fsm.state == 'OnCall'){
                self.phone.currentSession.sendDTMF(pressed_key);
            }
        });
    }

    subscribeToFSMEvents() {
        var self = this;
        this.phone_fsm.observe({
            onInactive: function() {
                console.log('FSM: onInactive')
                self.view.setInputDisabledStatus('Inactive');
                // TODO: Mostrar boton para llamar
                // deshabilitar Teclado
            },
            onConnecting: function() {
                console.log('FSM: onConnecting')
                self.view.setInputDisabledStatus('Connecting');
                // TODO: Mostrar que esta llamando
                // deshabilitar Teclado
                self.phone.startSipSession();
            },
            onCalling: function() {
                console.log('FSM: onCalling')
                self.view.setInputDisabledStatus('Calling');
                self.phone.makeCall(self.number_to_call, self.is_video_call);
                // TODO: Seguir mostrando que esta llamando
                // deshabilitar Teclado
            },
            onOncall: function() {
                console.log('FSM: onOncall')
                self.view.setInputDisabledStatus('OnCall');
                // TODO: Mostrar que esta hablando
                // Habilitar Teclado
            },
        });
    }

    subscribeToPhoneEvents() {
        var self = this;

        /** User Agent **/
        this.phone.eventsCallbacks.onUserAgentRegistered.add(function () {
            console.log('onUserAgentRegistered');
            self.phone_fsm.call();
        });

        this.phone.eventsCallbacks.onUserAgentRegisterFail.add(function () {
            // TODO: Mostrar mensaje de error.
            self.phone_fsm.failedRegistration();
        });

        this.phone.eventsCallbacks.onUserAgentDisconnect.add(function () {
            // TODO: Mostrar mensaje de error.
            // TODO: Definir acciones a tomar.
        });

        /** Calls **/
        this.phone.eventsCallbacks.onSessionFailed.add(function() {
            // TODO: Mostrar mensaje de error.
            console.log('onSessionFailed');
            if (self.phone_fsm.state == 'Inactive'){ // Fallo el Register
                // Posiblemente haya fallado la sesion.
            } else if (self.phone_fsm.state == 'Connecting'){ // Fallo el Register
                self.phone_fsm.failedRegistration();
            } else if (self.phone_fsm.state == 'Calling'){ // Fallo la llamada
                self.phone_fsm.endCall();
                self.phone.cleanLastCallData();     // Es necesario?
            } else {
                console.log(`Session Failed at: ${self.phone_fsm.state}`)
            }
        });

        // Outbound Call
        this.phone.eventsCallbacks.onCallConnected.add(function() {
            console.log('onCallConnected from: ' + self.phone_fsm.state);
            self.view.webphone_display.value = '';
            // TODO: Mostrar que se conectó.
            if (self.phone_fsm.state == 'Calling') {
                self.phone_fsm.connectCall();
            } else {console.log(`Error: onCallConnected at: ${self.phone_fsm.state}`)}

        });

        this.phone.eventsCallbacks.onCallAccepted.add(function () {
            if (self.is_video_call)
                self.loadVideo();
        });

        this.phone.eventsCallbacks.onOutCallFailed.add(function(cause) {
            // TODO: Mostrar mensaje de error.
            console.log('--->  onOutCallFailed')
            self.logCallFailedStatus(cause);
            if (self.phone_fsm.state == 'Connecting') {
                self.phone_fsm.endCall();
                self.phone_fsm.failedRegistration();
            }
            if (self.phone_fsm.state == 'Calling') {
                self.phone_fsm.endCall()
            }
            // El fallo tambien dispara el onSessionFailed?? Si un fallo en
            // onSessionFailed despues dispara este
        });

        this.phone.eventsCallbacks.onCallEnded.add(function() {
            // TODO: Mostrar mensaje de que terminó la llamada
            self.phone_fsm.endCall();
            self.phone.cleanLastCallData();     // Es necesario?
            self.unloadVideo();
        });
    }

    askForMediaPermission() {
        if (navigator.appCodeName == 'Mozilla') {
            try {
                navigator.mediaDevices.getUserMedia({audio: true});
            }
            catch(error){
                alert('HTTPS Required');
            }
        }
        else {
            try {
                navigator.permissions.query({name: 'microphone'});
            }
            catch(error){
                alert('HTTPS Required');
            }
        }
    }

    makeCall(number_to_call, is_video_call) {
        console.log(number_to_call)
        this.number_to_call = number_to_call;
        this.is_video_call = is_video_call;
        this.phone_fsm.startCallProcess();
        //  TODO: Mostrar que esta llamando
    }

    loadVideo() {
        // window.open(this.video_domain + this.video_channel);
        /* For opening with Jitsi Api */
        this.jitsi_api = new JitsiMeetExternalAPI(this.video_domain, jitsi_options);
        var self = this;
        this.jitsi_api.addEventListener("readyToClose", function(a){
            self.unloadVideo();
        });
        this.view.reload_video_button.show();
    }

    unloadVideo() {
        if (this.jitsi_api) {
            this.jitsi_api.dispose();
            this.jitsi_api = undefined;
        }
        this.view.reload_video_button.hide();
    }

    reloadVideo() {
        if (this.jitsi_api) {
            this.unloadVideo();
        }
        this.loadVideo();
    }

    logCallFailedStatus(cause) {
        switch(cause){
            case JsSIP.C.causes.BUSY:
                console.log("Number busy, try later", "orange");
                break;
            case JsSIP.C.causes.REJECTED:
                console.log("Rejected, try later", "orange");
                break;
            case JsSIP.C.causes.UNAVAILABLE:
                console.log("Unavailable, contact your administrator", "red");
                break;
            case JsSIP.C.causes.NOT_FOUND:
                console.log("Error, check the number dialed", "red");
                break;
            case JsSIP.C.causes.AUTHENTICATION_ERROR:
                console.log("Authentication error, contact your administrator", "red");
                break;
            case JsSIP.C.causes.MISSING_SDP:
                console.log("Error, Missing sdp", "red");
                break;
            case JsSIP.C.causes.ADDRESS_INCOMPLETE:
                console.log("Address incomplete", "red");
                break;
            case JsSIP.C.causes.SIP_FAILURE_CODE:
                console.log("Service Unavailable, contact your administrator", "red");
                break;
            case JsSIP.C.causes.USER_DENIED_MEDIA_ACCESS:
                console.log("WebRTC Error: User denied media access", "red");
                break;
            default:
                console.log("Error: Call failed", "red");
        }
    }

}


var jitsi_options = {
  'configOverwrite': {
    'enableNoAudioDetection': false,
    'enableNoisyMicDetection': false,
    'startWithAudioMuted': true,
    'startWithVideoMuted': false,
    'startSilent': true,
    'hideLobbyButton': true,
    'requireDisplayName': false,
    'enableWelcomePage': false,
    'enableInsecureRoomNameWarning': false,
  },
  'interfaceConfigOverwrite': {
    'MOBILE_APP_PROMO': false,
    'SHOW_CHROME_EXTENSION_BANNER': false,
    'HIDE_KICK_BUTTON_FOR_GUESTS': true,
    'HIDE_INVITE_MORE_HEADER': true,
    'SHOW_JITSI_WATERMARK': false,
    'ENFORCE_NOTIFICATION_AUTO_DISMISS_TIMEOUT': 100,
    'TOOLBAR_BUTTONS': ['camera', 'fullscreen', 'chat', 'desktop'],
  }
};
