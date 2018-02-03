'''
Created on Jan 21, 2018

@author: yiwei
'''
import pandas as pd
import urllib3 as url
import json
import numpy as np
import pickle as pkl
import os

PROTEIN_ID = 203
FAT_ID = 204
CARB_ID = 205
KCAL_ID = 208

def test_api(k,
             p,
             c, 
             f, 
             error_bound):
    print("""Testing params: kcal={}&protein={}&carb={}&fat={}&error_bound={}""".format(k, p, c, f, error_bound))
    
    http = url.PoolManager()
    request_url = """http://localhost:8000/api/getmeal/?kcal={}&protein={}&carb={}&fat={}&error_bound={}""".format(k, p, c, f, error_bound)
    
    r = http.request('GET', request_url)    
    meal_data = json.loads(r.data)
    
    for i in range(0, len(meal_data)):
        if str(i) not in meal_data:
            print('None Found')
            return False
        meal = meal_data[str(i)]
        protein_result = meal['protein_percent']
        carb_result = meal['carb_percent']
        fat_result = meal['fat_percent']
        kcal_result = meal['kcal']
                          
        if abs(protein_result - p) - error_bound >= 0:
            print('Wrong protein ' + str(protein_result))
            return False
        if abs(carb_result - c) - error_bound >= 0:
            print('Wrong carb ' + str(carb_result))
            return False
        if abs(fat_result - f) - error_bound >= 0:
            print('Wrong fat' + str(fat_result))
            return False
        if abs((kcal_result - k)/ k) - error_bound >= 0:
            print('Wrong kcal ' + str(kcal_result))
            return False
            
        ingredients = meal['ingredients']
        
        total_kcal = 0
        total_protein = 0
        total_fat = 0
        total_carb = 0
        for igd in ingredients:
            food_serving_id = igd['food_serving_id']
            serving_nutr = serving_nutrition[
                serving_nutrition[
                    'food_serving_id'] == food_serving_id]
            kcal = serving_nutr[
                serving_nutr['nutrient_id'] == KCAL_ID]['nutrient_amount'].values[0]
            protein = serving_nutr[
                serving_nutr['nutrient_id'] == PROTEIN_ID]['nutrient_amount'].values[0]
            carb = serving_nutr[
                serving_nutr['nutrient_id'] == CARB_ID]['nutrient_amount'].values[0]
            fat = serving_nutr[
                serving_nutr['nutrient_id'] == FAT_ID]['nutrient_amount'].values[0]
            
            total_kcal += kcal
            total_protein += protein
            total_fat += fat
            total_carb += carb
        
        total_grams = total_protein + total_fat + total_carb
        
        assert np.isclose(meal['kcal'], total_kcal)
        assert np.isclose(meal['protein_percent'], total_protein/total_grams)
        assert np.isclose(meal['carb_percent'], total_carb/total_grams)
        assert np.isclose(meal['fat_percent'], total_fat/total_grams)
    return True

if __name__ == '__main__':
    if os.path.exists('serving_nutrition.pkl'):
        serving_nutrition = pkl.load(open('serving_nutrition.pkl', 'rb'))
    else:
        serving_nutrition = pd.read_csv('serving_nutrition.csv')
            
    kcals = np.arange(600, 3000, 100)
    proteins = 0.4
    carbs = 0.3
    fats = 0.3
    error_bound = 0.04    
    
    for kcal in kcals:
        print(test_api(k=kcal,
                 p=proteins,
                 c=carbs,
                 f=fats,
                 error_bound=error_bound))
        
   
        
            
                