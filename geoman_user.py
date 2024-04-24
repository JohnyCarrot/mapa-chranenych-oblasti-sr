from branca.element import Element, Figure,MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin
from folium.utilities import parse_options


class Geoman(JSCSSMixin, MacroElement):

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            async function zozbieraj_iframe_na_upravu() {
                  let user = {
                  username: '{{ this.username }}',
                  dostan_vrstvy_uprava_iframe: null
                };

                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });
                    response.text().then(function (text) {
                    uprav_vrstvu(text);
                        
                });
           return true;
        }
        
            async function zozbieraj_iframe_na_zmazanie() {
                  let user = {
                  username: '{{ this.username }}',
                  dostan_vrstvy_zmazanie_iframe: null
                };

                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });
                    response.text().then(function (text) {
                    zmaz_vrstvu(text);
                        
                });
           return true;
        }
        
         const draggable = new L.DraggableLines({{ this._parent.get_name() }}, 
            {
	        enableForLayer: false
            });
        parent.posledne_html_z_editora = "";
        var html_pred_zmenou = "";
        
        var obchadzanie_iframe = window.setInterval(function(){
              zozbieraj_iframe_na_upravu();
              zozbieraj_iframe_na_zmazanie();
            }, 300);
        
        var textbox_ako_klasa   = L.Control.extend({
            onAdd: function() {
                
            var text = L.DomUtil.create('div');
            text.id = "info_text_delete";
            text.innerHTML = '<h1 style="color: red;font-size: 50px;">' + 'Režim úpravy' + "</h1>"
            return text;
            },
        });
        var textbox_edit_1 = new textbox_ako_klasa({ position: 'bottomright' });
        var textbox_edit_2 = new textbox_ako_klasa({ position: 'bottomleft' });
        async function coord_update(html,geometry,id,update_pozicia,style) {
                  let user = {
                  id_objektu: id,
                  html: html,
                  geometry: geometry,
                  update_pozicia: update_pozicia,
                  admin_coord_update: null,
                  style: style
                };

                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });
                           return true;
        }
        
        
        var StyleEditorContent = `
        <style>
            .leaflet-styleeditor-stroke {
                height: 20px;
                width: 150px;
                background-repeat: no-repeat;
                border: 1px solid white;
                background-image: url("static/administration/dash_array.png");
                cursor: pointer;
            }
            .leaflet-styleeditor-stroke:hover {
                border: 1px solid black;
            }

        </style>
        
        <div style="height:500px; width:300px;" class="content-hlavny">
        
        <label id="draggable_checkbox_label">Editor tvaru</label>
        <input type="checkbox" id="draggable_checkbox" min="0" max="100" />
        <br>
        
        <b>Farba hrany: </b> <div id="zmena-farby" style="width:25px;height:25px;border: 1px solid black;"></div>
        <br>
        
        <b>Viditeľnosť hrany: </b> <br>
        <label id="layer_opacity_label">-</label>
        <input type="range" id="layer_opacity" min="0" max="100" />
        
                <br>
        <b>Hrúbka hrany: </b> <br>
        <label id="layer_weight_label">-</label>
        <input type="range" id="layer_weight" min="0" max="30" />
                        <br>
        <b>Orámovanie hrany: </b> <br>
        <div id="layer_dash_array_1" class="leaflet-styleeditor-stroke" style="background-position: 0px -75px;"></div>
        <div id="layer_dash_array_2" class="leaflet-styleeditor-stroke" style="background-position: 0px -95px;"></div>
        <div id="layer_dash_array_3" class="leaflet-styleeditor-stroke" style="background-position: 0px -115px;"></div>
        <br>
        
        <b>Farba pozadia: </b> <div id="zmena-pozadie" style="width:25px;height:25px;border: 1px solid black;"></div>
        <br>
        
        <b>Viditeľnosť pozadia: </b> <br>
        <label id="layer_opacity_label_fill">-</label>
        <input type="range" id="layer_opacity_fill" min="0" max="100" />
        <br>
        <button onclick="parent.uprava_html()" type=button>Uprava-HTML</button>
        <br>
        <button id="style_reset_button"type="button">Resetovať</button>
        
        </div>
        `;
        
        
        var StyleEditor = L.control.window({{ this._parent.get_name() }},{title:'',content:StyleEditorContent,
        visible: false,
        maxWidth: 650,
        position: 'topRight',
        prompt: {callback:function(){
    //alert('Chellou!');
    
        //koniec funkcie
        }
    ,buttonOK:'  '} //Po stlačení button OK zmizne celé okno, zrejme bude treba dorobiť iný button, zrejme ho treba prevytvoriť
        });
        StyleEditor.disableBtn();
        var picker;
        var picker_pozadie;
         var stateChangingButton = L.easyButton({
                states: [{
                        stateName: 'zoom-to-forest',        // name the state
                        icon:      'fa-pen-to-square',               // and define its properties
                        title:     'Upraviť',      // like its title
                        onClick: function(btn, map) {       // and its callback
                            draggable.disable();
                            textbox_edit_1.addTo( {{ this._parent.get_name() }} );
                            textbox_edit_2.addTo( {{ this._parent.get_name() }} );
                            let layer_previous_options;
                            let selected_layers = [];                                    
                                    {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                                            if(layer.feature && (layer.feature.geometry.podskupina_spravca == '{{ this.username }}' || layer.feature.geometry.zdielane_w == true)  ){
                                            
                                            if(layer.feature.geometry.type === "Point"){return;}
                                            
                                            if(map.getBounds().contains( layer.getBounds().getCenter() )) { 
                                                layer.upraveny = true
                                                //draggable.enableForLayer(layer);
                                                selected_layers.push(layer);
                                                layer.previous_options = JSON.parse(JSON.stringify(layer.options)); //ked sa bude robit nas5 tlacidlo
                                                layer_previous_options = JSON.parse(JSON.stringify(layer.options));
                                                //console.log(layer); //do budúcna ZMAZAŤ
                                                html_pred_zmenou = layer.feature.geometry.popup_HTML;
                                                 
                                             }
                                             
                                            }                             
                                    }); //Koniec označenia vrsiev
                            
                            if(selected_layers.length == 0){
                                alert("Momentálne nie sú k dispozícii žiadne vrstvy na úpravu. Priblížte alebo posuňte mapu tak, aby boli viditeľné vrstvy na editáciu.");
                                textbox_edit_1.remove();
                                textbox_edit_2.remove();
                                return null;
                            } 
                            parent.posledne_html_z_editora = html_pred_zmenou;                          
                            StyleEditor.show();
                            picker = new Picker({ //Zaciatok pickera
                                parent: document.querySelector('#zmena-farby'),
                                alpha: false,
                                popup: 'bottom',
                                cancelButton: false,
                                editor: false,
                                defaultColor: layer_previous_options.color,
                                onChange: function(color) {
                                              document.querySelector('#zmena-farby').style.background = color.rgbaString;
                                              selected_layers.forEach(function (layer, index) {
                                                  layer.options.color = color.rgbaString;
                                                  layer.setStyle(layer.options);
                                                });
                                              
                                          },
                            }); //Koniec pickera
                            document.getElementById('draggable_checkbox').outerHTML = document.getElementById('draggable_checkbox').outerHTML;
                            document.getElementById('draggable_checkbox').addEventListener('change', function () {
                            
                              if (this.checked) {
                                    draggable.enable();
                                   selected_layers.forEach(function (layer, index) {
                                   draggable.enableForLayer(layer);
                                    });
                                  } else {
                                    draggable.disable();
                                  }

                            });
                            
                            
                            document.getElementById('layer_opacity').outerHTML = document.getElementById('layer_opacity').outerHTML;
                            document.getElementById('layer_opacity_label').innerHTML = "-";
                            document.getElementById('layer_opacity').addEventListener('input', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.opacity = parseInt( document.getElementById('layer_opacity').value )/100;
                                    document.getElementById('layer_opacity_label').innerHTML = document.getElementById('layer_opacity').value;
                                    layer.setStyle(layer.options);
                                    });
                            });
                            document.getElementById('layer_weight').outerHTML = document.getElementById('layer_weight').outerHTML;
                            document.getElementById('layer_weight_label').innerHTML = "-";
                            document.getElementById('layer_weight').addEventListener('input', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.weight = parseInt( document.getElementById('layer_weight').value );
                                    document.getElementById('layer_weight_label').innerHTML = document.getElementById('layer_weight').value;
                                    layer.setStyle(layer.options);
                                    });
                            });
                            
                            document.getElementById('layer_dash_array_1').addEventListener('click', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.dashArray = "1";
                                    layer.setStyle(layer.options);
                                    });
                            });
                            
                            document.getElementById('layer_dash_array_2').addEventListener('click', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.dashArray = '10';
                                    layer.setStyle(layer.options);
                                    });
                            });
                            
                            document.getElementById('layer_dash_array_3').addEventListener('click', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.dashArray = "15, 10, 1, 10";
                                    layer.setStyle(layer.options);
                                    });
                            });
                            
                            
                            if(layer_previous_options.fillColor==null){
                                    layer_previous_options.fillColor = 'blue';
                            }
                            picker_pozadie = new Picker({ //Zaciatok pickera
                                parent: document.querySelector('#zmena-pozadie'),
                                alpha: false,
                                popup: 'bottom',
                                cancelButton: false,
                                editor: false,
                                defaultColor: layer_previous_options.fillColor,
                                onChange: function(color) {
                                              document.querySelector('#zmena-pozadie').style.background = color.rgbaString;
                                              selected_layers.forEach(function (layer, index) {
                                                  layer.options.fillColor = color.rgbaString;
                                                  layer.setStyle(layer.options);
                                                });
                                              
                                          },
                            }); //Koniec pickera
                            
                            document.getElementById('layer_opacity_fill').outerHTML = document.getElementById('layer_opacity_fill').outerHTML;
                            document.getElementById('layer_opacity_label_fill').innerHTML = "-";
                            document.getElementById('layer_opacity_fill').addEventListener('input', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.fillOpacity = parseInt( document.getElementById('layer_opacity_fill').value )/100;
                                    document.getElementById('layer_opacity_label_fill').innerHTML = document.getElementById('layer_opacity_fill').value;
                                    layer.setStyle(layer.options);
                                    });
                            });
                            
                            document.getElementById('style_reset_button').outerHTML = document.getElementById('style_reset_button').outerHTML;
                            document.getElementById('style_reset_button').addEventListener('click', function (event) {
                                    selected_layers.forEach(function (layer, index) {                                 
                                    layer.setStyle(layer.previous_options);
                                    
                            document.getElementById('layer_opacity_label').innerHTML = "-";
                            document.getElementById('layer_weight_label').innerHTML = "-";
                            document.getElementById('zmena-farby').style.backgroundColor = "white";
                            document.getElementById('zmena-pozadie').style.backgroundColor = "white";
                            document.getElementById('layer_opacity_label_fill').innerHTML = "-";
                            parent.posledne_html_z_editora = html_pred_zmenou;
                                    });
                            });
                            
                            
                            btn.state('zoom-to-school');    // change state on click!
                        }
                    }, {
                        stateName: 'zoom-to-school',
                        icon:      'fa-floppy-disk',
                        title:     'Uložiť',
                        onClick: function(btn, map) {
                            {{ this._parent.get_name() }}.eachLayer(function (layer) { 
                            if(layer.upraveny && layer.upraveny==true){
                            
                                    if(parent.posledne_html_z_editora != html_pred_zmenou && parent.posledne_html_z_editora !=""  ){
                                        html_pred_zmenou = ""; //Ponechavam si editor html
                                    }
                                    else{
                                        parent.posledne_html_z_editora = "";
                                        html_pred_zmenou = "";
                                    }
                                    
                                    let layer2 = L.polygon(layer.getLatLngs());
                                    layer.upraveny=false;
                                    //console.log(layer);
                                    coord_update(parent.posledne_html_z_editora,layer.feature.geometry,layer.feature.geometry.serverID,layer2.toGeoJSON().geometry.coordinates,JSON.parse(JSON.stringify(layer.options)));
                                }
                            });
                            textbox_edit_1.remove();
                            textbox_edit_2.remove();
                            parent.posledne_html_z_editora = "";
                            picker_pozadie.destroy();
                            draggable.disable();
                            picker.destroy();
                            StyleEditor.hide();
                            btn.state('zoom-to-forest');
                            //vratit html elementy do povodneho stavu
                            document.getElementById('draggable_checkbox').outerHTML = document.getElementById('draggable_checkbox').outerHTML;
                            document.getElementById('layer_opacity').outerHTML = document.getElementById('layer_opacity').outerHTML;
                            document.getElementById('layer_opacity_label').innerHTML = "-";
                            document.getElementById('layer_weight').outerHTML = document.getElementById('layer_weight').outerHTML;
                            document.getElementById('layer_weight_label').innerHTML = "-";
                            document.getElementById('zmena-farby').style.backgroundColor = "white";
                            document.getElementById('zmena-pozadie').style.backgroundColor = "white";
                            document.getElementById('layer_opacity_fill').outerHTML = document.getElementById('layer_opacity_fill').outerHTML;
                            document.getElementById('layer_opacity_label_fill').innerHTML = "-";
                        }
                }]
        });

