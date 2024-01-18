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
                karma = self.zisti_karmu(prispevok.karma)
                upvoted = False
                downvoted = False
                if self.request.user.username in prispevok.karma:
                    if prispevok.karma[self.request.user.username]=="+":
                        upvoted = True
                    elif prispevok.karma[self.request.user.username]=="-":
                        downvoted = True
                self.prispevky.append(  (prispevok,Profile.objects.get(user=prispevok.user),karma,upvoted,downvoted ) )

    def zisti_karmu(self,karmy):
        karma = 0
        for x in list(karmy.values()):
            if x =='+':
                karma+=1
            elif x=='-':
                karma-=1
        return karma