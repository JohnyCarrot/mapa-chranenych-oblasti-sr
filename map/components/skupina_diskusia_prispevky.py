
from django_unicorn.components import UnicornView

from map.models import Diskusia_skupiny, Diskusny_prispevok_skupiny, Profile, Diskusny_prispevok_skupiny_komentar


class SkupinaDiskusiaPrispevkyView(UnicornView):
    diskusia_id = ""
    ikonka_uzivatel_request = ""
    prispevky = []
    komentare = []
    mapa_html = ""
    def mount(self):
        self.diskusia_id = self.component_kwargs["diskusia_id"]
        self.nahraj_prispevky()
        self.ikonka_uzivatel_request = Profile.objects.get(user = self.request.user).icon
        self.nahraj_komentare()

    def nahraj_komentare(self):
        self.komentare.clear()
        for komentar in Diskusny_prispevok_skupiny_komentar.objects.all():
            self.komentare.append( (komentar,Profile.objects.get(user = komentar.user)) )
    def nahraj_prispevky(self):
        self.prispevky.clear()
        for prispevok in Diskusny_prispevok_skupiny.objects.filter(diskusia = Diskusia_skupiny.objects.get(id = self.diskusia_id)):
            self.prispevky.append(  (prispevok, Profile.objects.get(user=prispevok.user) ) )


