from django_unicorn.components import UnicornView
from map.models import Notifikacie


class NavbarBellIconCountView(UnicornView):
    notifications_unread_count = 0

    def mount(self):
        kwarg = self.component_kwargs
        if self.request.user.is_authenticated:
            self.notifications_unread_count = len(Notifikacie.objects.all().filter(prijimatel=self.request.user))

    def update(self):
        self.notifications_unread_count = len(Notifikacie.objects.all().filter(prijimatel=self.request.user))
