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
        ziadost.cancel()
        self.prepni_na_ziadosti()

    def primi_ziadost(self,id):
        ziadost = FriendshipRequest.objects.get(id=id)
        ziadost.accept()
        self.prepni_na_ziadosti()

    def hladat_priatelov(self):
        #0 - žiaden vzťah
        #1 - žiadosť odoslaná
        #2 - priatelia
        #3 - zablokovaný
        self.hladane_osoby = []
        for uzivatel in User.objects.all():
            if uzivatel.username == self.request.user.username:
                continue
            uz_odoslane = 0
            if self.similar(self.vyhladavacie_pole,uzivatel.username) > 0.5:
                for x in Friend.objects.sent_requests(user=self.request.user):
                    if (User.objects.get(id=x.to_user_id).get_username() == uzivatel.username):
                        uz_odoslane = 1
                if Friend.objects.are_friends(self.request.user, uzivatel) == True:
                    uz_odoslane = 2
                if Block.objects.is_blocked(self.request.user, uzivatel) == True:
                    uz_odoslane = 3
                self.hladane_osoby.append(  (uzivatel,uz_odoslane)  )

    def poziadat_o_priatelstvo(self,other_user_pk):
        other_user = User.objects.get(pk=other_user_pk)
        Friend.objects.add_friend(
            self.request.user,
            other_user,
                )
        self.hladat_priatelov()

    def priatelia_zrusit_priatelstvo(self,other_user_pk):
        other_user = User.objects.get(pk=other_user_pk)
        Friend.objects.remove_friend(self.request.user, other_user)
        self.prepni_na_priatelov()


    def similar(self,a, b):
        return SequenceMatcher(None, a, b).ratio()


