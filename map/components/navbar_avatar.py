from django_unicorn.components import UnicornView

from map.models import Profile


class NavbarAvatarView(UnicornView):
    url=""
    profil_url = ""
    def mount(self):
        self.url = Profile.objects.get(user=self.request.user).icon
        self.profil_url = self.request.user.username
