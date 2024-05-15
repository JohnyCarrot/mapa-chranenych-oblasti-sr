#
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
import uuid
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime


class Viditelnost_mapa(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    globalne = models.TextField(blank=True, null=True, default="")
    prihlaseny = models.TextField(blank=True, null=True, default="") #Ak je prázdne alebo None tak sa díva na global
    uzivatelia = models.JSONField(blank=True, null=True, default=dict)

class Diskusia(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    anonym_read = models.BooleanField(default=True) #Ak True, môže vidieť každý, inak len ten čo má r vo viditelnosti
    anonym_write = models.BigIntegerField(default=0, null=False) #0 - všetci,1 - R, 2 - W; všetci čo majú R,W permisiu ....
    spravca = models.TextField(blank=True, null=True) #Ak null tak musí byť superuser
    odbery = models.JSONField(blank=True, null=True, default=dict) #odbery notifikácií, meno: true / false
    aktivna = models.BooleanField(default=True) #Ak false diskusia bude archuvovaná, teda akoby neexistovala (vidí iba správca)

class Diskusny_prispevok(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    diskusia = models.ForeignKey(Diskusia, blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    sprava = models.TextField(blank=True, null=False, default="") #HTML !!!!
    timestamp = models.DateTimeField(default=timezone.now, null=False)
    karma = models.JSONField(blank=True, null=True, default=dict) # meno uzivatela a + / - a nakoniec sa karma sčíta

class Diskusia_skupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    uzivatelia = models.JSONField(blank=True, null=True, default=dict)  # username a r,| r - je v skupine, w - moderator (moze mazat)
    verejna = models.BooleanField(default=True)  # Kazdy moze prezerat a vyhladat
    pre_kazdeho = models.BooleanField(default=True)  # Kazdy sa moze pridat
    #Pripadne pridat spravcov, odbery...

class Diskusny_prispevok_skupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    diskusia = models.ForeignKey(Diskusia_skupiny, blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    sprava = models.TextField(blank=True, null=False, default="") #HTML !!!!
    timestamp = models.DateTimeField(default=timezone.now, null=False)
    karma = models.JSONField(blank=True, null=True, default=dict) # meno uzivatela a + / - a nakoniec sa karma sčíta

class Diskusny_prispevok_skupiny_komentar(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    prispevok = models.ForeignKey(Diskusny_prispevok_skupiny, blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    sprava = models.TextField(blank=True, null=False, default="") #NIE HTML !!!!
    timestamp = models.DateTimeField(default=timezone.now, null=False)
    karma = models.JSONField(blank=True, null=True, default=dict) # meno uzivatela a + / - a nakoniec sa karma sčíta


class Skupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    spravca = models.TextField(blank=True, null=True)
    viditelnost = models.ForeignKey(Viditelnost_mapa, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "viditelnost")  #
    nastavenia = models.JSONField(blank=True, null=True)  #popis,own,shared
    priorita = models.BigIntegerField(default=None, null=True)
    diskusia = models.ForeignKey(Diskusia_skupiny, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "diskusia")

    class Meta:
        managed = False
        db_table = 'skupiny'

class Podskupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    viditelnost = models.ForeignKey(Viditelnost_mapa, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "viditelnost")  #
    spravca = models.TextField(blank=True, null=True)
    skupina = models.ForeignKey(Skupiny, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "skupina")
    nastavenia = models.JSONField(blank=True, null=True)   #
    priorita = models.BigIntegerField(default=None, null=True)

    class Meta:
        managed = False
        db_table = 'podskupiny'

class Objekty(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    style = models.JSONField(blank=True, null=True)
    html = models.TextField(blank=True, null=True)
    diskusia = models.ForeignKey(Diskusia, blank=True, null=True, on_delete=models.CASCADE,to_field='id',db_column = "diskusia")
    podskupina = models.ForeignKey(Podskupiny, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "podskupina")
    geometry = models.GeometryField()  #
    nastavenia = models.JSONField(blank=True, null=True)  #
    stupen_ochrany = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'objekty'

class Map_settings(models.Model):
    stupen2 = models.BooleanField(default=True) #Stupeň ochrany 2
    stupen3 = models.BooleanField(default=True)#Stupeň ochrany 3
    stupen4 = models.BooleanField(default=True)#Stupeň ochrany 4
    stupen5 = models.BooleanField(default=True)#Stupeň ochrany 5
    legenda = models.BooleanField(default=True)  # True zobrazí / False nezobrazí


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    icon = models.TextField(blank=True, null=False, default="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")  # HTML !!!!
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    website_url = models.TextField(max_length=500, blank=True, default="")
    facebook_url = models.TextField(max_length=500, blank=True, default="")
    instagram_url = models.TextField(max_length=500, blank=True, default="")
    youtube_url = models.TextField(max_length=500, blank=True, default="")
    linked_in_url = models.TextField(max_length=500, blank=True, default="")
    reg_date = models.DateTimeField(default=timezone.now, null=False)
    map_settings = models.OneToOneField(Map_settings, on_delete=models.CASCADE)

    @property
    def vek(self):
        return int((datetime.now().date() - self.birth_date).days / 365.25)


class Notifikacie(models.Model):
    odosielatel = models.ForeignKey(User, on_delete=models.CASCADE,related_name='odosielatel')
    prijimatel = models.ForeignKey(User, on_delete=models.CASCADE,related_name='prijimatel')
    sprava = models.TextField(blank=True, null=False,default="")
    level = models.BigIntegerField(default=1, null=False) #  (1-'info', 3-'warning', 4-'error') (default=info)
    timestamp = models.DateTimeField(default=timezone.now,null=False)
    videne = models.BooleanField(default=False)

class Sprava(models.Model):
    odosielatel = models.ForeignKey(User, on_delete=models.CASCADE,related_name='odosielatel_sprava')
    prijimatel = models.ForeignKey(User, on_delete=models.CASCADE,related_name='prijimatel_sprava')
    sprava = models.TextField(blank=True, null=False,default="")
    timestamp = models.DateTimeField(default=timezone.now,null=False)
    videne = models.BooleanField(default=False)






