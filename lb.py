"""
6.101 Lab:
Recipes
"""

import pickle
import sys
# import typing # optional import
# import pprint # optional import

sys.setrecursionlimit(20_000)
# NO ADDITIONAL IMPORTS!


def atomic_ingredient_costs(recipes_db):
    """
    Given a recipes database, a list containing compound and atomic food tuples,
    make and return a dictionary mapping each atomic food name to its cost.
    """
    recipe_to_cost = {}
    for recipie in recipes_db:
        if(recipie[0] == 'atomic'):
            recipe_to_cost[recipie[1]] = recipie[2]
    return recipe_to_cost


def compound_ingredient_possibilities(recipes_db):
    """
    Given a recipes database, a list containing compound and atomic food tuples,
    make and return a dictionary that maps each compound food name to a
    list of all the ingredient lists associated with that name.
    """
    recipe_to_ingridient = {}
    for recipie in recipes_db:
        if(recipie[0] == 'compound'):
            if(recipie[1] in recipe_to_ingridient):
                recipe_to_ingridient[recipie[1]].append(recipie[2])
            else:
                recipe_to_ingridient[recipie[1]] = []
                recipe_to_ingridient[recipie[1]].append(recipie[2])
    return recipe_to_ingridient
    


def lowest_cost(recipes_db, food_name, forbidden_item = None):
    """
    Given a recipes database and the name of a food (str), return the lowest
    cost of a full recipe for the given food item or None if there is no way
    to make the food_item.
    """
    atomic_dic = atomic_ingredient_costs(recipes_db)
    compound_dic = compound_ingredient_possibilities(recipes_db)
    if(forbidden_item != None):
        for items in forbidden_item:
            if(items in atomic_dic):
                del atomic_dic[items]
            if(items in compound_dic):
                del compound_dic[items]
    def helper(f):
        min_cost = 9999999
        if(f not in atomic_dic and f not in compound_dic):
            return
        if(f in atomic_dic):
            return atomic_dic[f]
        else:
            if(f in compound_dic):
                for recipe in compound_dic[f]:
                    cost = 0
                    ingridient_missing = False
                    for ingridient in recipe:
                        catch = helper(ingridient[0]) 
                        if(catch == None):
                            ingridient_missing = True 
                            break 
                        cost = cost + catch * ingridient[1]
                    if(not(ingridient_missing)):
                        if (cost < min_cost):
                            min_cost = cost
        if(min_cost != 0 and min_cost != 9999999):                
            return min_cost
    return helper(food_name)






def scaled_recipe(recipe_dict, n):
    """
    Given a dictionary of ingredients mapped to quantities needed, returns a
    new dictionary with the quantities scaled by n.
    """
    new_dic = {}
    for key, values in recipe_dict.items():
        new_dic[key] = values * n
    return new_dic



def add_recipes(recipe_dicts):
    """
    Given a list of recipe dictionaries that map atomic food items to quantities,
    return a new dictionary that maps each ingredient name
    to the sum of its quantities across the given recipe dictionaries.

    For example,
        add_recipes([{'milk':1, 'chocolate':1}, {'sugar':1, 'milk':2}])
    should return:
        {'milk':3, 'chocolate': 1, 'sugar': 1}
    """
    new_dic = {}
    for dic in recipe_dicts:
        for key, value in dic.items():
            if(key in new_dic):
                new_dic[key] += value
            else:
                new_dic[key] = value
    return new_dic


def cheapest_flat_recipe(recipes_db, food_name, forbidden_item = None):
    """
    Given a recipes database and the name of a food (str), return a dictionary
    (mapping atomic food items to quantities) representing the cheapest full
    recipe for the given food item.

    Returns None if there is no possible recipe.
    """
    #Observation - right now you are finding local minimum sure, as in the cheapest way to make the ingridients of a burger but there might be a burger with cheaper ingridients
    # Deleting the item in dictionary is weak because the ingridients can be compound as well
    atomic_dic = atomic_ingredient_costs(recipes_db)
    compound_dic = compound_ingredient_possibilities(recipes_db)
    master_dic = {}
    atomic_list = []
    if(forbidden_item != None):
        for items in forbidden_item:
            if(items in atomic_dic):
                del atomic_dic[items]
            if(items in compound_dic):
                del compound_dic[items]
    if(food_name in atomic_dic):
        return {food_name : 1}
    def helper(f):
        min_cost = 9999999
        if(f not in atomic_dic and f not in compound_dic):
            return
        if(f in atomic_dic):
            return atomic_dic[f]
        else:
            if(f in compound_dic):
                for recipe in compound_dic[f]:
                    cost = 0
                    ingridient_missing = False
                    for ingridient in recipe:
                        catch = helper(ingridient[0]) 
                        if(catch == None):
                            ingridient_missing = True 
                            break 
                        cost = cost + catch * ingridient[1]
                    if(not(ingridient_missing)):
                        if (cost < min_cost):
                            min_cost = cost
                            placeholder ={}
                            for key,value in recipe:
                                placeholder[key] = value
                            master_dic[f] = placeholder
        if(min_cost != 0 and min_cost != 9999999):                
            return min_cost
    helper(food_name)
    if(food_name not in master_dic):
        return None
    masterfood = master_dic[food_name]
    def subhelper(food):
        tmp = {}
        for key, value in food.items():
            if(key in atomic_dic):
                tmp[key] = value 
            else:
                subhelper(scaled_recipe(master_dic[key], value))
        atomic_list.append(tmp)
    
    subhelper(masterfood)
    result = add_recipes(atomic_list)
    return result




