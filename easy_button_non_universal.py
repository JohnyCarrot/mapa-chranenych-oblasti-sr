from branca.element import MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin
from folium.utilities import parse_options


class EasyButton(JSCSSMixin, MacroElement):
    """
     Nie univerzálne implementovaný leaflet plugin :)

 https://github.com/CliffCloud/Leaflet.EasyButton/tree/master



    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        
                //Vypnutie legendy ak je False
                
                {% if not this.legenda %}
                        {{ this._parent.get_name() }}.legenda.collapse();
                {% endif %}    
                //Vypnutie legendy ak je False Koniec
                
                
                //Vsetky vrstvy do poľa, aby bolo možné ich neskôr po filtrovaní znovu pridať
                var vsetky_vrstvy_v_mape = [];
                {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                        if(layer.feature){
                            vsetky_vrstvy_v_mape.push(layer);
                            //console.log(layer.feature.geometry.stupen_ochrany);
                            
                            {% if not this.stupen2 %}
                                    if(layer.feature.geometry.stupen_ochrany==2){layer.remove();}
                            {% endif %}  
                            {% if not this.stupen3 %}
                                    if(layer.feature.geometry.stupen_ochrany==3){layer.remove();}
                            {% endif %} 
                            {% if not this.stupen4 %}
                                    if(layer.feature.geometry.stupen_ochrany==4){layer.remove();}
                            {% endif %} 
                            {% if not this.stupen5 %}
                                    if(layer.feature.geometry.stupen_ochrany==5){layer.remove();}
                            {% endif %} 
                            
                            
                          }                             
                }); //Koniec označenia vrsiev
                {{ this._parent.get_name() }}.vsetky_vrstvy = vsetky_vrstvy_v_mape;
                
                //Koniec Vrstiev do poľa
                
        
                async function foo(stupen2,stupen3,stupen4,stupen5,legendA) {
                  let user = {
                  stupen2: stupen2,
                  stupen3: stupen3,
                  stupen4: stupen4,
                  stupen5: stupen5,
                  legendA: legendA
                };
                
                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });
                
                let result = await response;
                
                if (response.status === 202) {
                    if(legendA){
                        {{ this._parent.get_name() }}.legenda.expand();
                    }
                    else{
                        {{ this._parent.get_name() }}.legenda.collapse();
                    }
                
                
                
                
                    {{ this._parent.get_name() }}.eachLayer(function (layer) { //Označ vrstvy pre zobrazenie
                        if(layer.feature){
                            let stupen = layer.feature.geometry.stupen_ochrany;
                            if(stupen==2 || stupen ==3 || stupen==4 || stupen==5){
                                layer.remove();
                            }
                          }                             
                    }); //Koniec označenia vrsiev
                    
                    vsetky_vrstvy_v_mape.forEach(layer => {
                        let stupen = layer.feature.geometry.stupen_ochrany;
                            if(stupen==2 && stupen2){
                                layer.addTo({{ this._parent.get_name() }});
                            }
                            if(stupen==3 && stupen3){
                                layer.addTo({{ this._parent.get_name() }});
                            }
                            if(stupen==4 && stupen4){
                                layer.addTo({{ this._parent.get_name() }});
                            }
                            if(stupen==5 && stupen5){
                                layer.addTo({{ this._parent.get_name() }});
                            }
                    });
                
                
                
                
                //alert('Zmeny úspešne aplikované!'); //Je to otravné
                  

                } else {
                  alert(`Niekde nastala chyba, skúste neskôr: Status ${response.status}`);
                }
                    
           return true;
        }
            var content = `
            <form id="settings-form" onsubmit="return false">
            <h4>Stupne ochrany</h4>
<div class="form-check form-check-inline">
  <input class="form-check-input" type="checkbox" id="stupen2" value="option1" {{ 'checked' if this.stupen2 else '' }}>
  <label class="form-check-label" for="stupen2">II. stupeň</label>
</div>
<div class="form-check form-check-inline">
  <input class="form-check-input" type="checkbox" id="3stupen" value="option2" {{ 'checked' if this.stupen3 else '' }}>
  <label class="form-check-label" for="3stupen">III. stupeň</label>
</div>
<div class="form-check form-check-inline">
  <input class="form-check-input" type="checkbox" id="4stupen" value="option3" {{ 'checked' if this.stupen4 else '' }}>
  <label class="form-check-label" for="4stupen">IV. stupeň</label>
</div>
<div class="form-check form-check-inline">
  <input class="form-check-input" type="checkbox" id="5stupen" value="option3" {{ 'checked' if this.stupen5 else '' }}>
  <label class="form-check-label" for="5stupen">V. stupeň</label>
</div>
<hr>
<h4>Legenda</h4>
<div class="form-check-inline">
  <input class="form-check-input" type="checkbox" value="" id="LegendActive" {{ 'checked' if this.legenda else '' }}>
  <label class="form-check-label" for="LegendActive">
    Aktívna
  </label>
</div>
<hr>
<button class="btn btn-primary" onclick="foo(document.getElementById('stupen2').checked,document.getElementById('3stupen').checked,document.getElementById('4stupen').checked,document.getElementById('5stupen').checked,document.getElementById('LegendActive').checked);">Aplikovať</button>
</form>





            
            
            `;
    var win =  L.control.window({{ this._parent.get_name() }}, {title:'Nastavenia', modal: false});
    win.content(content)
    .prompt({callback:function(){    
    },buttonOK:'     '})
    .hide().disableBtn();
            var stateChangingButton = L.easyButton({
                position: 'bottomleft',
                states: [{
                        stateName: 'settings',        // name the state
                        icon:      'fa-cog',               // and define its properties
                        title:     'Nastavenia',      // like its title
                        onClick: function(btn, map) {       // and its callback
                              
                                win.show();
                        }
                    }]
            });
            stateChangingButton.addTo({{ this._parent.get_name() }});

        {% endmacro %}
    """
    )

    default_js = [
        (
            "easy-button.js",
            "https://cdn.jsdelivr.net/npm/leaflet-easybutton@2/src/easy-button.js",
        ),
        (
            "L.Control.Window.js",
            "https://rawgit.com/mapshakers/leaflet-control-window/master/src/L.Control.Window.js",
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
        )
    ]

    def __init__(self, stupen2,stupen3,stupen4,stupen5,legenda,**kwargs):
        super().__init__()
        self._name = "EasyButton"
        self.stupen2 = stupen2
        self.stupen3 = stupen3
        self.stupen4 = stupen4
        self.stupen5 = stupen5
        self.legenda = legenda

