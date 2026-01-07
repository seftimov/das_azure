from django.db import models


# Create your models here.

class OhlcvData(models.Model):
    coin_id = models.CharField(primary_key=True, max_length=100)
    symbol = models.CharField(max_length=20)
    date = models.DateField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        managed = False
        db_table = 'ohlcv_data'
        unique_together = (('coin_id', 'date'),)
