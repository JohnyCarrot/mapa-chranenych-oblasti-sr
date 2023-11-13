from django.contrib.auth.models import User
from django_unicorn.components import UnicornView


class NavbarView(UnicornView):
    notifications_unread = []
    def mount(self):
        kwarg = self.component_kwargs
        self.notifications_unread = self.request.user.notifications.unread()



