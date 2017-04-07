"""
There are two classes:  Food and Ingredient.
A Food can be a recipe (Cookies) or a basic food (Apple, Cinnamon).
An Ingedient is an amount of food (in grams).
"""

from PlainTxtDB import YAMLSetter, Tag

class Ingredient(YAMLSetter):
	""" An ingredient is a certain amount of food, prepared in a certain way.
		\param food: is of class Food
		\param amount: A floating point amount of this ingredient 
		'param unit: The units for the amount ('cup', 'floz', etc.).  An empty string indicates pieces (2 eggs)
		\param prep:  might be 'sliced', 'steamed', 'sifted', etc.
	"""
	yaml_tag = "!Ingredient"
	yaml_props = {
		'food': None,
		'amount': 0.0,
		'unit':'',
		'prep':''
	}
	
	VOLUME_UNITS = ['cup', 'tbsp', 'tsp', 'floz', 'ml']
	MASS_UNITS = ['oz', 'g']
	UNITS = {'cup':236.588, 'tbsp':14.7868, 'tsp':4.9289, 'floz':29.5735, 'ml':1.0, 'oz':28.3495, 'g':1.0}
	
	def __init__(self, **kwargs):
		YAMLSetter.__init__(self, kwargs)

	def __mul__(self, factor):
		return Ingredient(food=self.food, amount=self.amount*factor, unit = self.unit, prep=self.prep)

	def __imul__(self, factor):
		self.amount *= factor
		return self

	def __eq__(self, other):
		return self.food.name == str(other)

	def all_units(self):
		return [self.food.unit_label] + Ingredient.VOLUME_UNITS + Ingredient.MASS_UNITS
		
	def set(self, amt):
		""" Set the amount with a string like '1 2/3 cup' or '33.5 g'
		If amt is a number (float/int) then just set the amout without setting the units.
		"""
		if isinstance(amt, str):
			amt = list(filter(lambda x: x, amt.split(' ')))
			if len(amt) == 1: # units
				value = float(amt[0])
				unit = ''
			elif len(amt) == 2 and '/' in amt[0]: # frac unit
				a, b = amt[0].split('/')
				value = float(a) / float(b)
				unit = amt[1]
			elif len(amt) == 2 and '/' in amt[1]: # whole frac
				a, b = amt[1].split('/')
				value = float(amt[0]) + float(a) / float(b)
				unit = ''
			elif len(amt) == 2: # whole unit
				value = float(amt[0])
				unit = amt[1]
			elif len(amt) == 3: # whole frac units
				a, b = amt[1].split('/')
				value = float(amt[0]) + float(a) / float(b)
				unit = amt[2]
			else:
				raise Exception("Invalid amount %s"%amt)
				
			if unit not in self.all_units():
				raise Exception("Unknown units '%s'"%unit)
			
			self.amount = value
			self.unit = unit
		else:
			self.amount = float(amt)


	def amt(self, unit=None):
		""" Return the amount of this ingredient in units of \a unit.  
		The default unit is the internal unit used.
		"""
		if not unit or unit == self.unit:
			return self.amount
			
		if unit == 'g':
			if self.unit in Ingredient.VOLUME_UNITS:
				return self.amount * Ingredient.UNITS[self.unit] * self.food.unit_mass / self.food.unit_volume
			elif self.unit in Ingredient.MASS_UNITS:
				return self.amount * Ingredient.UNITS[self.unit]
			else:
				return self.amount * self.food.unit_mass
		else:
			grams = self.amt('g') # first convert to grams
			if unit in Ingredient.VOLUME_UNITS:
				return grams * self.food.unit_volume / self.food.unit_mass / Ingredient.UNITS[unit]
			elif unit in Ingredient.MASS_UNITS:
				return grams / Ingredient.UNITS[unit]
			elif unit == self.food.unit_label:
				return grams / self.food.unit_mass
			else:
				raise Exception("Unknown unit <%s>"%unit)

	def str_amt(self, unit=None):
		""" Convert the floating point amount 5.3333 to a nice 5 1/3
		"""
		if not unit:
			unit = self.unit
		amt = self.amt(unit)
		if unit in ['g', 'ml', 'oz']: # These should not be fractionalized
			return "%.1f %s"%(amt, unit)
		# Otherwise, turn amt into a fraction
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
		return "%s%s%s %s"%(whole, ' ' if whole and part else '', part, unit)
	
	def __str__(self):
		return self.food.name
		

class Food(YAMLSetter):
	""" A food can be an elementary food (oranges, papurika, water), or a composite recipie (spaghetti sauce, cocoa).
	The food should specify its unit_mass and unit_volume so that it can be converted to any unit.
	"""
	yaml_tag="!Food"
	yaml_props = {
		'name':'',  #A uniqe short name of the food.
		'unit_mass': 1.0, # amount of mass per 'unit_label'
		'unit_volume': 1.00000001, # Amount of volume per 'unit_label'
		'unit_label': '', # The units to count this food by (e.g.  'stick' of butter)
		'kcals': -1,  # kCalories per gram of this food (-1 means unknown)
		'protein': -1, # protein per gram of this food (-1 means unknown)
		'carbs': -1, # carbs per gram of this food (-1 means unknown)
		'tags': [], # A list of tags for categorizing this food
		'description': '', #A longer description of the food
		'ingredients': [], # A list of type <Ingredient>
		'instructions': [], #A simple list of strings describing how to combine the ingredients.
	}
	
	def __init__(self, **kwargs):
		YAMLSetter.__init__(self, kwargs)
	
	def __eq__(self, other):
		return self.name == str(other)
	
	def has_tag(self, tagname):
		""" tagname should be all caps"""
		return tagname in self.tags
		
	def add_ingredient(self, food, amt_str='0.0 g', prep=""):
		""" Add a new ingredient to this food """
		ig = Ingredient(food=food, prep=prep)
		ig.set(amt_str)
		self.ingredients.append(ig)
		self.add_tag('recipe')
	
	def clear_tags(self):
		""" Delete all the tags.  But retain the <RECIPE> tag if we are a recipe. """
		self.tags = ['RECIPE'] if len(self.ingredients) else []
	
	def add_tag(self, tagname):
		""" Add a new tag.  It is cleaned up and uppercased for you.  A duplicate tag will not be added."""
		if not tagname.strip():
			raise Exception("No Null tags")
		for i in Tag.OPS + ['(', ')']:
			if i in tagname:
				raise Exception("'%s' cannot be in a tagname"%i)
		tagname = tagname.upper()
		if tagname not in self.tags:
			self.tags.append(tagname)
	
	def scale(self, factor):
		""" Scale this recipe by the given factor """
		for i in self.ingredients:
			i *= factor
		return self
	
	def ingredients_str(self):
		if not self.ingredients:
			return ""
		max_name = max(map(lambda x: len(str(x)), self.ingredients))
		return '\n'.join(map(lambda s: '   %s%s | %s   %s'%(' '*(max_name-len(str(s))), s, s.str_amt(), s.prep), self.ingredients ))

	def verbose(self):
		title = "%s %s\n"%(self.name, ' : '+self.description if self.description else '')
		astr = '='*len(title) + '\n%s'%title + '-'*len(title)
		if self.tags:
			astr += '\n<' + '> <'.join(self.tags) + '>\n'
		if self.ingredients:
			astr += "\nIngredients:\n"
			astr += self.ingredients_str()
		if self.instructions:
			astr += '\n\n' + '\n'.join(map(lambda s: '  * '+s, self.instructions)) + '\n'
	
		return astr
		
	def __str__(self):
		return self.name
