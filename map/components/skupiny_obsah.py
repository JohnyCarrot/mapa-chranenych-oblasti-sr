from django_unicorn.components import UnicornView
from map.views import over_viditelnost
from map.models import Skupiny

class SkupinyObsahView(UnicornView):
    stranka_skupiny = True
    stranka_najst_skupinu = False
    vytvorit_skupinu = False #stranka
    skupiny = [] # skupiny v ktorých je užívatel
    def mount(self):
        self.nahraj_skupiny()

    def nahraj_skupiny(self):
        self.skupiny.clear()
        for skupina in Skupiny.objects.filter(spravca__isnull=False):
            if over_viditelnost(skupina.viditelnost,self.request.user.is_authenticated,self.request.user.username):
                if skupina.nastavenia is not None and ("shared" in skupina.nastavenia or "own" in skupina.nastavenia):
                    continue
                self.skupiny.append(skupina)

    def prepni_na_skupiny(self):
        self.nahraj_skupiny()
        self.stranka_skupiny = True
        self.stranka_najst_skupinu = False
        self.vytvorit_skupinu = False

    def prepni_na_najst_skupinu(self):
        self.stranka_skupiny = False
        self.stranka_najst_skupinu = True
        self.vytvorit_skupinu = False

    def prepni_na_vytvorit_skupinu(self):
        self.stranka_skupiny = False
        self.stranka_najst_skupinu = False
        self.vytvorit_skupinu = True