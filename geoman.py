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
        <b>Farba: </b> <br>
        <div style="height:500px; width:300px;" class="content-hlavny">
        <div id="zmena-farby">Click me</div>
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
    ,buttonOK:'Aplikovať'}
        });
        
        var picker;
         var stateChangingButton = L.easyButton({
                states: [{
                        stateName: 'zoom-to-forest',        // name the state
                        icon:      'fa-pen-to-square',               // and define its properties
                        title:     'Upraviť',      // like its title
                        onClick: function(btn, map) {       // and its callback
                            draggable.enable();
                            StyleEditor.show();
                            picker = new Picker({
                                parent: document.querySelector('#zmena-farby'),
                                alpha: false,
                                popup: 'bottom',
                                cancelButton: false,
                                editor: false,
                                onChange: function(color) {
                                              document.querySelector('#zmena-farby').style.background = color.rgbaString;
                                          },
                            });

                            
                                    {{ this._parent.get_name() }}.eachLayer(function (layer) { 
                                            if(layer.feature){
                                            if(map.getBounds().contains( layer.getBounds().getCenter() )) { 
                                                layer.upraveny = true
                                                draggable.enableForLayer(layer);
                                                 
                                             }
                                             
                                            }
                                            
                                              
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
