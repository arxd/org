"""
	Just some general discussion / brainstorming / motivations..
	===================================

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
	"""
	Repositories only have value relative to other repositories.  
	So you go to the market to get the value of a repo.
	One market holds the temporal trade values between two units
	  * USD vs. JPY
	  * Bus vs. USD
	The market values can come from the internet (currencies / stocks)
	or you can define your own values and load them from a file.
	
	If you define market values for future dates then you can speculate
	about the future.  Values are interperated linearly between dates.
	"""
	def __init__(self, unitA, unitB):
		self.unitA = unitA
		self.unitB = unitB
		self.points = [] # an array of tuples:  (time, amt_unitA, amt_unitB).  Sorted by time (earliest first).
		
	def load(self, url):
		""" 
		Load market data from filename  file://asdfasdfasdf
			or Load data from a url http:// basdfasdfa
			
			This method will be overridden in sub classes to implement different data locations
		"""
		pass

	def trade(self, value, unit, time=None):
		""" 
		Convert value \a from_units \a to_units at \a time.
		The default time is today
		"""
		# figure out which way we are trading
		if unit == self.unitA:
			ratio_exp = -1.0 # value_A *  (B/A)
		elif unit == self.unitB:
			ratio_exp = 1.0 # value_B * (A/B)
		else:
			raise Exception("This Market (%s, %s) can't trade %s"%(self.unitA, self.unitB, unit))
		
		# Search for the correct trade value
		return value * (self.get_ratio(time) ** ratio_exp)

	def get_ratio(self, time=None):
		"""
		Get a converstion ratio (unitA/unitB) at \a time.  The default time is today.
		"""
		if len(self.points) == 0:
			raise Exception("This market has no assesment data.")
		if not time:
			time = today()
		i = 0
		while i < len(self.points) and time > self.points[i][0]:
			i += 1
		if i == len(self.points): # Asking about the future.  Use the latest known value
			return self.points[-1][1] / self.points[-1][2]
		if i == 0: # Asking at a time before our first assessment
			raise Exception("This market has no defined value before %s"%(str(self.points[0][0])))
		# Linearly interpolate between the two points
		dA = self.points[i][1] - self.points[i-1][1]
		dB = self.points[i][2] - self.points[i-1][2]
		frac = (time - self.points[i-1][0]).days() / (self.points[i][0] - self.points[i-1][0]).days()
		return (self.points[i-1][1] + frac*dA) / (self.points[i-1][2] + frac*dB)
		
	def assess(self, amt_unitA, amt_unitB, time=None):
		""" 
		Assess \a amt_unitA as \a amt_unitB.  Time defaults to today.
		
		market = Market("PrevostBus", "USD")
		market.assess(1, 5000000) # 1 Bus == $50,000.00
		"""
		if not time:
			time = date.today()
		# insert in sorted order
		i = len(self.points)  # search backward to give O(n) for sorted data
		while i > 0 and time < self.points[i-1][0]:
			i -= 1
		if i and self.points[i-1][0] == time:
			raise Exception("Cannot have two different assessments on the same day")
		self.points.insert(i, (time, amt_unitA, amt_unitB))


class Repo(object):
	""" 
	A Repo (Repository) is a place where 'value' is kept.  It has an integer quantity of 'stuff'.  
	It is kept as an integer to avoid flotaing point imprecision and ensure exact math.
	If the quantity is 1 then that means this is indivisible (like a house, or a dog).
	Otherwise, parts of this repository can be transfered to another repository.
	
	A credit card account would be represented by a Repo that is not owned by you (someone elses money)
	A company (Walmart) would also be a Repo not owned by you.
	"""
	def __init__(self, name, frac_digits=2, units="USD", mine=False):
		self.name = name  # Bus, Scooter, Capital One Checking, Cash, etc.
		self.frac_digits = frac_digits # Since quantity is an integer, this tells us how many of those digits are fractional parts.  USD:2, JPY:0,  etc.
		self.quantity = 0 # This is an integer value of quantity, 1 bus, 200 cents,  3000000 cm^2 of land, etc.
		self.mine = mine # is this repository owned by me?
		self.units = units # what is quantity counting? (DeckerPrarieAcres, USD, Bitcoin, Bus, Scooter)
		
	def get_value(self, market=None, when=None):
		""" Get the value of this repo from the \a market.
		Since value changes with time you can specefy \a when.  It defaults to today.
		"""
		if not market:
			return self.quantity
		# use the market
		return market.trade(self.quantity, self.units, when)


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
