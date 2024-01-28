from django_unicorn.components import UnicornView
from map.views import over_viditelnost
from map.models import Skupiny, Diskusia_skupiny,Diskusny_prispevok_skupiny, Objekty
import json
from difflib import SequenceMatcher
class SkupinyObsahView(UnicornView):
    stranka_skupiny = True
    stranka_najst_skupinu = False
    vytvorit_skupinu = False #stranka
    skupiny = [] # skupiny v ktorých je užívatel
    vyhladavacie_pole = ""
    hladane_skupiny = []
    def mount(self):
        self.nahraj_skupiny()

    def hladaj_skupinu(self):
        self.hladane_skupiny.clear()
        for skupina in Skupiny.objects.filter(diskusia__isnull=False):
            if skupina.diskusia.verejna == False:
                continue

            if self.request.user.username in skupina.diskusia.uzivatelia:
                v_skupine = 1
            elif skupina.diskusia.pre_kazdeho == False:
                v_skupine = 2
            else:
                v_skupine = 0
            meno = skupina.meno
            if meno.lower().find(self.vyhladavacie_pole.lower()) != -1:
                self.hladane_skupiny.append( (skupina,v_skupine)  )
            elif self.similar(meno,self.vyhladavacie_pole) > 0.6:
                self.hladane_skupiny.append( (skupina,v_skupine)  )

        if len(self.hladane_skupiny)==0:
            self.hladane_skupiny.append( (None,None) )
    def nahraj_skupiny(self):
        self.skupiny.clear()
        for skupina in Skupiny.objects.filter(diskusia__isnull=False):
            if self.request.user.username in skupina.diskusia.uzivatelia:
                pocet_komentov = len(Diskusny_prispevok_skupiny.objects.filter(diskusia=skupina.diskusia))
                pocet_vrstiev = 0
                for objekt in Objekty.objects.filter(podskupina__skupina=skupina):
                    if objekt.nastavenia != None:
                        nastavenia = json.loads(objekt.nastavenia)
                        if "deleted" in nastavenia and nastavenia['deleted'] == True:
                            continue
                    pocet_vrstiev += 1
                if skupina.nastavenia is not None and "popis" in json.loads(skupina.nastavenia):
                    self.skupiny.append( (skupina, json.loads(skupina.nastavenia)['popis'],pocet_komentov,pocet_vrstiev  )  )
                else:
                    self.skupiny.append((skupina, None,pocet_komentov,pocet_vrstiev))

    def prepni_na_skupiny(self):
        self.nahraj_skupiny()
        self.stranka_skupiny = True
        self.stranka_najst_skupinu = False
        self.vytvorit_skupinu = False
        self.vyhladavacie_pole = ""
        self.hladane_skupiny = []

    def prepni_na_najst_skupinu(self):
        self.stranka_skupiny = False
        self.stranka_najst_skupinu = True
        self.vytvorit_skupinu = False
        self.vyhladavacie_pole = ""
        self.hladane_skupiny = []

    def prepni_na_vytvorit_skupinu(self):
        self.stranka_skupiny = False
        self.stranka_najst_skupinu = False
        self.vytvorit_skupinu = True
        self.vyhladavacie_pole = ""
        self.hladane_skupiny = []

    def pridat_sa_do_skupiny(self,id_skupiny):
        skupina = Skupiny.objects.get(id = id_skupiny)
        if skupina.spravca != self.request.user.username:
            skupina.viditelnost.uzivatelia[self.request.user.username] = "r"
        else:
            skupina.viditelnost.uzivatelia[self.request.user.username] = "rw"
        skupina.diskusia.uzivatelia[self.request.user.username] = "r"
        skupina.viditelnost.save()
        skupina.diskusia.save()
        skupina.save()


    def similar(self,a, b):
        return SequenceMatcher(None, a, b).ratio()