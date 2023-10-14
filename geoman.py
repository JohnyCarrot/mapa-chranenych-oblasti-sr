from branca.element import Element, Figure,MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin
from folium.utilities import parse_options


class Geoman(JSCSSMixin, MacroElement):

    _template = Template(
        """
        {% macro script(this, kwargs) %}
         const draggable = new L.DraggableLines({{ this._parent.get_name() }}, 
            {
	        enableForLayer: false
            });
        async function coord_update(geometry,id,update_pozicia,style) {
                  let user = {
                  id_objektu: id,
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
                            let layer_previous_options;
                            let selected_layers = [];                                    
                                    {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                                            if(layer.feature){
                                            if(map.getBounds().contains( layer.getBounds().getCenter() )) { 
                                                layer.upraveny = true
                                                //draggable.enableForLayer(layer);
                                                selected_layers.push(layer);
                                                layer.previous_options = JSON.parse(JSON.stringify(layer.options)); //ked sa bude robit nas5 tlacidlo
                                                layer_previous_options = JSON.parse(JSON.stringify(layer.options));
                                                console.log(layer); //do budúcna ZMAZAŤ
                                                 
                                             }
                                             
                                            }                             
                                    }); //Koniec označenia vrsiev
                            
                            if(selected_layers.length == 0){
                                alert("Neboli vybrané žiadne vrstvy");
                                return null;
                            }                            
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
                                    let layer2 = L.polygon(layer.getLatLngs());
                                    layer.upraveny=false;
                                    coord_update(layer.feature.geometry,layer.feature.geometry.serverID,layer2.toGeoJSON().geometry.coordinates,JSON.parse(JSON.stringify(layer.options)));
                                }
                            });
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
        self,

    ):
        super().__init__()
