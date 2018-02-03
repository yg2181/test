from __future__ import unicode_literals

from django.db import models

class ServingNutrition(models.Model):
    food_serving_id = models.TextField(primary_key=True, unique=True)
    food_id = models.IntegerField()
    serving_size_id = models.IntegerField()
    short_desc = models.TextField()
    nutrient_name = models.TextField()
    nutrient_id = models.IntegerField()
    nutrient_amount = models.FloatField()
    serving_size = models.TextField()
    
    class Meta:
        managed = False
        db_table = 'serving_nutrition'
