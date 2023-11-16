from branca.element import Element, Figure, MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin


class Draw_custom_admin(JSCSSMixin, MacroElement):
    """
    Vector drawing and editing plugin for Leaflet.

    Parameters
    ----------
    export : bool, default False
        Add a small button that exports the drawn shapes as a geojson file.
    filename : string, default 'data.geojson'
        Name of geojson file
    position : {'topleft', 'toprigth', 'bottomleft', 'bottomright'}
        Position of control.
        See https://leafletjs.com/reference.html#control
    show_geometry_on_click : bool, default True
        When True, opens an alert with the geometry description on click.
    draw_options : dict, optional
        The options used to configure the draw toolbar. See
        http://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#drawoptions
    edit_options : dict, optional
        The options used to configure the edit toolbar. See
        https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#editpolyoptions

    Examples
    --------
    >>> m = folium.Map()
    >>> Draw(
    ...     export=True,
    ...     filename="my_data.geojson",
    ...     position="topleft",
    ...     draw_options={"polyline": {"allowIntersection": False}},
    ...     edit_options={"poly": {"allowIntersection": False}},
    ... ).add_to(m)

    For more info please check
    https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html

    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        function random_uuid() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
                    return v.toString(16);
                });
        }
        var suradnice_global = "";
        var okno_global = L.control.window({{ this._parent.get_name() }},{title:'Neviditelne okno',content:'Gratulujem, práve vidíte neviditelné okno.',visible: false});
        var otvorene_okno = false;
                
                function praca_s_formularom(meno,podskupina_id) { //len testovacia funkcia
                            alert(meno + ' ' +podskupina_id);
                            return true;
                        }  
                        
                function value_elementu(id) {
                            return document.getElementById(id).value;
                    } 
        async function create_object(coords,meno,podskupina_id) {
        
                    if(meno.length ==0){
                    
                    alert("Názov objektu nesmie byť prázdny");
                    return true;
                    
                    }
        
                  let user = {
                  coords: coords,
                  meno: meno,
                  podskupina_id: podskupina_id,
                  admin_object_create: null
                };

                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });
                otvorene_okno = false;
                okno_global.close();
                           return true;
        }
            var options = {
              position: {{ this.position|tojson }},
              draw: {{ this.draw_options|tojson }},
              edit: {{ this.edit_options|tojson }},
            }
            // FeatureGroup is to store editable layers.
            var drawnItems_{{ this.get_name() }} = new L.featureGroup().addTo(
                {{ this._parent.get_name() }}
            );
            options.edit.featureGroup = drawnItems_{{ this.get_name() }};
            var {{ this.get_name() }} = new L.Control.Draw(
                options
            ).addTo( {{this._parent.get_name()}} );
            {{ this._parent.get_name() }}.on(L.Draw.Event.CREATED, function(e) {
                var layer = e.layer,
                    type = e.layerType;
                var coords = JSON.stringify(layer.toGeoJSON());
                {%- if this.show_geometry_on_click %}
                layer.on('click', function() {
                                    
                    if(otvorene_okno == false){
                                
                         let juju = random_uuid();           
                        suradnice_global = JSON.stringify(layer.toGeoJSON());
                      let style_editor_content = `
                      
                        
                          <label for="fname${juju}">Názov objektu:</label><br>
                          <input type="text" id="fname${juju}" name="fname${juju}"><br>
                            <label for="cars${juju}">Vyberte podskupinu:</label><br>
                            
                            <select name="cars${juju}" id="cars${juju}">
                            {% for podskupina in this.podskupiny %}
                              <option value="{{ podskupina.id }}">{{ podskupina.meno }}</option>               
                            {% endfor %}
                            </select>
                            <br>
                            <label for="stupne_ochrany${juju}">Vyberte stupeň ochrany:</label><br>
                            
                            <select name="stupne_ochrany${juju}" id="stupne_ochrany${juju}">
                              <option value="0">Nedefinované</option>     
                              <option value="2">2</option>
                              <option value="3">3</option>
                              <option value="4">4</option>
                              <option value="5">5</option>          
                            </select>
                            <br>
                        <label for="diskusia${juju}">Povoliť diskusiu:</label>
                          <input type="checkbox" id="diskusia${juju}" name="diskusia${juju}" checked><br>
                            
                            
                            <button onclick="parent.testament()" type=button>TEST1</button>
                            
                            
                            <br>
                            <br>
                            <button onclick="create_object(  suradnice_global,value_elementu('fname${juju}'),value_elementu('cars${juju}')  );" type="button">Uložiť</button>
                            
                            
                        
                      
                      
                      `;
                      okno_global = L.control.window({{ this._parent.get_name() }},{title:'Nový objekt',content:style_editor_content  }).show()
                      okno_global.addEventListener('hide', function (e) {
                                otvorene_okno = false;
                        });
                      otvorene_okno = true;
                      
                      
                      } //Koniec ifu na otvorene okno
                      
                      
                      else{alert('V jednom momente je možné pridávať iba jeden objekt');}
                        
                });
                {%- endif %}
                drawnItems_{{ this.get_name() }}.addLayer(layer);
             });
            {{ this._parent.get_name() }}.on('draw:created', function(e) {
                drawnItems_{{ this.get_name() }}.addLayer(e.layer);
            });
            {% if this.export %}
            document.getElementById('export').onclick = function(e) {
                var data = drawnItems_{{ this.get_name() }}.toGeoJSON();
                var convertedData = 'text/json;charset=utf-8,'
                    + encodeURIComponent(JSON.stringify(data));
                document.getElementById('export').setAttribute(
                    'href', 'data:' + convertedData
                );
                document.getElementById('export').setAttribute(
                    'download', {{ this.filename|tojson }}
                );
            }
            {% endif %}
        {% endmacro %}
        """
    )

    default_js = [

        (
            "L.Control.Window.js",
            "https://rawgit.com/mapshakers/leaflet-control-window/master/src/L.Control.Window.js",
        ),
        (
            "leaflet_draw_js",
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.2/leaflet.draw.js",
        )
    ]
    default_css = [

        (
            "L.Control.Window.css",
            "https://rawgit.com/mapshakers/leaflet-control-window/master/src/L.Control.Window.css",
        ),
        (
            "leaflet_draw_css",
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.2/leaflet.draw.css",
        )
    ]

    def __init__(
        self,
        export=False,
        filename="data.geojson",
        position="topleft",
        show_geometry_on_click=True,
        draw_options=None,
        edit_options=None,
        podskupiny=[]
    ):
        super().__init__()
        self.podskupiny = podskupiny
        self._name = "DrawControl"
        self.export = export
        self.filename = filename
        self.position = position
        self.show_geometry_on_click = show_geometry_on_click
        self.draw_options = draw_options or {}
        self.edit_options = edit_options or {}

    def render(self, **kwargs):
        super().render(**kwargs)

        figure = self.get_root()
        assert isinstance(
            figure, Figure
        ), "You cannot render this Element if it is not in a Figure."

        export_style = """
            <style>
                #export {
                    position: absolute;
                    top: 5px;
                    right: 10px;
                    z-index: 999;
                    background: white;
                    color: black;
                    padding: 6px;
                    border-radius: 4px;
                    font-family: 'Helvetica Neue';
                    cursor: pointer;
                    font-size: 12px;
                    text-decoration: none;
                    top: 90px;
                }
            </style>
        """
        export_button = """<a href='#' id='export'>Export</a>"""
        if self.export:
            figure.header.add_child(Element(export_style), name="export")
            figure.html.add_child(Element(export_button), name="export_button")
