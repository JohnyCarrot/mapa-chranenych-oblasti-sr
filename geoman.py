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
        
        
        var geojsonFeature = {
                "type": "Feature",
                "properties": {
                    "name": "Coors Field",
                    "amenity": "Baseball Stadium",
                    "popupContent": "This is where the Rockies play!"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[ [18.177428,48.563215],[18.197428,48.583215],[19.127428,48.533215] ]]
                }
            };
        L.geoJSON(geojsonFeature).addTo({{ this._parent.get_name() }});

        
        
         var stateChangingButton = L.easyButton({
                states: [{
                        stateName: 'zoom-to-forest',        // name the state
                        icon:      'fa-pen-to-square',               // and define its properties
                        title:     'Upraviť',      // like its title
                        onClick: function(btn, map) {       // and its callback
                            draggable.enable();
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
        )
    ]
    default_css = [
        (
            "easy-button.css",
            "https://cdn.jsdelivr.net/npm/leaflet-easybutton@2/src/easy-button.css",
        )
    ]


    def __init__(
        self,

    ):
        super().__init__()
