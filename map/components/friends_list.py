from django_unicorn.components import UnicornView
from django.contrib.auth.models import User
from friendship.models import Friend, Follow, Block,FriendshipRequest
from map.models import Notifikacie, Objekty, Podskupiny
from map.views import over_viditelnost
from difflib import SequenceMatcher
import json

class FriendsListView(UnicornView):

    zoznam_priatelov = []
    zoznam_priatelov_pocet = 0
    zoznam_ziadosti = []
    zoznam_ziadosti_pocet = 0
    zoznam_odoslanych_ziadosti = []
    zoznam_odoslanych_ziadosti_pocet = 0
    priatelia_obsah = True
    ziadosti_obsah = False
    blokacie_obsah = False
    najst_priatelov_obsah = False
    hladane_osoby = [] #Osoby so search baru
    vyhladavacie_pole = ""
    blokovane_osoby = []
    blokovane_osoby_pocet = 0
    zdielane_vrstvy = []
    def mount(self):
        self.zoznam_priatelov = Friend.objects.friends(self.request.user)
        for priatel in self.zoznam_priatelov:
            if Block.objects.is_blocked(self.request.user, priatel) == True:
                self.zoznam_priatelov.remove(priatel)

        self.zoznam_priatelov_pocet = len(self.zoznam_priatelov)
        self.priatelia_obsah = True

    def prepni_na_priatelov(self):
        self.zoznam_priatelov = Friend.objects.friends(self.request.user)
        for priatel in self.zoznam_priatelov:
            if Block.objects.is_blocked(self.request.user,priatel) == True:
                self.zoznam_priatelov.remove(priatel)

        self.zoznam_priatelov_pocet = len(self.zoznam_priatelov)
        self.priatelia_obsah = True
        self.ziadosti_obsah = False
        self.najst_priatelov_obsah = False
        self.blokacie_obsah = False

    def prepni_na_ziadosti(self):
        self.zoznam_ziadosti = Friend.objects.unrejected_requests(user=self.request.user)
        self.zoznam_ziadosti_pocet = len(self.zoznam_ziadosti)
        self.zoznam_odoslanych_ziadosti = Friend.objects.sent_requests(user=self.request.user)
        self.zoznam_odoslanych_ziadosti_pocet = len(self.zoznam_odoslanych_ziadosti)
        self.priatelia_obsah = False
        self.ziadosti_obsah = True
        self.najst_priatelov_obsah = False
        self.blokacie_obsah = False


    def prepni_na_najst_priatelov(self):
        self.hladane_osoby = []
        self.vyhladavacie_pole = ""
        self.priatelia_obsah = False
        self.ziadosti_obsah = False
        self.najst_priatelov_obsah = True
        self.blokacie_obsah = False

    def prepni_na_blokacie(self):
        self.hladane_osoby = []
        self.vyhladavacie_pole = ""
        self.priatelia_obsah = False
        self.ziadosti_obsah = False
        self.najst_priatelov_obsah = False
        self.blokacie_obsah = True
        self.blokovane_osoby = Block.objects.blocking(self.request.user)
        self.blokovane_osoby_pocet = len(self.blokovane_osoby)

    def zablokuj_osobu(self,id_blokovaneho):
        other_user = User.objects.get(pk=id_blokovaneho)
        #if Friend.objects.are_friends(self.request.user, other_user) == True: Blokovaný bude vidieť ako priatela, blokovatel len ako bloknuteho
        #    Friend.objects.remove_friend(self.request.user, other_user)
        for ziadost in FriendshipRequest.objects.all():
            if ziadost.from_user == other_user and ziadost.to_user == self.request.user:
                ziadost.cancel()
            elif ziadost.to_user == other_user and ziadost.from_user == self.request.user:
                ziadost.cancel()
        Block.objects.add_block(self.request.user, other_user)
        self.zrusit_vsetky_zdielania(self.request.user, other_user)
        self.prepni_na_blokacie()

    def odblokuj_uzivatela(self,id_blokovaneho):
        other_user = User.objects.get(pk=id_blokovaneho)
        Block.objects.remove_block(self.request.user,other_user)
        self.prepni_na_blokacie()



    def odmietni_ziadost(self,id):
        ziadost = FriendshipRequest.objects.get(id=id)
        ziadost.cancel()
        self.prepni_na_ziadosti()

    def primi_ziadost(self,id):
        ziadost = FriendshipRequest.objects.get(id=id)
        ziadost.accept()
        notifikacia = Notifikacie()
        notifikacia.prijimatel = ziadost.from_user
        notifikacia.odosielatel = ziadost.to_user
        notifikacia.sprava = "prijal Vašu žiadosť o <b>priateľstvo</b>"
        notifikacia.save()
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
            if Block.objects.is_blocked(uzivatel,self.request.user) == True:
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
        notifikacia = Notifikacie()
        notifikacia.prijimatel = other_user
        notifikacia.odosielatel = self.request.user
        notifikacia.sprava = "Vás požiadal o <b>priateľstvo</b>"
        notifikacia.save()
        self.hladat_priatelov()

    def priatelia_zrusit_priatelstvo(self,other_user_pk):
        other_user = User.objects.get(pk=other_user_pk)
        Friend.objects.remove_friend(self.request.user, other_user)
        self.zrusit_vsetky_zdielania(self.request.user, other_user)
        self.zrusit_vsetky_zdielania(other_user,self.request.user)
        self.prepni_na_priatelov()


    def similar(self,a, b):
        return SequenceMatcher(None, a, b).ratio()

    def zrusit_vsetky_zdielania(self,spravca,poskodeny):
        other_user = poskodeny
        priatel = other_user.username  # !!!
        for zdielany_objekt in Objekty.objects.all().filter(podskupina__spravca=spravca.username):
            if zdielany_objekt.nastavenia != None:
                nastavenia = json.loads(zdielany_objekt.nastavenia)
                if "shared_with" in nastavenia and (priatel in nastavenia["shared_with"]):
                    Podskupiny.objects.get(id=nastavenia["shared_with"][priatel]).delete()
                    nastavenia["shared_with"].pop(priatel)
                    zdielany_objekt.nastavenia = json.dumps(nastavenia)
                    zdielany_objekt.save()

    def vsetky_zdielane_vrstvy_s_priatelom(self, id_priatela): #Nahraj do zdielane_vrstvy vsetky s kamaratom zdielane vrstvy
        self.zdielane_vrstvy = []
        other_user = User.objects.get(id=id_priatela)
        priatel = other_user.username  # !!!
        for zdielany_objekt in Objekty.objects.all().filter(podskupina__spravca=self.request.user.username):
            if zdielany_objekt.nastavenia != None:
                nastavenia = json.loads(zdielany_objekt.nastavenia)
                if "shared_with" in nastavenia and (priatel in nastavenia["shared_with"]):
                    zapis = False
                    pseudo_podskupina_objektu = Podskupiny.objects.get(
                        pk=nastavenia["shared_with"][other_user.username])
                    viditelnost = pseudo_podskupina_objektu.viditelnost
                    if "w" in viditelnost.uzivatelia[other_user.username]:
                        zapis = True
                    self.zdielane_vrstvy.append(   (zdielany_objekt,zapis)    )




