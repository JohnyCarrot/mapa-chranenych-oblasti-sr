from django.contrib.auth.models import User
from map.models import Notifikacie
from map.views import navbar_zapni_administraciu
from django_unicorn.components import UnicornView

class NavbarItemsView(UnicornView):
    administracia = False

    def mount(self):
        kwarg = self.component_kwargs
        if self.request.user.is_authenticated:
            self.administracia = navbar_zapni_administraciu(self.request.user)

    def update(self):
        self.administracia = navbar_zapni_administraciu(self.request.user)
