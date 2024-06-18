import json

from django_unicorn.components import UnicornView

from map.models import Diskusia_skupiny, Diskusny_prispevok_skupiny, Profile, Diskusny_prispevok_skupiny_komentar, Skupiny


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
        diskusia = Diskusia_skupiny.objects.get(id = self.diskusia_id)
        skupina = Skupiny.objects.get(diskusia=diskusia)
        uzi = self.request.user.username #dlhe
        for prispevok in Diskusny_prispevok_skupiny.objects.filter(diskusia = Diskusia_skupiny.objects.get(id = self.diskusia_id)):
            karma = self.zisti_karmu(prispevok.karma)
            upvoted = False
            downvoted = False
            moderator = False
            if uzi == skupina.spravca or "w" in diskusia.uzivatelia.get(uzi, "") or prispevok.user == self.request.user:
                moderator = True
            if self.request.user.username in prispevok.karma:
                if prispevok.karma[self.request.user.username] == "+":
                    upvoted = True
                elif prispevok.karma[self.request.user.username] == "-":
                    downvoted = True
            self.prispevky.append(  (prispevok, Profile.objects.get(user=prispevok.user),karma,upvoted,downvoted,moderator ) )

    def zisti_karmu(self,karmy):
        karma = 0
        for x in list(karmy.values()):
            if x =='+':
                karma+=1
            elif x=='-':
                karma-=1
        return karma

    def hlasuj_karma_prispevok(self,data):
        data = json.loads(data)
        prispevok = Diskusny_prispevok_skupiny.objects.get(id=data['id'])
        karma = ""
        if data['action'] == "upvote":
            karma = "+"
        elif data['action'] == "downvote":
            karma = "-"
        prispevok.karma[self.request.user.username] = karma
        prispevok.save()

    def zmaz_prispevok(self,prispevok_id):
        prispevok = Diskusny_prispevok_skupiny.objects.get(id=prispevok_id)
        for komentar in Diskusny_prispevok_skupiny_komentar.objects.filter(prispevok = prispevok):
            komentar.delete()
        prispevok.delete()

    def zmaz_komentar(self,komentar_id):
        komentar = Diskusny_prispevok_skupiny_komentar.objects.get(id = komentar_id)
        komentar.delete()


