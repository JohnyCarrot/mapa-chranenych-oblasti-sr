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
                async function foo(stupen2,stupen3,stupen4,stupen5) {
                  let user = {
                  stupen2: stupen2,
                  stupen3: stupen3,
                  stupen4: stupen4,
                  stupen5: stupen5
                };
                
                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });
                
                let result = await response.json();
                    
           return true;
        }
            var content = `
            <form id="settings-form">
            <h3>Stupne ochrany</h3>
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
<button class="btn btn-primary" onclick="foo(document.getElementById('stupen2').checked,document.getElementById('3stupen').checked,document.getElementById('4stupen').checked,document.getElementById('5stupen').checked);window.parent.location.href = '';alert('Zmeny úspešne aplikované!');">Aplikovať</button>
</form>





            
            
            `;
            var stateChangingButton = L.easyButton({
                position: 'bottomleft',
                states: [{
                        stateName: 'settings',        // name the state
                        icon:      'fa-cog',               // and define its properties
                        title:     'Nastavenia',      // like its title
                        onClick: function(btn, map) {       // and its callback
                              
                              var win =  L.control.window(map, {title:'Nastavenia', modal: false})
    .content(content)
    .prompt({callback:function(){
    window.parent.location.href = "",alert('Zmeny úspešne aplikované!')
    
    },buttonOK:'     '})
    .show().disableBtn()
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

    def __init__(self, stupen2,stupen3,stupen4,stupen5,**kwargs):
        super().__init__()
        self._name = "EasyButton"
        self.stupen2 = stupen2
        self.stupen3 = stupen3
        self.stupen4 = stupen4
        self.stupen5 = stupen5

