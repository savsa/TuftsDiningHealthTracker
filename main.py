import webapp2
import jinja2
import requests
import json
import base64
import os
import time
import logging

import config
import datetime
import string
import random

from google.appengine.ext import deferred
from google.appengine.ext import ndb

import requests_toolbelt.adapters.appengine
requests_toolbelt.adapters.appengine.monkeypatch()

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

dining_options = [
    'dewick',
    'carm',
    # 'commons',
    # 'paxetlox',
    # 'brownandbrew',
    # 'hodgdon',
    # 'mugar',
    # 'tower',
]
meal_periods = [
    'Breakfast',
    'Lunch',
    'Dinner'
]

breakfast_meal_types = [
    'BREAKFAST DAIRY & FRUIT BAR',
    'BRK BREADS,PASTRIES & TOPPINGS',
    'BREAKFAST POTATO',
    'HOT BREAKFAST CEREAL BAR',
    'BREAKFAST MEATS',
    'BREAKFAST ENTREE',
]

lunch_meal_types = [
    'PIZZA'
    'SALAD BAR DAIRY & FRUIT',
    'LUNCH ENTREE',
    'VEGETARIAN OPTIONS',
    'PASTA & SAUCES',
    'SPECIALTY SALADS',
    'FRESH BAKED DESSERTS',
    'POTATO & RICE ACCOMPANIMENTS',
    'BREAKFAST ENTREE',
    'DELI & PANINI',
    'BREADS & ROLLS',
    'Hearty Soups',
    'BREAKFAST MEATS',
    'SAUCES,GRAVIES & TOPPINGS',
    'CHAR-GRILL STATIONS',
    'VEGETABLES',
]

dinner_meal_types = [
    'PIZZA',
    'DINNER ENTREES',
    'VEGETARIAN OPTIONS',
    'PASTA & SAUCES',
    'SPECIALTY SALADS',
    'SALAD BAR DAIRY & FRUIT',
    'POTATO & RICE ACCOMPANIMENTS',
    'CHAR-GRILL STATIONS',
    'VEGETABLES',
    'Hearty Soups',
    'NOODLERY & STIR FRY',
    'FRESH BAKED DESSERTS',
    'DELI & PANINI',
]

class MenuItem(ndb.Model):
    name = ndb.StringProperty()
    calories = ndb.IntegerProperty()
    meal_period = ndb.StringProperty()

class Food:
    def __init__(self, name, meal_period):
        self.name = name
        self.meal_period = meal_period

class PopulateDatabase(webapp2.RequestHandler):
    def get(self):
        # /hall/day/month/year
        date = datetime.datetime.now()


        ## get all the different foods from the menus
        foods = []
        for dining_option in dining_options:
            print(dining_option.upper())
            menu_endpoint = 'https://tuftsdiningdata.herokuapp.com/rmenus/{}/{}/{}/{}'.format(dining_option, date.day, date.month, date.year)
            menu = requests.get(menu_endpoint)
            menu_json = menu.json()
            menu_data = menu_json['data']
            print(menu_data)

            # get all the breakfast items
            breakfast = menu_data['Breakfast']
            for i in range(0, len(breakfast_meal_types)):
                try:
                    # foods = foods + breakfast[breakfast_meal_types[i]]

                    for j in range(0, len(breakfast[breakfast_meal_types[i]])):
                        food_obj = Food(breakfast[breakfast_meal_types[i]][j], "breakfast")
                        foods.append(food_obj)
                except KeyError:
                    continue

            # get all the lunch items
            lunch = menu_data['Lunch']
            for i in range(0, len(lunch_meal_types)):
                try:
                    # foods = foods + lunch[lunch_meal_types[i]]
                    for j in range(0, len(lunch[lunch_meal_types[i]])):
                        food_obj = Food(lunch[lunch_meal_types[i]][j], "lunch")
                        foods.append(food_obj)
                except KeyError:
                    continue

            # get all the dinner items
            dinner = menu_data['Dinner']
            for i in range(0, len(dinner_meal_types)):
                try:
                    for j in range(0, len(dinner[dinner_meal_types[i]])):
                        food_obj = Food(dinner[dinner_meal_types[i]][j], "dinner")
                        foods.append(food_obj)
                except KeyError:
                    continue

        # get all the nutrition information from each of the food items
        for food in foods:
            actual_item = food.name;
            food_formatted = actual_item.replace(" ", "%20")
            ingredients_endpoint = 'https://tuftsdiningdata.herokuapp.com/ingredients/{}'.format(food_formatted)
            # print(ingredients_endpoint)
            ingredients = requests.get(ingredients_endpoint)
            print(ingredients)

            try:
                ingredients_json = ingredients.json()
            except ValueError:
                continue


            try:
                calories = ingredients_json['calories']

                menu_item = MenuItem(
                    name=food.name,
                    calories=calories,
                    meal_period=food.meal_period
                )
                menu_item.put()
            except KeyError:
                continue


        template = env.get_template('populate.html')
        self.response.write(template.render())


class Home(webapp2.RequestHandler):
    def get(self):

        template = env.get_template('index.html')
        self.response.write(template.render())

class Results(webapp2.RequestHandler):
    def get(self):
        calories = self.request.get('calories')
        calories = int(calories)
        # num_meals = self.request.get('meals')
        num_meals = 3

        calories_per_meal = calories / num_meals
        foods = MenuItem.query()

        # Breakfast
        breakfast_cals_left = calories_per_meal
        recommended_breakfast = []
        while breakfast_cals_left > 0:
            breakfast = MenuItem.query().filter(MenuItem.meal_period == 'breakfast',
                                                MenuItem.calories <= (breakfast_cals_left))
            for food in breakfast:
                if (food.calories > 80):
                    recommended_breakfast.append(food.name)
                    breakfast_cals_left = breakfast_cals_left - food.calories
                if breakfast_cals_left < 0:
                    break
        # Lunch
        lunch_cals_left = calories_per_meal
        recommended_lunch = []
        while lunch_cals_left > 50:
            lunch = MenuItem.query().filter(MenuItem.meal_period == 'lunch',
                                                MenuItem.calories <= (lunch_cals_left))
            for food in lunch:
                if (food.calories > 150):
                    recommended_lunch.append(food.name)
                    lunch_cals_left = lunch_cals_left - food.calories
                    print(food.calories)
                    print(lunch_cals_left)
                    if lunch_cals_left < 0:
                        break

        # Dinner
        dinner_cals_left = calories_per_meal
        recommended_dinner = []
        while dinner_cals_left > 50:
            dinner = MenuItem.query().filter(MenuItem.meal_period == 'dinner',
                                                MenuItem.calories <= (dinner_cals_left))
            for food in dinner:
                if (food.calories > 150):
                    recommended_dinner.append(food.name)
                    dinner_cals_left = dinner_cals_left - food.calories
                if dinner_cals_left < 0:
                    break

        template_vars = {
            "recommended_breakfast" : recommended_breakfast,
            "recommended_lunch" : recommended_lunch,
            "recommended_dinner" : recommended_dinner,
        }

        template = env.get_template('results.html')
        self.response.write(template.render(template_vars))


app = webapp2.WSGIApplication([
    ('/', Home),
    ('/populate', PopulateDatabase),
    ('/results', Results),
], debug=True)