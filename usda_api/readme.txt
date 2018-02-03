Readme

Dependencies/Installation Instructions

1. Anaconda 3.6 Distribution
Download here: https://www.anaconda.com/download/

2. Django ORM
conda install django

I have run and tested on the latest versions of Anaconda/Django(older versions may work)


Running the WebServer

1. Unzip the usda_api.zip anywhere locally
2. Navigate to the usda_api directory
3. python manage.py runserver 8000
4. Open a browser and send API request in this format:
	http://localhost:8000/api/getmeal/?kcal=780&protein=0.2&carb=0.5&fat=0.3
5. For testing, optionally add two additional arguments
	a. meal_num: will look for at least n number of valid meals, defaults to 1
	b. error_bound: valid error bound in decimal form, defaults to 0.04 
	http://localhost:8000/api/getmeal/?kcal=780&protein=0.2&carb=0.5&fat=0.3&error_bound=0.1&meal_num=4
6. In the usda_api/test folder, there is a test_api.py script that will send a request to localhost 
and test output against a local pickle version of the database


Notes/Description

Since the goal is to quickly find an acceptable matching ingredient set, it uses a genetic algorithm to find candidates
and then selects the 'fittest' for the next round. It then randomly adds/removes/replaces an ingredient for each of the 
new candidates. This iterates until a viable candidate is found. Alternatively, a linear programming solution likely takes longer but
may be better for finding maximum fit(i.e set that comes closest to the nutrition parameters)

Some input sets will result in no 'meals' being found. For example asking for a 99% fat meal with 10000 kcal will
result in it hitting the maximum number of iterations(currently defaults to 25 generations).
Average protein/carb/fat in grams is 20/18/14 so weights that deviate from this drastically will be harder to match. 
Small kcal input will make it very difficult to match as there can only be a few ingredients in a set. 
The output is also non-deterministic, a caching layer can be added to ensure that the same input params output the same results. 

I've chosen reasonable default settings but the parameters can certainly be tuned. For example if kcal input is expected to be large,
then the mutation rate should be increased to get faster convergence. Right now it is set to 1 for ~2000kcal input. 
Also, I've just used the sqlite db as is in the link. Storing the data as key value pairs precached in memory(sorted keys for binary search lookups) will be faster. 

The output is in this format:
meal number: meal

meal contains 4 keys

1. kcal
2. protein %
3. fat %
4. carb %
5. ingredient_list: this is a list containing the food short desc and the serving size
6. fitness_score: this is the sum of the absolute percentile differences	


Example output:

http://localhost:8000/api/getmeal/?kcal=780&protein=0.2&carb=0.5&fat=0.3

{"0": {"ingredients": [{"short_description": "MILK,FILLED,FLUID,W/LAURIC ACID OIL", "serving_size": "fl oz"}, {"short_description": "GRAPEFRUIT,RAW,PINK & RED,FLORIDA", "serving_size": "cup sections, with juice"}, {"short_description": "PORK,FRSH,VAR MEATS&BY-PRODUCTS,TAIL,CKD,SIMMRD", "serving_size": "piece, cooked, excluding refuse (yield from 1 lb raw meat with refuse)"}, {"short_description": "ROLLS,DINNER,RYE", "serving_size": "medium"}], "fitness_score": 0.06775201765145736, "kcal": 775.0, "protein_percent": 0.2239620744145956, "carb_percent": 0.46932911937939953, "fat_percent": 0.3067088062060049}}