stateChangingButton.addTo( {{ this._parent.get_name() }} );



//Tu začína mazanie
    var textbox_ako_klasa   = L.Control.extend({
        onAdd: function() {
            
        var text = L.DomUtil.create('div');
        text.id = "info_text_delete";
        text.innerHTML = '<h1 style="color: red;font-size: 50px;">' + 'Režim mazania !' + "</h1>"
        return text;
        },

    });
    var textbox_delete_1 = new textbox_ako_klasa({ position: 'bottomright' });
    var textbox_delete_2 = new textbox_ako_klasa({ position: 'bottomleft' });
    
    
async function delete_layer_server(id) {
      let user = {
      id_objektu: id,
      admin_delete_objekt: null
    };

    let response = await fetch('/api', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8'
      },
      body: JSON.stringify(user)
    });
    
    if(response.status==201){
        alert("Objekt úspešne zmazaný");
    }
    else{
        alert("Niekde nastala chyba, prosím skúste znovu");
    }
        return true;
}
    
var customIcon = L.Icon.extend({
    options: {
        iconSize: [40.4, 44],
        iconAnchor: [20, 43],
        popupAnchor: [0, -51]
    }
});

var customIcon_default = L.Icon.extend({
    options: {
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34]
    }
});

var delete_ikona = new customIcon({ iconUrl: '/static/administration/skull-solid.png' });
var default_ikona = new customIcon_default({ iconUrl: 'https://unpkg.com/leaflet@1.5.1/dist/images/marker-icon.png' });

