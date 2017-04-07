"""
There are two classes:  Food and Ingredient.
A Food can be a recipe (Cookies) or a basic food (Apple, Cinnamon).
An Ingedient is an amount of food (in grams).
"""

from PlainTxtDB import YAMLSetter, Tag

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
		If you leave unit=None then it just returns the value in the current units.
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
		'unit_mass': 1.0,
		'unit_volume': 1.00000001,
		'unit_label': '',
		'kcals': -1,
		'protein': -1,
		'carbs': -1,
		'tags': [],
		'description': '',
		'ingredients': [],
		'instructions': [],
	}
	
	def __init__(self, **kwargs):
		YAMLSetter.__init__(self, kwargs)
	
	def __eq__(self, other):
		return self.name == str(other)
	
	def has_tag(self, tagname):
		return tagname in self.tags
		
	def add_ingredient(self, food, amt_str='0.0 g', prep=""):
		ig = Ingredient(food=food, prep=prep)
		ig.set(amt_str)
		self.ingredients.append(ig)
		self.add_tag('recipe')
	
	def add_tag(self, tagname):
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
	
	def verbose(self):
		title = "%s %s\n"%(self.name, ' : '+self.description if self.description else '')
		astr = '='*len(title) + '\n%s'%title + '-'*len(title)
		if self.tags:
			astr += '\n<' + '> <'.join(self.tags) + '>\n'
		if self.ingredients:
			astr += "\nIngredients:\n"
			max_name = max(map(lambda x: len(str(x)), self.ingredients))
			astr += '\n'.join(map(lambda s: '   %s%s | %s   %s'%(' '*(max_name-len(str(s))), s, s.str_amt(), s.prep), self.ingredients ))
		if self.instructions:
			astr += '\n\n' + '\n'.join(map(lambda s: '  * '+s, self.instructions)) + '\n'
	
		return astr
		
	def __str__(self):
		return self.name
