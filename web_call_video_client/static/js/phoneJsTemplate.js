/* exported phoneTemplate */

var phoneTemplate = `
    <h3>{{webphone_title}}</h3>
    <div id="webphone_outputs" class="webphone_outputs" hidden>
        <div id="{{webphone_status_id}}" class="webphone_status"></div>
        <div class="webphone_display_container">
           <input id="{{webphone_display_id}}" class="webphone_display" type="text" disabled="disabled">
        </div>
    </div>
    </br>
    <div id="{{webphone_keys_id}}" class="webphone_keys">
        <div id="{{phone_actions_id}}" class="phone_actions" style="display:inline-block">
          {{#destinations}}
            <button class="btn btn-outline-primary" id="call_{{index}}" data={{phone}}><img src="{{images.phone_green}}" height="20" width="20" align="center">{{name}}</button>
          {{/destinations}}
          {{#video_channels}}
            <button class="btn btn-outline-primary" id="videocall_{{index}}" data={{phone}}><img src="{{images.video_green}}" height="20" width="20" align="center">{{name}}</button>
          {{/video_channels}}
        </div>
        <div id="{{non_phone_actions_id}}" style="display:inline-block">
          <button id="{{show_keypad_button_id}}" class="btn btn-outline-inf"><img src="{{images.numpad}}" height="30" width="30" align="center">Numpad</button>
          <button id="call_end" class="btn btn-outline-danger" disabled=""><img src="{{images.phone_red}}" height="20" width="20" align="center">Cortar</button>
        </div>
        </br>
        <div id="{{phone_key_pad_id}}" class="phone_key_pad" hidden>
          {{#key_pad_buttons}}
            <div>
              {{#div}}
                <button id="btn_{{button_label}}" class="{{buttons_class}} btn_{{button_label}}" disabled="">{{button_value}}</button>
              {{/div}}
            </div>
          {{/key_pad_buttons}}
        </div>
    </div>
    <div id="{{video_container_id}}" class="webphone-body">
      <button class="btn btn-outline-primary" id="{{reload_video_id}}" style="display: none;">
        <img src="{{images.reload_video}}" height="10" width="10" align="center">
      </button>
    </div>

    <div id="{{footer_img_id}}"><img src="{{images.powered_by}}" height="100" width="100" align="right"></div>
`;