function delete_funkcia_prvy_klik(layer){
    layer.off('click');
    layer.na_zmazanie = true;
    if(layer.feature.geometry.type === "Point"){
        layer.setIcon(delete_ikona);
    }
    else{
        layer.style_stary = JSON.parse(JSON.stringify(layer.options));
        layer.setStyle({fillColor: 'grey',color: 'grey'});
    }
    layer.on('click',function(e) {delete_funkcia_druhy_klik(layer)});
    return true;
}

function delete_funkcia_druhy_klik(layer){
    layer.off('click');
    layer.na_zmazanie = false;
    if(layer.feature.geometry.type === "Point"){
        layer.setIcon(    default_ikona     );  
    }
    else{
    layer.setStyle(layer.style_stary);
    }
    layer.on('click',function(e) {delete_funkcia_prvy_klik(layer)});
    return true;
}
    
var stateChangingButton_delete = L.easyButton({
    states: [{
            stateName: 'zoom-to-delete',        // name the state
            icon:      'fa-trash-can',               // and define its properties
            title:     'Zmazať',      // like its title
            onClick: function(btn, map) {       // and its callback
                  textbox_delete_1.addTo( {{ this._parent.get_name() }} );
                  textbox_delete_2.addTo( {{ this._parent.get_name() }} );
                  
                  
                {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                        if(layer.feature){
                        
                            layer.on('click',function(e) {delete_funkcia_prvy_klik(layer)});
                            
                         
                        }                             
                }); //Koniec označenia vrsiev
                  
                  
                btn.state('zoom-to-school');    // change state on click!
            }
        }, {
            stateName: 'zoom-to-school',
            icon:      'fa-save',
            title:     'Uložiť',
            onClick: function(btn, map) {
                textbox_delete_1.remove();
                textbox_delete_2.remove();
                let vrstvy_na_zmazanie_server_delete = [];
                {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                        if(layer.feature){
                            layer.off('click');  
                           if(layer.na_zmazanie == true) {
                                vrstvy_na_zmazanie_server_delete.push(layer.feature.geometry.serverID);
                                layer.remove();
                           }
                                  
                        }                             
                }); //Koniec označenia vrsiev
                if (typeof vrstvy_na_zmazanie_server_delete !== 'undefined' && vrstvy_na_zmazanie_server_delete.length > 0) {
                        delete_layer_server(vrstvy_na_zmazanie_server_delete);
                }
                btn.state('zoom-to-delete');
            }
    }]
});

