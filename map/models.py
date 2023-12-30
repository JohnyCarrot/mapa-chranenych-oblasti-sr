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
    spravca = models.TextField(blank=True, null=True)
    odbery = models.JSONField(blank=True, null=True, default=dict) #odbery notifikácií, meno: true / false
    aktivna = models.BooleanField(default=True) #Ak false diskusia bude archuvovaná, teda akoby neexistovala (vidí iba správca)

class Diskusny_prispevok(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    diskusia = models.ForeignKey(Diskusia, blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    sprava = models.TextField(blank=True, null=False, default="") #HTML !!!!
    timestamp = models.DateTimeField(default=timezone.now, null=False)
    karma = models.JSONField(blank=True, null=True, default=dict) # meno uzivatela a + / - a nakoniec sa karma sčíta

class Skupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    spravca = models.TextField(blank=True, null=True)
    viditelnost = models.ForeignKey(Viditelnost_mapa, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "viditelnost")  #
    nastavenia = models.JSONField(blank=True, null=True)  #
    priorita = models.BigIntegerField(default=None, null=True)

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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    icon = models.TextField(blank=True, null=False, default="")  # HTML !!!!
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

class zdielanie_objektu(models.Model):
    zdielane_s = models.ForeignKey(User, on_delete=models.CASCADE)
    objekt = models.ForeignKey(Objekty, on_delete=models.CASCADE)
    zapis = models.BooleanField(default=False)


class Notifikacie(models.Model):
    odosielatel = models.ForeignKey(User, on_delete=models.CASCADE,related_name='odosielatel')
    prijimatel = models.ForeignKey(User, on_delete=models.CASCADE,related_name='prijimatel')
    sprava = models.TextField(blank=True, null=False,default="")
    level = models.BigIntegerField(default=1, null=False) #  (1-'info', 3-'warning', 4-'error') (default=info)
    timestamp = models.DateTimeField(default=timezone.now,null=False)
    videne = models.BooleanField(default=False)








