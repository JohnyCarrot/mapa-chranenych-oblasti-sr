from django_unicorn.components import UnicornView
from map.models import Diskusia_skupiny, Diskusny_prispevok_skupiny, Profile

class SkupinaDiskusiaPrispevkyView(UnicornView):
    diskusia_id = ""
    prispevky = []
    def mount(self):
        self.diskusia_id = self.component_kwargs["diskusia_id"]
        self.nahraj_prispevky()


    def nahraj_prispevky(self):
        self.prispevky.clear()
        for prispevok in Diskusny_prispevok_skupiny.objects.filter(diskusia = Diskusia_skupiny.objects.get(id = self.diskusia_id)):
            self.prispevky.append(  (prispevok, Profile.objects.get(user=prispevok.user) ) )
