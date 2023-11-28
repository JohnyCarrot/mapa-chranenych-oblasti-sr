from django_unicorn.components import UnicornView
from django.contrib.auth.models import User
from friendship.models import Friend, Follow, Block,FriendshipRequest
from difflib import SequenceMatcher


class FriendsListView(UnicornView):

    zoznam_priatelov = []
    zoznam_priatelov_pocet = 0
    zoznam_ziadosti = []
    zoznam_ziadosti_pocet = 0
    priatelia_obsah = True
    ziadosti_obsah = False
    najst_priatelov_obsah = False
    hladane_osoby = [] #Osoby so search baru
    vyhladavacie_pole = ""
    def mount(self):
        self.zoznam_priatelov = Friend.objects.friends(self.request.user)
        self.zoznam_priatelov_pocet = len(self.zoznam_priatelov)
        self.priatelia_obsah = True

    def prepni_na_priatelov(self):
        self.zoznam_priatelov = Friend.objects.friends(self.request.user)
        self.zoznam_priatelov_pocet = len(self.zoznam_priatelov)
        self.priatelia_obsah = True
        self.ziadosti_obsah = False
        self.najst_priatelov_obsah = False

    def prepni_na_ziadosti(self):
        self.zoznam_ziadosti = Friend.objects.unrejected_requests(user=self.request.user)
        self.zoznam_ziadosti_pocet = len(self.zoznam_ziadosti)
        self.priatelia_obsah = False
        self.ziadosti_obsah = True
        self.najst_priatelov_obsah = False


    def prepni_na_najst_priatelov(self):
        self.hladane_osoby = []
        self.vyhladavacie_pole = ""
        self.priatelia_obsah = False
        self.ziadosti_obsah = False
        self.najst_priatelov_obsah = True


    def odmietni_ziadost(self,id):
        ziadost = FriendshipRequest.objects.get(id=id)
        ziadost.reject()
        self.prepni_na_ziadosti()

    def primi_ziadost(self,id):
        ziadost = FriendshipRequest.objects.get(id=id)
        ziadost.accept()
        self.prepni_na_ziadosti()

    def hladat_priatelov(self):
        self.hladane_osoby = []
        for uzivatel in User.objects.all():
            if self.similar(self.vyhladavacie_pole,uzivatel.username) > 0.3:
                self.hladane_osoby.append(uzivatel)


    def similar(self,a, b):
        return SequenceMatcher(None, a, b).ratio()


