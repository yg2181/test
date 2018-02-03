import math
from django.db.models import Avg
from django.http import JsonResponse

import numpy as np
from .constants import DEFAULT_ERROR_BOUND, DEFAULT_NUM_MEALS
from .constants import KCAL_ID
from .constants import NUM_SAMPLES_PER_GENERATION, SELECTION_PARAM, \
    MUTATIONS_PER_GEN, MAX_GENERATIONS_NUM
from .genetic_search import GeneticFoodPopulation
from .meal import Meal, MealNutrition
from .models import ServingNutrition


def serialize_meal_response(valid_meals_found):
    """
    Creates a JSON response containing the list of valid meals

    @param valid_meals_found: List of Meals
    """
    meals = {}
    for i in range(0, len(valid_meals_found)):
        meal = valid_meals_found[i]
        meal_nutrition = meal.meal_nutrition
        fitness_score = meal.fitness_score

        ingredient_list = [
            {'food_serving_id': ingredient.food_serving_id,
             'short_description': ingredient.short_description,
             'serving_size': ingredient.serving_size}
            for ingredient in meal.ingredient_list]

        meal_dict = {
            'ingredients': ingredient_list,
            'fitness_score': fitness_score,
            'kcal': meal_nutrition.kcal,
            'protein_percent': meal_nutrition.protein_percent,
            'carb_percent': meal_nutrition.carb_percent,
            'fat_percent': meal_nutrition.fat_percent
        }
        meals[i] = meal_dict
    return meals


def get_meal(request):
    if 'kcal' not in request.GET:
        return JsonResponse({
            'message:': 'missing kcal parameter'}, status=422)
    if 'protein' not in request.GET:
        return JsonResponse(
            {'message:': 'missing protein parameter'}, status=422)
    if 'carb' not in request.GET:
        return JsonResponse({
            'message:': 'missing carb parameter'}, status=422)
    if 'fat' not in request.GET:
        return JsonResponse({
            'message:': 'missing fat parameter'}, status=422)

    try:
        kcal_target = float(request.GET['kcal'])
    except:
        return JsonResponse(
            {'message:': 'non float kcal parameter'}, status=422)
    try:
        protein_target = float(request.GET['protein'])
    except:
        return JsonResponse(
            {'message:': 'non float protein parameter'}, status=422)
    try:
        carb_target = float(request.GET['carb'])
    except:
        return JsonResponse(
            {'message:': 'non float carb parameter'}, status=422)
    try:
        fat_target = float(request.GET['fat'])
    except:
        return JsonResponse(
            {'message:': 'non float fat parameter'}, status=422)

    if 'error_bound' not in request.GET:
        error_bound = DEFAULT_ERROR_BOUND
    else:
        try:
            error_bound = float(request.GET['error_bound'])
        except:
            return JsonResponse(
                {'message:': 'non float error_bound parameter'}, status=422)
    if 'meal_num' not in request.GET:
        meal_num = DEFAULT_NUM_MEALS
    else:
        try:
            meal_num = int(request.GET['meal_num'])
        except:
            return JsonResponse(
                {'message:': 'non int meal_num parameter'}, status=422)

    if not np.isclose(protein_target + carb_target + fat_target, 1):
        return JsonResponse(
            {'message:': 'nutrient percents must add up to 1'}, status=422)

    target_meal_nutrition = MealNutrition(
        kcal=kcal_target,
        protein_percent=protein_target,
        carb_percent=carb_target,
        fat_percent=fat_target)

    serving_nutrition_qs = ServingNutrition.objects.all()
    food_serving_ids_qs = serving_nutrition_qs.values_list(
        'food_serving_id')
    food_serving_ids = [u[0] for u in food_serving_ids_qs]

    kcal_qs = serving_nutrition_qs.filter(nutrient_id=KCAL_ID)
    average_kcal_qs = kcal_qs.aggregate(Avg('nutrient_amount'))
    average_kcal = average_kcal_qs['nutrient_amount__avg']

    init_sample_size = int(math.ceil(kcal_target / average_kcal))

    genetic_population = GeneticFoodPopulation(
        num_samples_per_generation=NUM_SAMPLES_PER_GENERATION,
        init_num_per_sample=init_sample_size,
        selection_param=SELECTION_PARAM,
        mutations_per_generation=MUTATIONS_PER_GEN,
        error_bound=error_bound,
        num_meals_requirement=meal_num,
        food_serving_ids=food_serving_ids,
        serving_nutrition_data_qs=serving_nutrition_qs,
        target_meal_nutrition=target_meal_nutrition)
    genetic_population.generate_initial_population()
    genetic_population.eval_population_fitness()

    while not genetic_population.requirements_met and \
            genetic_population.gen_num < MAX_GENERATIONS_NUM:
        print("""
        Gen: {}: Meals Found: {} Min Fit: {} Mean Fit {}
        """.format(genetic_population.gen_num,
                   len(genetic_population.valid_meals_found),
                   round(np.min(genetic_population.get_fitness_scores()), 3),
                   round(np.mean(genetic_population.get_fitness_scores()), 3)))
        genetic_population.iterate_generation()

    if len(genetic_population.valid_meals_found) == 0:
        return JsonResponse(
            {'message:':
                'cannot find meal, increase error_bound or adjust nutrient%'},
            status=422)

    serialized_meals = serialize_meal_response(
        genetic_population.valid_meals_found)
    return JsonResponse(serialized_meals)
