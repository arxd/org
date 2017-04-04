from plain_txt_db import YAMLSetter

class Ingredient(YAMLSetter):
	""" An ingredient is a certain amount of food, prepared in a certain way.
	Internally the amount is kept in grams to make things easier.  (does it make things easier?)
		\param food is of class Food
		\param amount is always measured in grams.
		\param preperation might be 'sliced', 'steamed', 'sifted', etc.
	"""
	yaml_tag = "!Ingredient"
	yaml_props = {
		'food': None,
		'amount': 1.0,
		'prep':''
	}
	
	volume_units = [('cup', 236.588), ('tbsp', 14.7868), ('tsp',4.9289), ('floz',29.5735), ('ml',1.0)]
	mass_units = [('oz',28.3495), ('g',1.0)]
		
	def __init__(self, **kwargs):
		YAMLSetter.__init__(self, kwargs)

	def __mul__(self, other):
		return Ingredient(food=self.food, amount=self.amount*other, prep=self.prep)

	def guess_unit(self):
		""" Try to guess the best unit to represent this amount in.  There are hints if unit_volume or unit_mass
		is set to 1.0.
		"""
		if self.food.unit_volume == 1.0: # a volume unit would be best
			guess_units = [x[0] for x in Ingredient.volume_units]
		elif self.food.unit_mass == 1.0: # a mass unit would be best
			guess_units = [x[0] for x in Ingredient.mass_units]
		else: # try volume or unit_label fall back on mass
			guess_units = [self.food.unit_label] + [x[0] for x in Ingredient.volume_units] 
		
		# The units are listed in the order of priority so the first one you find wins
		for v,u in  [self.amt(t) for t in guess_units]:
			# Are we close to 1/2 1/3 1/4 etc. of a unit?
			if (v/0.25 + 0.02)%1.0 < 0.04 or (v/ (1.0/3.0) + 0.02)%1.0 < 0.04:
				return u
		return u
		

	def amt(self, unit=None):
		""" Return a tuple (amt, 'unit') of the amount of this ingredient.  
		If you leave unit=None then it tries to guess the best unit.
		"""
		if unit == None:
			unit = self.guess_unit()
			
		# Is the unit a custom food unit (1 egg, 1 stick of butter, 1 carrot)
		if unit == self.food.unit_label:
			return (self.amount / self.food.unit_mass, unit)
			
		# Check volume units
		for u,v in Ingredient.volume_units:
			if u == unit:
				return (self.amount * self.food.unit_volume / self.food.unit_mass / v, unit)
				
		# Maybe it is a mass unit
		for u,v in Ingredient.mass_units:
			if u == unit:
				return (self.amount / v, unit)
		
		# Couldn't find the unit
		raise Exception("%s is not a valid unit"%unit)
	
	def str_amt(self, unit=None):
		""" Convert the floating point amount 1.3333 to a nice 1-1/3
		"""
		amt, unit = self.amt(unit)
		whole, part = divmod(amt, 1)
		if part > 0.875:
			whole += 1
			part = ""
		elif part > .708333:
			part = "3/4"
		elif part > .583333:
			part = "2/3"
		elif part > .416666:
			part = "1/2"
		elif part > .291666:
			part = "1/3"
		elif part > .125:
			part = "1/4"
		else:
			part = ""

		whole = str(int(whole)) if int(whole) else ""		
		return "%s%s%s %s"%(whole, '-' if whole and part else '', part, unit)
	
	def __str__(self):
		return "%s\t: %s"%(self.food.name, self.str_amt())
		


class Recipe(YAMLSetter):
	"""  A Recipe describes how to combine Foods to create a new Food.  """
	yaml_tag="!Recipe"
	yaml_props = {
		'ingredients': [],
		'instructions': [],
	}
	
	def __init__(self, **kwargs):
		YAMLSetter.__init__(self, kwargs)
	
	def __mul__(self, other):
		return Recipe(ingredients = [i*other for i in self.ingredients], instructions = self.instructions)
		
	def __str__(self):
		astr = " == Ingredients ==\n"
		astr += '\n'.join(map(lambda s: '\t'+str(s), self.ingredients))
		astr += "\n == Instructions ==\n"
		astr += '\n'.join(map(lambda s: ' * '+s, self.instructions))
		
		return astr


class Food(YAMLSetter):
	""" A food can be an elementary food (oranges, papurika, water), or a composite recipie (spaghetti sauce, cocoa).
	
	All foods are measured by mass in grams.  Some foods might prefer to be counted (2 carrots, 3 eggs).  In this 
	case you can supply \a unit_mass, which indicates the average mass (in grams) of one 'unit' of this food.  
	Similarly, \a unit_volume allows us to calculate density and convert this unit however we need to.
	
	\param unit_volume : volume in milliliters of one 'unit' of this food.  Should be 1.0 if this is non-countable 
	and usually measured by volume (e.g. Flour). 
	
	\param unit_mass : mass in grams of one 'unit' of this food.  Should be 1.0 if this is non-countable and 
	usually measured by mass (e.g. Meat).
	
	\param tags : Tags is an optional set of categories to put this object into.  (e.g. 'dessert', 'sauce', 'christmas')
	
	\param kcals, protein, carbs, are nutritional facts per gram of food.
	
	\param recipe : This is optional.  It allows us to create this Food from other Foods.  Delicious recursion :)
	"""
	yaml_tag="!Food"
	yaml_props = {
		'name':'',
		'unit_mass': 1.000000001,
		'unit_volume': 1.0,
		'unit_label': '',
		'kcals': -1,
		'protein': -1,
		'carbs': -1,
		'tags': [],
		'description': '',
		'recipe': None,
	}
	
	def __init__(self, **kwargs):
		YAMLSetter.__init__(self, kwargs)
	
	def verbose(self):
		astr = "%s %s\n"%(self.name, ' : '+self.description if self.description else '')
		if self.recipe:
			astr += str(self.recipe) + '\n'
		return astr
		
	def __str__(self):
		return self.name
