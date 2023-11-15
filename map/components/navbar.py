from django.contrib.auth.models import User
from map.models import Notifikacie
from django_unicorn.components import UnicornView


class NavbarView(UnicornView):
    notifications_unread = []
    def mount(self):
        kwarg = self.component_kwargs
        if self.request.user.is_authenticated:
            self.notifications_unread = Notifikacie.objects.all().filter(prijimatel=self.request.user,videne=False)

    def update(self):
        self.notifications_unread = Notifikacie.objects.all().filter(prijimatel=self.request.user,videne=False)

    def videne(self,id):
        notifikacia = Notifikacie.objects.get(pk=id)
        notifikacia.videne  =True
        notifikacia.save()
        self.notifications_unread = Notifikacie.objects.all().filter(prijimatel=self.request.user,videne=False)

    def clear(self):
        for notifikacia in Notifikacie.objects.all().filter(prijimatel=self.request.user,videne=False):
            notifikacia.videne = True
            notifikacia.save()
        self.notifications_unread = Notifikacie.objects.all().filter(prijimatel=self.request.user, videne=False)