// stateChangingButton_delete.addTo( {{ this._parent.get_name() }} ); //Aktuálne chcem, aby sa dalo mazať iba po jednom

//Začiatok iframe obchdázania

            var SingleStyleEditorContent = `
        <style>
            .leaflet-styleeditor-stroke {
                height: 20px;
                width: 150px;
                background-repeat: no-repeat;
                border: 1px solid white;
                background-image: url("static/administration/dash_array.png");
                cursor: pointer;
            }
            .leaflet-styleeditor-stroke:hover {
                border: 1px solid black;
            }

        </style>
        
        <div style="height:500px; width:300px;" class="content-hlavny">
        
        <label id="Singledraggable_checkbox_label">Editor tvaru</label>
        <input type="checkbox" id="Singledraggable_checkbox" min="0" max="100" />
        <br>
        
        <b>Farba hrany: </b> <div id="Singlezmena-farby" style="width:25px;height:25px;border: 1px solid black;"></div>
        <br>
        
        <b>Viditeľnosť hrany: </b> <br>
        <label id="Singlelayer_opacity_label">-</label>
        <input type="range" id="Singlelayer_opacity" min="0" max="100" />
        
                <br>
        <b>Hrúbka hrany: </b> <br>
        <label id="Singlelayer_weight_label">-</label>
        <input type="range" id="Singlelayer_weight" min="0" max="30" />
                        <br>
        <b>Orámovanie hrany: </b> <br>
        <div id="Singlelayer_dash_array_1" class="leaflet-styleeditor-stroke" style="background-position: 0px -75px;"></div>
        <div id="Singlelayer_dash_array_2" class="leaflet-styleeditor-stroke" style="background-position: 0px -95px;"></div>
        <div id="Singlelayer_dash_array_3" class="leaflet-styleeditor-stroke" style="background-position: 0px -115px;"></div>
        <br>
        
        <b>Farba pozadia: </b> <div id="Singlezmena-pozadie" style="width:25px;height:25px;border: 1px solid black;"></div>
        <br>
        
        <b>Viditeľnosť pozadia: </b> <br>
        <label id="Singlelayer_opacity_label_fill">-</label>
        <input type="range" id="Singlelayer_opacity_fill" min="0" max="100" />
        <br>
        <button style="margin: 0px;margin-left: 8px;" onclick="parent.uprava_html()" type=button>Uprava-HTML</button>
        <br>
        <button style="margin-bottom: 0px;padding-bottom: 0px;margin-top: 0px;padding-top: 0px;" id="Singlestyle_reset_button"type="button">Resetovať</button>
        <br>
        <button style="margin-top: 0px;padding-top: 0px;" id="Singlestyle_apply_button"type="button" onclick="uprav_vrstvu_uloz_iframe();" >Uložiť zmeny</button>
        
        </div>
        `;
        var SingleStyleEditor = L.control.window({{ this._parent.get_name() }},{title:'',content:SingleStyleEditorContent,
        visible: false,
        maxWidth: 650,
        position: 'topRight',
        prompt: {callback:function(){
    //alert('Chellou!');
    
        //koniec funkcie
        }
    ,buttonOK:'  '} //Po stlačení button OK zmizne celé okno, zrejme bude treba dorobiť iný button, zrejme ho treba prevytvoriť
        });
        SingleStyleEditor.disableBtn();
        

        
        var Singlepicker;
        var Singlepicker_pozadie;


