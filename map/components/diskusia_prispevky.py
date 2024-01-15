import json

from django_unicorn.components import UnicornView
from map.models import Diskusia,Diskusny_prispevok,Profile

class DiskusiaPrispevkyView(UnicornView):
    prispevky = []
    id_diskusie = ""
    def mount(self):
        self.prispevky = []
        self.id_diskusie = ""
        if "q" in self.request.GET:
            self.id_diskusie = self.request.GET.get("q")

        if self.id_diskusie !="":
            diskusia = Diskusia.objects.get(id=self.id_diskusie)
            for prispevok in Diskusny_prispevok.objects.filter(diskusia=diskusia):
                self.prispevky.append(  (prispevok,Profile.objects.get(user=prispevok.user)) )