def combine_dic(dic1, dic2):
    res = {}
    for key in dic1:
        if(key in dic2):
            res[key] = dic1[key] + dic2[key]
        else:
            res[key] = dic1[key]
    for key in dic2:
        if key not in dic1:
            res[key] = dic2[key]
    return res 


def combine_recipes(nested_recipes):
    """
    Given a list of lists of recipe dictionaries, where each inner list
    represents all the recipes for a certain ingredient, compute and return a
    list of recipe dictionaries that represent all the possible combinations of
    ingredient recipes.
    inp = [
    [{'peanut': 10}, {'almond': 10}],  # flat recipes for nut butter
    [{'grape': 20, 'sugar': 10}, {'trawberry': 5, 'sugar': 10}], # flat recipes for jelly
    [{'flour': 6, 'sugar': 2}] # flat recipes for bread
    ]
    """
    
    def helper(s):
        if not s:
            return [{}]
        else:
            first = s[0]
            rest = s[1:]
            rest_seq = helper(rest)
            first_seq = []
            for seq in rest_seq:
                for dic in first:
                    first_seq.append(combine_dic(dic, seq))
            return first_seq
    return helper(nested_recipes)



def all_flat_recipes(recipes_db, food_name, forbidden_item = None):
    """
    Given a recipes database, the name of a food (str), produce a list (in any
    order) of all possible flat recipe dictionaries for that category.

    Returns an empty list if there are no possible recipes
    """
    
    #cheese - > (milk , time), cutting edge lab
    #.  milk - >  cow, stool
    atomic_dic = atomic_ingredient_costs(recipes_db)
    compound_dic = compound_ingredient_possibilities(recipes_db) # lists a compound ingridient to its recipies, can have multiple recipes
    if(forbidden_item != None):
        for items in forbidden_item:
            if(items in atomic_dic):
                del atomic_dic[items]
            if(items in compound_dic):
                del compound_dic[items]
    if(food_name in atomic_dic):
        return [{food_name : 1}]
    def helper(food):
        res = []
        final = []
        if food in atomic_dic:
            return [{food: 1}]
        else:
            if(food not in atomic_dic and food not in compound_dic):
                return []
            for recipe in compound_dic[food]:
                catch = []
                for ingridient in recipe:
                    catch.append(helper(ingridient[0]))
                    for j in range(len(catch[-1])):
                        dic = catch[-1][j]
                        dic = scaled_recipe(dic, ingridient[1])
                        catch[-1][j] = dic
                res.append(combine_recipes(catch))
            for lst in res:
                final += lst
            return final

            
            
                
    return helper(food_name)
                  
    


def _filter_graph(graph, elts):
    elts = set(elts)
    return [i for i in graph if i[1] not in elts]

if __name__ == "__main__":
    # load recipe databases from the write-up
    with open("test_recipes/example_recipes.pickle", "rb") as f:
        example_recipes_db = pickle.load(f)

    with open("test_recipes/dairy_recipes.pickle", "rb") as f:
        dairy_recipes_db = pickle.load(f)

    with open("test_recipes/cookie_recipes.pickle", "rb") as f:
        cookie_recipes_db = pickle.load(f)
    with open("test_recipes/big_recipes_16.pickle", "rb") as f:
        big = pickle.load(f)
    
    #print(all_flat_recipes(example_recipes_db, "proteim", ["cow"]))
    #print(all_flat_recipes(cookie_recipes_db, "cookie sandwich"))
   