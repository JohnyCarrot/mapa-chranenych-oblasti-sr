from django.contrib.auth.models import User
from map.models import Notifikacie
from django_unicorn.components import UnicornView


class NavbarView(UnicornView):
    notifications_unread = []
    def mount(self):
        kwarg = self.component_kwargs
        if self.request.user.is_authenticated:
            self.notifications_unread = Notifikacie.objects.all().filter(prijimatel=self.request.user)

    def update(self):
        self.notifications_unread = Notifikacie.objects.all().filter(prijimatel=self.request.user)








