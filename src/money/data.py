"""
	Just some general discussion / brainstorming...
	----------------

        We are interested in how our value is moving around, going up, going
        down. But, we can only track what quantities we have.

        I have a house.
        I have $3000 in the bank.
        I have 4 shares of Apple Stock
        I have 2.1 bitcoin
        I have 1 acre of land
        I have 12 eggs

        
        The _value_ of the things that you have is variable.
        If you are stranded in the middle of a desert only one of those things
        has any value.

        Inflation means your $3000 is becoming less valuable over time, but
        your Apple Stock might become more valuable over time.  The eggs have
        a pretty constant value (for a short period of time).

        The problem with value is that it does not obey conservation laws.  For
        example, gravity obeys conservation laws.  If you go for bike ride you
        might ride up hill or downhill, but when you return home you are
        guaranteed that you rode uphill exactly as much as you got to go
        downhill.

        Value doesn't obey that law (it should), this is one of the reasons I
        dont like economics.  You can trade things around in a circle and you
        will usually come out with less value than when you started.  If you
        are very clever you might get back _more_ value than when you started.
        That is very irritating.


        Value is created:
            * Working at a job
            * Building a table

        Value is destroyed:
            * Blowing up your car
            * Eating food

        Value takes on many forms:
            * Gold
            * Real Estate
            * Yen
            * Stock
            * Etc.

        So we have to keep track of the things we have, and then work out how
        much value that is.  How much value is it? 
        Value can only be measured by trade.  You have to compare what you have with something
        else to assess its value.  Some demands are fairly constant (hunger) so
        you can use those as stable reference points to calculate the values of
        other commodities.  So how much bread can you get for your car?  That
        is how valuable your car is.  Is there a more constant reference than
        our appitite to measure value against?

        Our Possesions may have value but there may be barriers to trade.  It
        is easy to trade money in the bank to cash in your hand.  It is hard to
        trade your house into cash in your hand.  This barrier is dependant
        on the two tradeables.
"""

from datetime import date


class Market(object):
	""" Repositories only have value relative to other repositories.  
	So you go to the market to get the value of a repo.
	One market holds the temporal trade values between two units
	  * USD vs. JPY
	  * Bus vs. USD
	The market values can come from the internet (currencies / stocks)
	or you can define your own values and load them from a file.
	
	If you define market values for future dates then you can speculate
	about the future.  Values are interperated linearly between dates.
	"""
	def __init__(self):
		self.unitA = unitA
		self.unitB = unitB
		self.points = [] # an array of (time, ratio[unitA/unitB] ) tuples
		
	def load(self, url):
		""" Load market data from filename  file://asdfasdfasdf
			or Load data from a url http:// basdfasdfa
			
			This method will be overridden in sub classes to implement different data locations
		"""
		pass

	def trade(self, value, from_unit, to_unit, time=None):
		""" Convert value \a from_units \a to_units at \a time.
		The default time is today
		"""
		if not time:
			time = date.today()
			
		# figure out which way we are trading
		if from_unit == self.unitA and to_unit == self.unitB:
			ratio_exp = -1.0 # value_A *  (B/A)
		elif from_unit == self.unitB and to_unit == self.unitA:
			ratio_exp = 1.0 # value_B * (A/B)
		else:
			raise Exception("This Market (%s, %s) cant trade (%s, %s)"%(self.unitA, self.unitB, from_unit, to_unit))
		
		# Search for the correct trade value
		return value * (self.get_ratio(time, 0, len(self.points)) ** ration_exp)

	def find_ratio(self, t, idx_from, idx_to):
		""" A binary search for \a t """
		#~ if idx_from >= idx_to:
			#~ if idx_from >= len(self.points):
				#~ return self.points[-1][1]
		#~ idx_mid = (idx_to - idx_from)//2 + idx_from
		#~ if self.points[idx_mid][0]

class Repo(object):
	""" A Repo (Repository) is a place where 'value' is kept.  It has an integer quantity of 'stuff'.  
	It is kept as an integer to avoid flotaing point imprecision and ensure exact math.
	If the quantity is 1 then that means this is indivisible (like a house, or a dog).
	Otherwise, parts of this repository can be transfered to another repository.
	
	An credit card account would be represented by a Repo that is not owned by you (someone elses money)
	A company (Walmart) would also be a Repo not owned by you.
	"""
	def __init__(self, name, frac_digits=2, units="USD", mine=False):
		self.name = name  # Bus, Scooter, Capital One Checking, Cash, etc.
		self.frac_digits = frac_digits # Since quantity is an integer only this tells us how many of those digits are fractional parts.  USD:2, JPY:0,  etc.
		self.quantity = 0 # This is an integer value of quantity, 1 bus, 200 cents,  3 acre of land, etc.
		self.mine = mine # is this repository owned by me?
		self.units = units # what is quantity counting?
		
	def get_value(self, other_units=None, when=None):
		""" Get the value of this repo in terms of some other units or self.units (default).
		Since value changes with time you can specefy \a when.  It defaults to today.
		"""
		if not when:
			when = date.today()
		if not other_units:
			other_units = self.units
		
		# Check our assessments 
		
		
		
	def assess_value(self, value_ratio, other_units="USD", when=None):
		""" Asses the value of this repository in terms of other_units as a ratio other_unit / this_unit
		"""
		if not when:
			when = date.today()
		self.assessments.append( (when, other_units, value_ratio) )
		

class Transfer(object):
	""" We keep track of value moving between Repositories.
	
	A purchase at a store would be multiple transfers.  
	
	You buy a Scooter and a coke at walmart.
		Transfer("Cash", "Walmart", )
		Transfer("Walmart", "Scooter", )
		Transfer("Walmart", "Food", )
		
	You withdraw money from your bank account:
		Transfer("Capital One Checking", "Cash")
		
	You buy bitcoin
		Transfer("Capital One Checking", "Coinbase")
		Transfer("Coinbase", "Bitcoin wallet")
	"""
	def __init__(self, from_repo, to_repo, memo="", tags={}):
		self.from_repo = from_repo
		self.to_repo = to_repo
		self.memo = memo
		self.tags = tags
		self.when = None
