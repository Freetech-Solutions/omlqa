
/* Copyright (C) 2018 Freetech Solutions */

/*
 * Phone View for use with PhoneJSController
 */

/* global Mustache */
/* exported PhoneJSView */

class PhoneJSView {
    constructor (destinations, video_channels, container_id, key_pad_buttons_values,
        container_class, buttons_class, non_phone_actions_id, show_keypad_button_id,
        webphone_keys_id, phone_key_pad_id, phone_actions_id, footer_img_id, webphone_title,
        webphone_status_id, webphone_display_id, video_container_id, reload_video_id, images) {

        this.buttons_class = buttons_class;
        this.destinations = destinations;
        this.video_channels = video_channels;
        this.container_id = container_id;
        this.container_class = container_class;
        this.keypad_buttons_values = key_pad_buttons_values;
        this.inputs_ids = [];    // Add Action Buttons
        this.non_phone_actions_id = non_phone_actions_id;
        this.show_keypad_button_id = show_keypad_button_id;
        this.footer_img_id = footer_img_id;
        this.webphone_keys_id = webphone_keys_id;
        this.phone_key_pad_id = phone_key_pad_id;
        this.phone_actions_id = phone_actions_id;
        this.webphone_title = webphone_title;
        this.webphone_status_id = webphone_status_id;
        this.webphone_display_id = webphone_display_id;
        this.webphone_display_id = webphone_display_id;
        this.video_container_id = video_container_id
        this.reload_video_id = reload_video_id;
        this.images = images;

        /* For WebPhone Template rendering */
        this.phoneJsTemplate = phoneTemplate; // eslint-disable-line
        this.phoneJsTemplateContext = {
            'container_id': this.container_id,
            'container_class': this.container_class,
            'buttons_class': this.buttons_class,
            'key_pad_buttons': key_pad_buttons_values,
            'destinations': this.destinations,
            'video_channels': this.video_channels,
            'webphone_keys_id': this.webphone_keys_id,
            'phone_key_pad_id': this.phone_key_pad_id,
            'phone_actions_id': this.phone_actions_id,
            'webphone_title': this.webphone_title,
            'webphone_status_id': this.webphone_status_id,
            'webphone_display_id': this.webphone_display_id,
            'non_phone_actions_id': this.non_phone_actions_id,
            'show_keypad_button_id': this.show_keypad_button_id,
            'footer_img_id': this.footer_img_id,
            'video_container_id': this.video_container_id,
            'reload_video_id': this.reload_video_id,
            'images': this.images,
        };

        /* Events */
        this.onCallButtonClick = jQuery.Callbacks(),
        this.onKeypadButtonClick = jQuery.Callbacks(),

        this.createDOMElements();
    }

    createAudios() {
        this.audios = {
            remote: jQuery('<audio>', {id: 'remoteAudio', autoplay: 'autoplay'}),
            local: jQuery('<audio>', {id: 'localAudio', muted: 'muted'}),
        }
        jQuery('body').append(this.audios.remote);
        jQuery('body').append(this.audios.local);
    }


    createWebPhoneOutputNodes() {
        this.webphone_status = jQuery('#'+this.webphone_status_id);
        this.webphone_display = jQuery('#'+this.webphone_display_id);
    }

    createWebPhoneKeyPad() {
        var self = this;
        function createClickHandler(button, key) {
            button.click(function() {
                self.onKeypadButtonClick.fire(key);
            });
        }
        jQuery('.'+this.buttons_class).each(function() {
            var $button = jQuery(this);
            var buttonValue = $button.text();
            createClickHandler($button, buttonValue);
        });
    }

    createWebPhoneActions() {
        var self = this;
        function createClickHandler(button, phone, is_video_call) {
            button.click(function() {
                self.onCallButtonClick.fire(phone, is_video_call);
            });
        }

        this.phone_actions.find('button').each(function () {
            var $button = jQuery(this);
            var phone = $button.attr('data');
            var buttonId = $button.attr('id');
            if (buttonId != 'call_end') {
                // only creates handlers for destination buttons
                self.inputs_ids.push(buttonId);
                PHONE_STATUS_CONFIGS.Inactive.enabled_buttons.push(buttonId);
                var is_video_call = false;
                if (buttonId.indexOf('videocall_') == 0) {
                    is_video_call = true;
                }
                createClickHandler($button, phone, is_video_call);
            }
        });

        this.hang_up_button = jQuery('#call_end');
        this.inputs_ids.push('call_end');
    }

    renderPhoneTemplate() {
        var phoneJsRendered = Mustache.render(this.phoneJsTemplate, this.phoneJsTemplateContext);
        var $container = jQuery('#' + this.container_id);
        $container.html(phoneJsRendered);
        //jQuery('body').append($container);
    }

    addKeyPadVisibilityBinding() {
        var self = this;
        jQuery('#'+this.show_keypad_button_id).on('click', function () {
            self.webphone_key_pad.toggle();
        });
    }

    createInteractions() {
        this.webphone_keys = jQuery('#'+this.webphone_keys_id);
        this.webphone_key_pad = jQuery('#'+this.phone_key_pad_id);
        this.phone_actions = jQuery('#'+this.phone_actions_id);
        this.reload_video_button = jQuery('#'+this.reload_video_id);

        this.createWebPhoneKeyPad();
        this.createWebPhoneActions();
        this.createAudios();
        this.createWebPhoneOutputNodes();
        this.addKeyPadVisibilityBinding();
    }

    createDOMElements() {
        this.renderPhoneTemplate();
        this.createInteractions();
    }
    // FIXME: make a deeper revision for this methods ("disable", "enable")
    // seems to have an error on the propery parameters
    disable(elements) {
        this.setDisabledProp(elements, true);
    }

    enable(elements) {
        this.setDisabledProp(elements, true);
    }

    setDisabledProp(elements, property) {
        for (var i=0; i < elements.length; i++) {
            var element = elements[i];
            element.prop('disabled', property);
        }
    }

    setInputDisabledStatus(state_name) {
        var status_config = this.getStateConfig(state_name);
        this.setKeypadButtonsEnabled(status_config.keypad_enabled);
        this.setInputsEnabled(status_config.enabled_buttons);
    }

    setKeypadButtonsEnabled(enabled) {
        jQuery('.'+this.buttons_class).each(function() {
            var $button = jQuery(this);
            $button.prop('disabled', !enabled);
        });
    }

    setInputsEnabled(enabled_ones) {
        for (var i=0; i<this.inputs_ids.length; i++) {
            var id = this.inputs_ids[i];
            jQuery(`#${id}`).prop('disabled', enabled_ones.indexOf(id) == -1);
        }
    }

    getStateConfig(state_name) {
        return PHONE_STATUS_CONFIGS[state_name];
    }
}

var PHONE_STATUS_CONFIGS = {
    'Inactive': {
        keypad_enabled: false,
        enabled_buttons: [],  // add call buttons
    },
    'Connecting': {
        keypad_enabled: false,
        enabled_buttons: ['call_end'],
    },
    'LoggingIn': {
        keypad_enabled: false,
        enabled_buttons: ['call_end'],
    },
    'Calling': {
        keypad_enabled: false,
        enabled_buttons: ['call_end'],
    },
    'OnCall': {
        keypad_enabled: true,
        enabled_buttons: ['call_end'],
    },
};
