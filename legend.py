from branca.element import MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin
from folium.utilities import parse_options


class Legend(JSCSSMixin, MacroElement):
    """
https://github.com/mikeskaug/Leaflet.Legend?tab=readme-ov-file
    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        
        
L.Control.Legend.prototype.updateItems = function(items) {
    var container = this._container;
    container.innerHTML = '';  // Clear existing content
    var className = 'leaflet-legend';
    var list = L.DomUtil.create('div', 'leaflet-legend-list', container);
    items.forEach(function(item) {
        if (item.active == true){
                var div = L.DomUtil.create('div', className + '-item', list);
                var colorbox = L.DomUtil.create('div', className + '-color', div);
                colorbox.innerHTML = '&nbsp;';
                colorbox.style.backgroundColor = item.color;
                L.DomUtil.create('div', className + '-text', div).innerHTML = item.label;
        }
    });
    this.expand();  // Optionally expand the legend to show updated items
};
            
        
              var legenda =   L.control.legend({
            items: [
                {color: 'red', label: 'cervene'},
                {label: 'bez farby'},
                {color: 'blue', label: 'modre'}
            ],
            collapsed: false, //nastavenia v mape
            position: 'bottomright',
            buttonHtml: '<i class="fa fa-info" style="color: #000"></i>'
        });
        legenda.addTo({{this._parent.get_name()}});
        $('.leaflet-control-attribution').hide();
        var co_do_legendy = [];
        {% for x in this.legend %}
            co_do_legendy.push({color: '{{ x[1] }}', label: '{{ x[0] }}',active: true});
        {% endfor %}
        legenda.updateItems(co_do_legendy);
        
        {{this._parent.get_name()}}.on('overlayadd',function(e){
            co_do_legendy.forEach(element => {

                if (element.label == e.name) {
                                element.active = true;
                                legenda.updateItems(co_do_legendy);
                }
            });

        });
        
        {{this._parent.get_name()}}.on('overlayremove',function(e){
            co_do_legendy.forEach(element => {

                if (element.label == e.name) {
                                element.active = false;
                                legenda.updateItems(co_do_legendy);
                }
            });
        });
        
        
 
            
        {% endmacro %}
        """
    )

    default_js = [
        (
            "Legend.js",
            "https://cdn.jsdelivr.net/gh/zostera/leaflet-legend@master/leaflet-legend.js",
        )
    ]
    default_css = [
        (
            "Legend.css",
            "https://cdn.jsdelivr.net/gh/zostera/leaflet-legend@master/leaflet-legend.css",
        )
    ]

    def __init__(
        self,
        legend=None,
        **kwargs
    ):
        super().__init__()
        self.legend = legend or []
        self._name = "Legend"
        self.options = parse_options(
            **kwargs
        )
