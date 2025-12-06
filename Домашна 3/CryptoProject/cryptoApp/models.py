# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Coins(models.Model):
    coin_id = models.CharField(unique=True, max_length=100, blank=True, null=True)
    symbol = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    market_cap_rank = models.IntegerField(blank=True, null=True)
    current_price = models.FloatField(blank=True, null=True)
    market_cap = models.FloatField(blank=True, null=True)
    total_volume = models.FloatField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'coins'


class OhlcvData(models.Model):
    coin_id = models.CharField(primary_key=True, max_length=100)  # The composite primary key (coin_id, date) found, that is not supported. The first column is selected.
    symbol = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateField()
    open = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ohlcv_data'
        unique_together = (('coin_id', 'date'),)
