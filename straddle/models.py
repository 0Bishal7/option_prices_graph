from django.db import models

class StraddlePrice(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    index_name = models.CharField(max_length=50, default="NIFTY")  # Renamed from index_name
    atm_strike = models.PositiveIntegerField()
    call_price = models.FloatField()
    put_price = models.FloatField()
    straddle_price = models.FloatField()
    ltp=models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.timestamp} | {self.index_type}: {self.straddle_price}"

    class Meta:
        verbose_name = "Straddle Price"
        verbose_name_plural = "Straddle Prices"
        ordering = ['-timestamp']

# from django.db import models

# class StraddlePrice(models.Model):
#     timestamp = models.DateTimeField(auto_now_add=True)
#     index_name = models.CharField(max_length=50, default="NIFTY")
#     atm_strike = models.PositiveIntegerField()  # Positive integers only
#     call_price = models.FloatField()
#     put_price = models.FloatField()
#     straddle_price = models.FloatField()

#     def __str__(self):
#         return f"{self.timestamp} | {self.index_name}: {self.straddle_price}"

#     class Meta:
#         verbose_name = "Straddle Price"
#         verbose_name_plural = "Straddle Prices"
#         ordering = ['-timestamp']  # Orders by timestamp, newest first





# from django.db import models

# class StraddlePrice(models.Model):
#     timestamp = models.DateTimeField(auto_now_add=True)
#     atm_strike = models.IntegerField()
#     call_price = models.FloatField()
#     put_price = models.FloatField()
#     straddle_price = models.FloatField()

#     def __str__(self):
#         return f"{self.timestamp}: {self.straddle_price}"
