'''
Created on Jan 20, 2018

@author: ygu
'''
from collections import namedtuple

Meal = namedtuple('Meal',
                  ['food_serving_ids',
                   'fitness_score',
                   'meal_nutrition',
                   'ingredient_list'])

Ingredient = namedtuple('Ingredient',
                        ['food_serving_id',
                         'short_description',
                         'serving_size'])

MealNutrition = namedtuple('MealNutrition',
                           ['kcal',
                            'protein_percent',
                            'carb_percent',
                            'fat_percent'])


def is_within_error_bounds(sample_meal_nutrition,
                           target_meal_nutrition,
                           error_bound):
    """
    Checks if all properties are within the error_bound param

    @param sample_meal_nutrition: Sample MealNutrition 
    @param target_meal_nutrition: Target MealNutrition
    @param error_bound: Maximum percentage difference
    for all nutritional metrics
    """
    assert error_bound > 0, 'error_bound parameter cannot be negative'

    kcal_diff = abs(
        (sample_meal_nutrition.kcal -
         target_meal_nutrition.kcal) /
        target_meal_nutrition.kcal)
    protein_diff = abs(
        sample_meal_nutrition.protein_percent -
        target_meal_nutrition.protein_percent)
    carb_diff = abs(
        sample_meal_nutrition.carb_percent -
        target_meal_nutrition.carb_percent)
    fat_diff = abs(
        sample_meal_nutrition.fat_percent -
        target_meal_nutrition.fat_percent)

    return all([kcal_diff <= error_bound,
                protein_diff <= error_bound,
                carb_diff <= error_bound,
                fat_diff <= error_bound])


def fitness_function(sample_meal_nutrition,
                     target_meal_nutrition):
    """
    Cost function for measuring the fitness of the selections
    TODO: Can tweak this to optimize convergence speed

    Sums up all the differences in percentile space to get the final 'fitness'.
    Values closest to zero represent better fit.

    @param sample_meal_nutrition: Sample MealNutrition 
    @param target_meal_nutrition: Target MealNutrition 
    """
    kcal_diff = abs(
        (sample_meal_nutrition.kcal -
         target_meal_nutrition.kcal) /
        target_meal_nutrition.kcal)
    protein_diff = abs(
        sample_meal_nutrition.protein_percent -
        target_meal_nutrition.protein_percent)
    carb_diff = abs(
        sample_meal_nutrition.carb_percent -
        target_meal_nutrition.carb_percent)
    fat_diff = abs(
        sample_meal_nutrition.fat_percent -
        target_meal_nutrition.fat_percent)
    return kcal_diff + protein_diff + carb_diff + fat_diff
