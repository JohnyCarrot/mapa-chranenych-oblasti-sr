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


class Viditelnost_mapa(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    globalne = models.TextField(blank=True, null=True, default="")
    prihlaseny = models.TextField(blank=True, null=True, default="") #Ak je prázdne alebo None tak sa díva na global
    uzivatelia = models.JSONField(blank=True, null=True, default=dict)


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
    diskusia = models.BigIntegerField(blank=True, null=True)
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
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    map_settings = models.OneToOneField(Map_settings, on_delete=models.CASCADE)

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


class Diskusia(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    viditelnost = models.ForeignKey(Viditelnost_mapa, blank=True, null=True, on_delete=models.CASCADE, to_field='id',db_column="viditelnost")
    anonym_read = models.BooleanField(default=True) #Ak True, môže vidieť každý, inak len ten čo má r vo viditelnosti
    anonym_write = models.BigIntegerField(default=0, null=False) #0 - všetci,1 - R, 2 - W
    spravca = models.TextField(blank=True, null=True)

class Diskusny_prispevok(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    diskusia = models.OneToOneField(Diskusia, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sprava = models.TextField(blank=True, null=False, default="")
    timestamp = models.DateTimeField(default=timezone.now, null=False)
    karma = models.JSONField(blank=True, null=True, default=dict) # meno uzivatela a + / - a nakoniec sa karma sčíta






@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance,map_settings=Map_settings.objects.create())

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()