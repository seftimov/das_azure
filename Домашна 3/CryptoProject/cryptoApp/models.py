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
    coin_id = models.CharField(primary_key=True,
                               max_length=100)  # The composite primary key (coin_id, date) found, that is not supported. The first column is selected.
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


class News(models.Model):
    symbol = models.CharField(max_length=20, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    source_domain = models.CharField(max_length=100, blank=True, null=True)
    news_datetime = models.DateTimeField(blank=True, null=True)
    vader_score = models.FloatField(blank=True, null=True)
    currencies = models.TextField(blank=True, null=True)
    sourceid = models.CharField(db_column='sourceId', max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'news'


class DailySentiment(models.Model):
    symbol = models.CharField(max_length=20)
    date = models.DateField()
    sentiment_score = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'daily_sentiment'
        unique_together = (('symbol', 'date'),)


class OnchainMetrics(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True)
    date = models.DateField()
    time = models.DateTimeField(blank=True, null=True)

    capmrktestusd = models.FloatField(db_column='CapMrktEstUSD', blank=True, null=True)
    referencerate = models.FloatField(db_column='ReferenceRate', blank=True, null=True)
    referenceratebtc = models.FloatField(db_column='ReferenceRateBTC', blank=True, null=True)
    referencerateeth = models.FloatField(db_column='ReferenceRateETH', blank=True, null=True)
    referencerateeur = models.FloatField(db_column='ReferenceRateEUR', blank=True, null=True)
    referencerateusd = models.FloatField(db_column='ReferenceRateUSD', blank=True, null=True)

    volume_reported_spot_usd_1d = models.FloatField(blank=True, null=True)
    nvt_ratio = models.FloatField(db_column='NVT_Ratio', blank=True, null=True)

    adractcnt = models.BigIntegerField(db_column='AdrActCnt', blank=True, null=True)
    adrbalcnt = models.BigIntegerField(db_column='AdrBalCnt', blank=True, null=True)

    assetcompletiontime = models.DateTimeField(db_column='AssetCompletionTime', blank=True, null=True)
    asseteodcompletiontime = models.DateTimeField(db_column='AssetEODCompletionTime', blank=True, null=True)

    capmvrvcur = models.FloatField(db_column='CapMVRVCur', blank=True, null=True)
    capmrktcurusd = models.FloatField(db_column='CapMrktCurUSD', blank=True, null=True)

    isstotntv = models.FloatField(db_column='IssTotNtv', blank=True, null=True)
    isstotusd = models.FloatField(db_column='IssTotUSD', blank=True, null=True)

    pricebtc = models.FloatField(db_column='PriceBTC', blank=True, null=True)
    priceusd = models.FloatField(db_column='PriceUSD', blank=True, null=True)

    roi1yr = models.FloatField(db_column='ROI1yr', blank=True, null=True)
    roi30d = models.FloatField(db_column='ROI30d', blank=True, null=True)

    splycur = models.FloatField(db_column='SplyCur', blank=True, null=True)
    hashrate = models.FloatField(db_column='HashRate', blank=True, null=True)

    txcnt = models.BigIntegerField(db_column='TxCnt', blank=True, null=True)
    txtfrcnt = models.BigIntegerField(db_column='TxTfrCnt', blank=True, null=True)
    blkcnt = models.BigIntegerField(db_column='BlkCnt', blank=True, null=True)
    feetotntv = models.FloatField(db_column='FeeTotNtv', blank=True, null=True)
    splyexpfut10yr = models.FloatField(db_column='SplyExpFut10yr', blank=True, null=True)
    flowinexntv = models.FloatField(db_column='FlowInExNtv', blank=True, null=True)
    flowinexusd = models.FloatField(db_column='FlowInExUSD', blank=True, null=True)
    flowoutexntv = models.FloatField(db_column='FlowOutExNtv', blank=True, null=True)
    flowoutexusd = models.FloatField(db_column='FlowOutExUSD', blank=True, null=True)
    splyexntv = models.FloatField(db_column='SplyExNtv', blank=True, null=True)
    splyexusd = models.FloatField(db_column='SplyExUSD', blank=True, null=True)

    sentiment_score = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'onchain_metrics'
        unique_together = (('symbol', 'date'),)