function uprav_vrstvu(id_vrstvy){
        if(id_vrstvy == ''){return;}
        
                stateChangingButton.disable();   
                stateChangingButton_delete.disable();
                let Singlelayer;
                draggable.disable();
                let layer_previous_options;
    
        {{ this._parent.get_name() }}.eachLayer(function (layer) { 
        if(layer.feature && (layer.feature.geometry.podskupina_spravca == '{{ this.username }}' || layer.feature.geometry.zdielane_w == true)  ){
        
        if(layer.feature.geometry.type === "Point"){return;}
        
        if(  id_vrstvy ==  layer.feature.geometry.serverID ) { 
                
            layer.upraveny = true
            layer.previous_options = JSON.parse(JSON.stringify(layer.options)); 
            layer_previous_options = JSON.parse(JSON.stringify(layer.options));
            html_pred_zmenou = layer.feature.geometry.popup_HTML;
            Singlelayer = layer;
                             
         }
         
        }                             
    }); //Koniec označenia vrsiev
    
    SingleStyleEditor.addEventListener("hide", function() {
        stateChangingButton.enable();   
        stateChangingButton_delete.enable();
        Singlelayer.setStyle(layer_previous_options);
    });
    
    parent.posledne_html_z_editora = html_pred_zmenou; 
    SingleStyleEditor.show();
    Singlepicker = new Picker({ //Zaciatok pickera
    parent: document.querySelector('#Singlezmena-farby'),
    alpha: false,
    popup: 'bottom',
    cancelButton: false,
    editor: false,
    defaultColor: layer_previous_options.color,
    onChange: function(color) {
                  document.querySelector('#Singlezmena-farby').style.background = color.rgbaString;
                    Singlelayer.options.color = color.rgbaString;
                    Singlelayer.setStyle(Singlelayer.options);
                  
              },
    }); //Koniec pickera     
    document.getElementById('Singledraggable_checkbox').outerHTML = document.getElementById('Singledraggable_checkbox').outerHTML;
    
    document.getElementById('Singledraggable_checkbox').addEventListener('change', function () {
    
      if (this.checked) {
            draggable.enable();
           draggable.enableForLayer(Singlelayer);
          } else {
            draggable.disable();
          }

    });  
    
    document.getElementById('Singlelayer_opacity').outerHTML = document.getElementById('Singlelayer_opacity').outerHTML;
    document.getElementById('Singlelayer_opacity_label').innerHTML = "-";
    
    document.getElementById('Singlelayer_opacity').addEventListener('input', function (event) {
    
        Singlelayer.options.opacity = parseInt( document.getElementById('Singlelayer_opacity').value )/100;
        document.getElementById('Singlelayer_opacity_label').innerHTML = document.getElementById('Singlelayer_opacity').value;
        Singlelayer.setStyle(Singlelayer.options);

});

document.getElementById('Singlelayer_weight').outerHTML = document.getElementById('Singlelayer_weight').outerHTML;
document.getElementById('Singlelayer_weight_label').innerHTML = "-";
document.getElementById('Singlelayer_weight').addEventListener('input', function (event) {

        Singlelayer.options.weight = parseInt( document.getElementById('Singlelayer_weight').value );
        document.getElementById('Singlelayer_weight_label').innerHTML = document.getElementById('Singlelayer_weight').value;
        Singlelayer.setStyle(Singlelayer.options);

});

document.getElementById('Singlelayer_dash_array_1').addEventListener('click', function (event) {

        Singlelayer.options.dashArray = "1";
        Singlelayer.setStyle(Singlelayer.options);

});

document.getElementById('Singlelayer_dash_array_2').addEventListener('click', function (event) {

        Singlelayer.options.dashArray = '10';
        Singlelayer.setStyle(Singlelayer.options);

});

document.getElementById('Singlelayer_dash_array_3').addEventListener('click', function (event) {

        Singlelayer.options.dashArray = "15, 10, 1, 10";
        Singlelayer.setStyle(Singlelayer.options);

});
    
    
if(layer_previous_options.fillColor==null){
        layer_previous_options.fillColor = 'blue';
}

Singlepicker_pozadie = new Picker({ //Zaciatok pickera
    parent: document.querySelector('#Singlezmena-pozadie'),
    alpha: false,
    popup: 'bottom',
    cancelButton: false,
    editor: false,
    defaultColor: layer_previous_options.fillColor,
    onChange: function(color) {
                  document.querySelector('#Singlezmena-pozadie').style.background = color.rgbaString;
                  
                      Singlelayer.options.fillColor = color.rgbaString;
                      Singlelayer.setStyle(Singlelayer.options);

                  
              },
}); //Koniec pickera


document.getElementById('Singlelayer_opacity_fill').outerHTML = document.getElementById('Singlelayer_opacity_fill').outerHTML;
document.getElementById('Singlelayer_opacity_label_fill').innerHTML = "-";
document.getElementById('Singlelayer_opacity_fill').addEventListener('input', function (event) {
        Singlelayer.options.fillOpacity = parseInt( document.getElementById('Singlelayer_opacity_fill').value )/100;
        document.getElementById('Singlelayer_opacity_label_fill').innerHTML = document.getElementById('Singlelayer_opacity_fill').value;
        Singlelayer.setStyle(Singlelayer.options);
});


document.getElementById('Singlestyle_reset_button').outerHTML = document.getElementById('Singlestyle_reset_button').outerHTML;

document.getElementById('Singlestyle_reset_button').addEventListener('click', function (event) {
                                 
        Singlelayer.setStyle(Singlelayer.previous_options);
        
        document.getElementById('Singlelayer_opacity_label').innerHTML = "-";
        document.getElementById('Singlelayer_weight_label').innerHTML = "-";
        document.getElementById('Singlezmena-farby').style.backgroundColor = "white";
        document.getElementById('Singlezmena-pozadie').style.backgroundColor = "white";
        document.getElementById('Singlelayer_opacity_label_fill').innerHTML = "-";
        parent.posledne_html_z_editora = html_pred_zmenou;

});

}
function uprav_vrstvu_uloz_iframe(){
                            {{ this._parent.get_name() }}.eachLayer(function (layer) { 
                            if(layer.upraveny && layer.upraveny==true){
                            
                                    if(parent.posledne_html_z_editora != html_pred_zmenou && parent.posledne_html_z_editora !=""  ){
                                        html_pred_zmenou = ""; //Ponechavam si editor html
                                    }
                                    else{
                                        parent.posledne_html_z_editora = "";
                                        html_pred_zmenou = "";
                                    }
                                    
                                    let layer2 = L.polygon(layer.getLatLngs());
                                    layer.upraveny=false;
                                    coord_update(parent.posledne_html_z_editora,layer.feature.geometry,layer.feature.geometry.serverID,layer2.toGeoJSON().geometry.coordinates,JSON.parse(JSON.stringify(layer.options)));
                                    layer.options_before_commit = JSON.parse(JSON.stringify(layer.options))
                                    layer.commit=true;
                                }
                            });
                            parent.posledne_html_z_editora = "";
                            Singlepicker_pozadie.destroy();
                            draggable.disable();
                            Singlepicker.destroy();
                            SingleStyleEditor.hide();
                            
                            stateChangingButton.enable();   
                            stateChangingButton_delete.enable();
                            
                            
                            
                            //vratit html elementy do povodneho stavu
                            document.getElementById('Singledraggable_checkbox').outerHTML = document.getElementById('Singledraggable_checkbox').outerHTML;
                            document.getElementById('Singlelayer_opacity').outerHTML = document.getElementById('Singlelayer_opacity').outerHTML;
                            document.getElementById('Singlelayer_opacity_label').innerHTML = "-";
                            document.getElementById('Singlelayer_weight').outerHTML = document.getElementById('Singlelayer_weight').outerHTML;
                            document.getElementById('Singlelayer_weight_label').innerHTML = "-";
                            document.getElementById('Singlezmena-farby').style.backgroundColor = "white";
                            document.getElementById('Singlezmena-pozadie').style.backgroundColor = "white";
                            document.getElementById('Singlelayer_opacity_fill').outerHTML = document.getElementById('Singlelayer_opacity_fill').outerHTML;
                            document.getElementById('Singlelayer_opacity_label_fill').innerHTML = "-";
                            
                            
                            {{ this._parent.get_name() }}.eachLayer(function (layer) { 
                            if(layer.commit && layer.commit==true){
                                         layer.setStyle(layer.options_before_commit);
                                         
                                         
                                }
                            });
                            

                            alert("Zmeny úspešne uložené");


}        
        function zmaz_vrstvu(id_vrstvy){
                
                if(id_vrstvy == ''){ return null;}
                let okno_zmaz_vrstvu = L.control.window({{ this._parent.get_name() }},{title:'Zmazanie vrstvy',content:'Naozaj chcete zmazať túto vrstvu ?',visible: true})
                okno_zmaz_vrstvu.prompt({
                    buttonOK: 'Áno',
                    callback: function(){
                    
                    let Singlelayer;
            {{ this._parent.get_name() }}.eachLayer(function (layer) { 
        if(layer.feature && (layer.feature.geometry.podskupina_spravca == '{{ this.username }}' || layer.feature.geometry.zdielane_w == true)  ){

        if(  id_vrstvy ==  layer.feature.geometry.serverID ) {      
            Singlelayer = layer;                 
         }
         
        }                             
    }); 
        Singlelayer.remove();
        delete_layer_server([Singlelayer.feature.geometry.serverID]);
                    
                    
                    },
                    buttonCancel: 'Nie',
                
                });
                
        }
        
        {% endmacro %}
        """
    )

    default_js = [
        (
            "leaflet.geometryutil.js",
            "https://unpkg.com/leaflet-geometryutil@0.10.2/src/leaflet.geometryutil.js",
        ),
        (
            "L.DraggableLines.min.js",
            "https://cdn.jsdelivr.net/npm/leaflet-draggable-lines@1.2.1/dist/L.DraggableLines.min.js",
        ),
        (
            "easy-button.js",
            "https://cdn.jsdelivr.net/npm/leaflet-easybutton@2/src/easy-button.js",
        ),
        (
            "L.Control.Window.js",
            "https://rawgit.com/mapshakers/leaflet-control-window/master/src/L.Control.Window.js",
        ),
        (
            "vanilla-picker.min.js",
            "https://cdn.jsdelivr.net/npm/vanilla-picker@2.12.2/dist/vanilla-picker.min.js",
        ),
    ]
    default_css = [
        (
            "easy-button.css",
            "https://cdn.jsdelivr.net/npm/leaflet-easybutton@2/src/easy-button.css",
        ),
        (
            "L.Control.Window.css",
            "https://rawgit.com/mapshakers/leaflet-control-window/master/src/L.Control.Window.css",
        ),
        (
            "vanilla-picker.csp.min.css",
            "https://cdn.jsdelivr.net/npm/vanilla-picker@2.12.2/dist/vanilla-picker.csp.min.css",
        )
    ]


    def __init__(
        self,username

    ):
        super().__init__()
        self.username = username
