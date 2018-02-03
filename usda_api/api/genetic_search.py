'''
Created on Jan 19, 2018

@author: ygu
'''
from collections import Counter
import heapq
import itertools
from random import randint
import random

from django.db.models import Sum
from numpy import array

import numpy as np

from .constants import KCAL_ID, PROTEIN_ID, FAT_ID, CARB_ID
from .constants import REMOVE_MUTATION, ADD_MUTATION, REPLACE_MUTATION
from .meal import Ingredient
from .meal import Meal
from .meal import MealNutrition
from .meal import fitness_function
from .meal import is_within_error_bounds


class GeneticFoodPopulation:

    def __init__(self,
                 num_samples_per_generation,
                 init_num_per_sample,
                 selection_param,
                 mutations_per_generation,
                 error_bound,
                 num_meals_requirement,
                 food_serving_ids,
                 serving_nutrition_data_qs,
                 target_meal_nutrition):
        """
        Finds valid food servings combinations that
        fit the target_meal_nutrition criteria using a selection/mutation algorithm

        @param num_samples_per_generation: Number of candidate samples per generation
        @param init_num_per_sample: Mean initial number of samples.
        Sample counts will be a distribution around the mean(1-2x value)
        @param selection_param: Selection rate, takes the top 100/N percentile
        to keep for the next generation
        @param mutations_per_generation: Number of mutations(add/remove/replace)
        per generation
        @param error_bound: Maximum percentile difference for EACH nutrient
        @param num_meals_requirement: Find at least n meals
        @param food_serving_ids: List of candidate Food Serving Ids
        @param serving_nutrition_data_qs: Serving Nutrition Data
        @param target_meal_nutrition: Target MealNutrition
        """

        self.num_samples_per_generation = num_samples_per_generation
        self.init_num_per_sample = init_num_per_sample
        self.selection_param = selection_param
        self.mutations_per_generation = mutations_per_generation
        self.error_bound = error_bound
        self.num_meals_requirement = num_meals_requirement
        self.gen_num = 0
        self.population = []
        self.population_fitness = []
        self.valid_meals_found = []
        self.requirements_met = False
        self.food_serving_ids = food_serving_ids
        self.serving_nutrition_data_qs = serving_nutrition_data_qs
        self.target_meal_nutrition = target_meal_nutrition

    def iterate_generation(self):
        """
        Iterate to next generation
        """
        self.perform_selection()
        self.mutate_population()
        self.eval_population_fitness()
        self.gen_num += 1

    def eval_population_fitness(self):
        population_fitness_results = []
        for sample in self.population:
            sample_meal_nutrition = self.calculate_sample_meal_nutrition(
                sample=sample)
            sample_fitness = fitness_function(
                sample_meal_nutrition=sample_meal_nutrition,
                target_meal_nutrition=self.target_meal_nutrition
            )
            is_within_bounds = is_within_error_bounds(
                sample_meal_nutrition=sample_meal_nutrition,
                target_meal_nutrition=self.target_meal_nutrition,
                error_bound=self.error_bound)

            population_fitness_results.append((sample,
                                               sample_meal_nutrition,
                                               sample_fitness))
            if is_within_bounds:
                if self.is_valid_sample(sample):
                    ingredients_qs = self.serving_nutrition_data_qs.filter(
                        food_serving_id__in=sample).filter(nutrient_id=KCAL_ID)
                    ingredient_list = []
                    for ingredient in ingredients_qs:
                        short_desc = ingredient.short_desc
                        serving_size = ingredient.serving_size
                        food_serving_id = ingredient.food_serving_id
                        ingredient_list.append(
                            Ingredient(food_serving_id,
                                       short_description=short_desc,
                                       serving_size=serving_size))
                    self.valid_meals_found.append(Meal(
                        food_serving_ids=sample,
                        fitness_score=sample_fitness,
                        meal_nutrition=sample_meal_nutrition,
                        ingredient_list=ingredient_list))

            if len(self.valid_meals_found) >= self.num_meals_requirement:
                self.requirements_met = True
        self.population_fitness = population_fitness_results

    def get_fitness_scores(self):
        fitness_scores = np.array([s[2] for s in self.population_fitness])
        return fitness_scores

    def perform_selection(self):
        """
        Performs the selection step:
        1. Chooses top n percentile most fit based on selection param
        2. Duplicates those selected(no crossover)
        """
        fitness_scores = self.get_fitness_scores()
        best_fit_index = heapq.nsmallest(
            int(len(fitness_scores) / self.selection_param),
            range(len(fitness_scores)),
            fitness_scores.take)
        best_fit_population = array(self.population)[
            best_fit_index].tolist()
        next_gen_population = best_fit_population * self.selection_param
        self.population = next_gen_population

    def mutate_population(self):
        """
        Mutates the population by performing
        randomized mutations(add/remove/replace) on each of the samples

        Default probabilities:
        30% Add
        30% Remove
        40% Replace
        """
        new_sample_population = []
        for sample in self.population:
            new_sample = list(sample)
            mutation_action = self.generate_random_mutation_action()

            if mutation_action == REMOVE_MUTATION:
                for _ in itertools.repeat(
                        None, self.mutations_per_generation):
                    # Skip remove if it results in an empty sample
                    if len(new_sample) >= 2:
                        new_sample.pop(
                            random.randint(
                                0,
                                len(new_sample) -
                                1))
            elif mutation_action == ADD_MUTATION:
                new_sample.extend(
                    random.sample(
                        self.food_serving_ids,
                        self.mutations_per_generation))
            else:
                for _ in itertools.repeat(
                        None, self.mutations_per_generation):
                    replace_found = 0
                    while not replace_found:
                        replace_selection = random.sample(
                            self.food_serving_ids,
                            1)
                        if replace_selection not in new_sample:
                            new_sample[
                                random.randint(
                                    0,
                                    len(new_sample) -
                                    1)] = replace_selection[0]
                            replace_found = 1
            # If sample is valid(No more than 2 of the same food)
            # Else keep old sample
            if self.is_valid_sample(new_sample):
                new_sample_population.append(new_sample)
            else:
                new_sample_population.append(sample)
        self.population = new_sample_population

    def generate_initial_population(
            self):
        """
        Generate initial population
        """
        assert self.num_samples_per_generation >= 1, \
            'num_samples_per_generation must be >= 1'
        assert self.init_num_per_sample >= 1, \
            'init_num_per_sample must be >= 1'
        assert len(self.food_serving_ids) >= self.init_num_per_sample * 2, \
            'insufficient number of food_serving_ids to support sample size'

        init_population = []
        for _ in itertools.repeat(None, self.num_samples_per_generation):
            valid_sample_found = 0
            while not valid_sample_found:
                random_sample_number = randint(
                    1,
                    self.init_num_per_sample *
                    2)
                random_sample = random.sample(
                    self.food_serving_ids,
                    random_sample_number)
                if self.is_valid_sample(random_sample):
                    init_population.append(random_sample)
                    valid_sample_found = 1
        self.population = init_population

    def calculate_sample_meal_nutrition(self,
                                        sample):
        """
        Calculate the sample's MealNutrition

        @param sample: List of Food Serving Ids
        """
        sample_qs = self.serving_nutrition_data_qs.filter(
            food_serving_id__in=sample)
        assert len(sample) > 0, 'no food servings in sample'        

        kcal_sum = get_sample_kcal_sum(sample_qs)
        protein_grams_sum = get_sample_protein_grams_sum(sample_qs)
        carb_grams_sum = get_sample_carb_grams_sum(sample_qs)
        fat_grams_sum = get_sample_fat_grams_sum(sample_qs)

        sum_grams = protein_grams_sum + carb_grams_sum + fat_grams_sum
        if np.isclose(sum_grams, 0):
            return MealNutrition(kcal=kcal_sum,
                                 protein_percent=0,
                                 carb_percent=0,
                                 fat_percent=0)
        sample_meal_nutrition = MealNutrition(
            kcal=kcal_sum,
            protein_percent=protein_grams_sum / sum_grams,
            carb_percent=carb_grams_sum / sum_grams,
            fat_percent=fat_grams_sum / sum_grams)
        return sample_meal_nutrition

    def is_valid_sample(self, food_serving_ids):
        """
        Check that there are no more than two food serving
        sizes of the same food in the sample.
        This should be rare given randomized nature of the sampling and the
        number of potential selections in the DB

        @param food_serving_ids: List of food_serving_ids in the sample
        """
        food_ids = [f.split('_')[0] for f in food_serving_ids]
        food_counter = Counter(food_ids)
        counts = list(food_counter.values())
        return all([x <= 2 for x in counts])

    def generate_random_mutation_action(self):
        rdm = randint(1, 100)
        action = ''
        if rdm >= 1 and rdm <= 30:
            action = REMOVE_MUTATION
        elif rdm <= 60:
            action = ADD_MUTATION
        else:
            action = REPLACE_MUTATION
        return action


def get_sample_kcal_sum(sample_qs):
    kcal_sum = sample_qs.filter(
        nutrient_id=KCAL_ID).aggregate(
        Sum('nutrient_amount'))['nutrient_amount__sum']
    return kcal_sum


def get_sample_protein_grams_sum(sample_qs):
    protein_grams_sum = sample_qs.filter(
        nutrient_id=PROTEIN_ID).aggregate(
        Sum('nutrient_amount'))['nutrient_amount__sum']
    return protein_grams_sum


def get_sample_fat_grams_sum(sample_qs):
    fat_grams_sum = sample_qs.filter(
        nutrient_id=FAT_ID).aggregate(
        Sum('nutrient_amount'))['nutrient_amount__sum']
    return fat_grams_sum


def get_sample_carb_grams_sum(sample_qs):
    carb_grams_sum = sample_qs.filter(
        nutrient_id=CARB_ID).aggregate(
        Sum('nutrient_amount'))['nutrient_amount__sum']
    return carb_grams_sum
