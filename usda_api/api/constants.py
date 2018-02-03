'''
Created on Jan 20, 2018

@author: ygu
'''

# GA Params

# Number of candidate samples per generation
NUM_SAMPLES_PER_GENERATION = 40
# Selection rate, takes the top 100/N percentile to keep for the next
# generation
SELECTION_PARAM = 4
# Number of mutations(add/remove/replace) per generation
MUTATIONS_PER_GEN = 1
# Maximum number of generations before exiting
MAX_GENERATIONS_NUM = 25

PROTEIN_ID = 203
FAT_ID = 204
CARB_ID = 205
KCAL_ID = 208

DEFAULT_ERROR_BOUND = 0.04
DEFAULT_NUM_MEALS = 1

REMOVE_MUTATION = 'remove_mutation'
ADD_MUTATION = 'add_mutation'
REPLACE_MUTATION = 'replace_mutation'
