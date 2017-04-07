#!/usr/bin/python3
import sys
from PlainTxtDB import DB
from Food import *

g_usage = """
USAGE:

	Pass a string of commands and they will be done in sequence.  
	If you want to load a particular databse then load 'dbname' should be 
	the first command. Otherwise and implicit load 'db/food' is 
	done for you.
	
EXAMPLES:

	To show all of the foods
		./FoodCMD.py list
		
	To show a particular food
		./FoodCMD.py food "Eggy Sauce" show
		
	To change the description of a food
		./FoodCMD.py food ham set description "Comes from Pigs" save
		
	To copy the db to a new location
		./FoodCMD.py load "db/foods1" list save "db/foods2"

COMMANDS:"""


g_cmds = {}
g_dbname = ''
g_foods = None
g_food = None

def cmd(func):
	def do_cmd(args, kvargs):
		print("\n_____%s %s %s\n"%(func.__name__, args, kvargs))
		func(*args, **kvargs)
	# add the command to the global set of commands
	global g_cmds
	do_cmd.__doc__ = func.__doc__
	g_cmds[func.__name__] = do_cmd
	return func

@cmd
def set(attr, value):
	"""
	set ATTR VALUE
		Set the current working food's attribute ATTR to VALUE
		ATTR must be one of :
		  * kcals
		  * protein
		  * carbs
		  * unit_mass
		  * unit_volume
		  * unit_label
		  * description
	"""
	global g_food
	if not g_food:
		raise Exception("You must select a food first.  use cmd 'food' before 'set'")
	
	if attr not in ['kcals', 'protein', 'carbs', 'unit_mass', 'unit_volume', 'unit_label', 'description']:
		raise Exception("You cannot set attribute '%s'."%attr)
	
	if attr in ['kcals', 'protein', 'carbs', 'unit_mass', 'unit_volume']:
		value = float(value)
	
	setattr(g_food, attr, value)
	

@cmd
def show(factor=1.0):
	"""
	show [FACTOR]
		Show all the information about the current food.
		Optionally scale the recipe by FACTOR (eg 2.0 or 0.5)
	"""
	global g_food
	print(g_food.scale(float(factor)).verbose())
	

@cmd
def list(tagexpr='', verbose=False):
	"""
	list [TAGEXPR]
		You can specify a TAGEXPR to filter the results.
		The tag name 'recipe' filters for foods that have a recipe.
		
		Examples:
		
		list dessert                         # List only desserts
		list -dessert			     # List everything EXCEPT
							desserts
		list "ice cream, cake"               # ice cream or cake
		list "dessert & -(cake, ice cream)"  # Dessert but no cake or 
							ice cream
		list "dessert & healthy & delicious" # Only healty, delicious
							desserts
	"""
	global g_foods
	for f in Tag.filter(g_foods, tagexpr):
		if verbose:
			print(f.verbose())
		else:
			print(" - %s%s%s  %s"%(f, ' : ' if f.description else '', f.description, '<' + '> <'.join(f.tags) + '>'))

@cmd
def new(name, desc=""):
	"""
	new NAME [DESC]
		If food does not exist then create it with optional
		description DESC.
		Set food NAME as the current working food.
	"""
	global g_foods, g_food
	if name in g_foods:
		g_food = g_foods[g_foods.index(name)]
	else:
		g_food = Food(name=name, description=desc)
		g_foods.append(g_food)

@cmd
def food(name):
	"""
	food NAME
		Set food NAME as the current working food.
	"""
	global g_foods, g_food
	if name not in g_foods:
		raise Exception("'%s' does not exist.  Create it with the 'new' command."%name)
	g_food = g_foods[ g_foods.index(name)]


@cmd
def delete(name):
	"""
	delete NAME
		Delete the food NAME from the database.  You cannot delete 
		a food that is used as an ingredient.
	"""
	global g_foods, g_food
	if max([ing==name for food in g_foods for ing in food.ingredients]):
		print("'%s' is used as an ingredient.  It cannot be deleted"%name)
		return
	if g_food == name:
		g_food = None
	if name not in g_foods:
		print("Couldn't find '%s'"%name)
	g_foods.remove(name)

@cmd
def load(dbname='db/food'):
	"""
	load [DBNAME]
		Loads a food database DBNAME.
		This command is optional.  It is implicitly added as the first 
		command if missing.
	"""
	global g_foods, g_dbname
	g_foods, name = DB.load(dbname)
	g_dbname = dbname


@cmd
def save(dbname=None):
	"""
	save [DBNAME]
		Save the current foods to DBNAME.  Or back where it came 
		from if no DBNAME is given.
	"""
	global g_foods, g_dbname
	if not dbname:
		dbname = g_dbname
	g_dbname = dbname
	DB.save(g_foods, g_dbname)

@cmd
def ingd(food, amount, prep=""):
	"""
	ingd FOOD AMOUNT [PREP]
		Add an ingredient to the current food.
		The AMOUNT can be a easy string "1 1/2 cup" 
		PREP is an optional preperation ("sliced", "diced", etc.)
	"""
	global g_food, g_foods
	assert(g_food)
	if food not in g_foods:
		raise Exception("'%s' is not a food"%food)
	g_food.add_ingredient(g_foods[g_foods.index(food)], amount, prep)
	
@cmd
def inst(text):
	"""
	inst TEXT
		Add a new instruction to the recipe.
	"""
	global g_food
	assert(g_food)
	g_food.instructions.append(text)
	

@cmd
def tag(name):
	"""
	tag NAME
		Add tag NAME to the current working food.
	"""
	global g_food
	assert(g_food)
	g_food.add_tag(name)
	

if __name__=='__main__':
	try:
		argv = sys.argv[1:] # get rid of the name of the file
		# implicity add 'load' as the first command if needed
		if argv[0] != 'load':
			argv = ['load'] + argv
		
		while argv:
			# find the next_cmd
			next_cmd = 1
			while next_cmd < len(argv) and argv[next_cmd] not in g_cmds:
				next_cmd += 1
			
			args = []
			argkv = {}
			#last=next_cmd
			for i, arg in enumerate(argv[1:next_cmd]):
				if '=' in arg:
					k,v = arg.split('=')
					argkv[k]=v
				else:
					args.append(arg)
					
			g_cmds[argv[0]](args, argkv)
			argv = argv[next_cmd:]
			
	except (KeyError, IndexError, TypeError) as  e:
		print(g_usage)
		for c in g_cmds:
			print(g_cmds[c].__doc__)
