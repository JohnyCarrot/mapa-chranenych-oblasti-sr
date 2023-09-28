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
        async function coord_update(geometry,id,update_pozicia) {
                  let user = {
                  id_objektu: id,
                  geometry: geometry,
                  update_pozicia: update_pozicia,
                  admin_coord_update: null
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
        <label id="draggable_checkbox_label">Editor tvaru</label>
        <input type="checkbox" id="draggable_checkbox" min="0" max="100" />
        <br>
        <b>Farba: </b> <br>
        <div style="height:500px; width:300px;" class="content-hlavny">
        <div id="zmena-farby">Zmena farby</div>
        <br>
        <b>Viditeľnosť: </b> <br>
        <label id="layer_opacity_label">-</label>
        <input type="range" id="layer_opacity" min="0" max="100" />
        
                <br>
        <b>Hrúbka: </b> <br>
        <label id="layer_weight_label">-</label>
        <input type="range" id="layer_weight" min="0" max="30" />
        </div>
        `;
        
        
        var StyleEditor = L.control.window({{ this._parent.get_name() }},{title:'',content:StyleEditorContent,
        visible: false,
        maxWidth: 650,
        position: 'topRight',
        prompt: {callback:function(){
    alert('Chellou!');
    
        //koniec funkcie
        }
    ,buttonOK:'Aplikovať'} //Po stlačení button OK zmizne celé okno, zrejme bude treba dorobiť iný button, zrejme ho treba prevytvoriť
        });
        
        var picker;
         var stateChangingButton = L.easyButton({
                states: [{
                        stateName: 'zoom-to-forest',        // name the state
                        icon:      'fa-pen-to-square',               // and define its properties
                        title:     'Upraviť',      // like its title
                        onClick: function(btn, map) {       // and its callback
                            draggable.disable();
                            StyleEditor.show();
                            let selected_layers = [];                                    
                                    {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                                            if(layer.feature){
                                            if(map.getBounds().contains( layer.getBounds().getCenter() )) { 
                                                layer.upraveny = true
                                                //draggable.enableForLayer(layer);
                                                selected_layers.push(layer);
                                                layer.previous_options = layer.options; //ked sa bude robit nas5 tlacidlo
                                                console.log(layer); //do budúcna ZMAZAŤ
                                                 
                                             }
                                             
                                            }                             
                                    }); //Koniec označenia vrsiev
                            picker = new Picker({ //Zaciatok pickera
                                parent: document.querySelector('#zmena-farby'),
                                alpha: false,
                                popup: 'bottom',
                                cancelButton: false,
                                editor: false,
                                onChange: function(color) {
                                              document.querySelector('#zmena-farby').style.background = color.rgbaString;
                                              selected_layers.forEach(function (layer, index) {
                                                  layer.options.fillColor = color.rgbaString;
                                                  layer.redraw();
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
                                    layer.redraw();
                                    });
                            });
                            document.getElementById('layer_weight').outerHTML = document.getElementById('layer_weight').outerHTML;
                            document.getElementById('layer_weight_label').innerHTML = "-";
                            document.getElementById('layer_weight').addEventListener('input', function (event) {
                                    selected_layers.forEach(function (layer, index) {
                                    layer.options.weight = parseInt( document.getElementById('layer_weight').value );
                                    document.getElementById('layer_weight_label').innerHTML = document.getElementById('layer_weight').value;
                                    layer.redraw();
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
                                    coord_update(layer.feature.geometry,layer.feature.geometry.serverID,layer2.toGeoJSON().geometry.coordinates);
                                }
                            });
                            draggable.disable();
                            picker.destroy();
                            StyleEditor.hide();
                            btn.state('zoom-to-forest');
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
