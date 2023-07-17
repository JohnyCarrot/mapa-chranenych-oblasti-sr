#
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
import uuid

class Skupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    spravca = models.TextField(blank=True, null=True)
    viditelnost = ArrayField(models.TextField(), blank=True)  #
    nastavenia = models.JSONField(blank=True, null=True)  #

    class Meta:
        managed = False
        db_table = 'skupiny'

class Podskupiny(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    viditelnost = ArrayField(models.TextField(), blank=True)  #
    spravca = models.TextField(blank=True, null=True)
    skupina = models.ForeignKey(Skupiny, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "skupina")
    nastavenia = models.JSONField(blank=True, null=True)   #

    class Meta:
        managed = False
        db_table = 'podskupiny'

class Objekty(models.Model):
    id = models.TextField(primary_key=True, default=uuid.uuid4, editable=False)
    meno = models.TextField(blank=True, null=True)
    color = models.TextField(blank=True, null=True)
    fillcolor = models.TextField(blank=True, null=True)
    html = models.TextField(blank=True, null=True)
    diskusia = models.BigIntegerField(blank=True, null=True)
    podskupina = models.ForeignKey(Podskupiny, blank=True, null=True,on_delete=models.CASCADE,to_field='id',db_column = "podskupina")
    geometry = models.GeometryField()  #
    nastavenia = models.JSONField(blank=True, null=True)  #

    class Meta:
        managed = False
        db_table = 'objekty'