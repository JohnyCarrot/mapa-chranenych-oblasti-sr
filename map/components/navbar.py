from django.contrib.auth.models import User
from map.models import Notifikacie, Profile
from django_unicorn.components import UnicornView


class NavbarView(UnicornView):
    notifications_unread = []
    def mount(self):
        kwarg = self.component_kwargs
        if self.request.user.is_authenticated:
            self.ziskaj_notifikacie()

    def ziskaj_notifikacie(self):
        self.notifications_unread.clear()
        for notifikacia in Notifikacie.objects.all().filter(prijimatel=self.request.user,videne=False):
            if notifikacia.odosielatel.is_authenticated:
                self.notifications_unread.append(  (notifikacia, Profile.objects.get(user=notifikacia.odosielatel) )  )
            else:
                self.notifications_unread.append( (notifikacia, None ) )

    def update(self):
        self.ziskaj_notifikacie()

    def videne(self,id):
        notifikacia = Notifikacie.objects.get(pk=id)
        notifikacia.videne  =True
        notifikacia.save()
        self.ziskaj_notifikacie()

    def clear(self):
        for notifikacia in Notifikacie.objects.all().filter(prijimatel=self.request.user,videne=False):
            notifikacia.videne = True
            notifikacia.save()
        self.ziskaj_notifikacie()








