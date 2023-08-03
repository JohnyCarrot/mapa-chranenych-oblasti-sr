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
            var content = '<div>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</div>';

            var stateChangingButton = L.easyButton({
                position: 'bottomleft',
                states: [{
                        stateName: 'settings',        // name the state
                        icon:      'fa-cog',               // and define its properties
                        title:     'Nastavenia',      // like its title
                        onClick: function(btn, map) {       // and its callback
                              
                              var win =  L.control.window(map, {title:'Hello world!', maxWidth: 350, modal: false})
    .content(content)
    .prompt({callback:function(){alert('This is called after OK click!')}})
    .show()
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

    def __init__(self, **kwargs):
        super().__init__()
        self._name = "EasyButton"

