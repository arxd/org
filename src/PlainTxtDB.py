"""
We want to store our objects in plain txt files.
YAML Is great.

Each object is stored as a directory on disk.  In the directory is a bunch of YAML
files for the object named with a timestamp.
Whenever the object is saved -- DB.save() -- a new file is created and the object is written to the new file.  
This serves as an automatic backup system.
"""
import yaml
from datetime import datetime
import os.path
import os


class Tag(object):
	AND = '&'
	OR = ','
	NOT = '-'
	OPS = [ AND, OR, NOT]

	@staticmethod
	def parse(tagstr):
		""" Turn a sloppy infix string  '(my car, your car, -(bob , cob)) & expensive'
		into a nice valid tagexpr ['&', ',', 'MY CAR', ',', 'YOUR CAR', '-', ',', 'BOB', 'COB', 'EXPENSIVE']
		"""
		if not tagstr.strip():
			return []
		tagstr += '(' # add a ( to remove specail cases at the end of the string
		expr = []
		stack = []
		i = 0
		
		while i < len(tagstr):
			if len(expr) > 1 and expr[-1] not in Tag.OPS and expr[-2] == Tag.NOT:
				expr[-1] = [Tag.NOT, expr.pop()]
				i -= 1
			elif len(expr)>1 and expr[-1] not in Tag.OPS and expr[-2] == Tag.AND:
				a,b,c = (expr.pop(), expr.pop(), expr.pop())
				expr.append([b,c,a])
				i -= 1
			elif tagstr[i] == '(':
				stack.append(expr)
				expr = []
			elif tagstr[i] == ')':
				stack[-1].append(expr[0] if len(expr) == 1 else expr)
				expr = stack.pop()
			elif tagstr[i] in Tag.OPS:
				expr.append(tagstr[i])
			elif tagstr[i] != ' ':
				expr.append(tagstr[i])
				while tagstr[i+1] not in ['(', ')']+Tag.OPS :
					expr[-1] += tagstr[i+1]
					i += 1
				expr[-1] = expr[-1].strip().upper()
			i += 1
			
		def flatten(lst):
			out = [Tag.OR] * (0 if lst[0] in Tag.OPS else len(lst)//2)
			for i in range(0, len(lst), 2 if lst[0] not in Tag.OPS else 1):
				out += [lst[i]] if type(lst[i]) == str else flatten(lst[i])
			return out
		
		return flatten(stack[0])


	@staticmethod
	def match(obj, tagexpr):
		""" tag expr has a special prefix form.  And the tag names must be all caps.
		If tagexpr is a string then it passes the string through parse for you.
		obj must have the has_tag() method.
		 
		['BOB']
		['-', 'BOB']
		['&', 'BOB', ',', '-', 'MY HOUSE', 'MY CAR']
		"""
		if isinstance(tagexpr, str):
			tagexpr = Tag.parse(tagexpr)
		
		if not tagexpr:
			return True
		
		def match_r(i):
			if tagexpr[i] == Tag.AND or tagexpr[i] == Tag.OR:
				bool1, end1 = match_r(i+1)
				bool2, end2 = match_r(end1)
				return ( (bool1 and bool2) if tagexpr[i] == Tag.AND else (bool1 or bool2), end2)
			elif tagexpr[i] == Tag.NOT:
				bool, end = match_r(i+1)
				return (not bool, end)
			else:
				if obj.has_tag(tagexpr[i]):
					return (True, i+1)
				return (False, i+1)

		return match_r(0)[0]

	@staticmethod
	def filter(iterable, tagstr):
		""" Return a filtered list of foods based on the tagstr.
		This is prefered because it only parses the tagstr once.
		"""
		try:
			tagexpr = Tag.parse(tagstr)
		except Exception as e:
			print("Syntax Error in tag expression")
			return []
		return [f for f in iterable if Tag.match(f, tagexpr)]


class YAMLSetter(yaml.YAMLObject):
	def __init__(self, kwargs):
		for k,v in self.__class__.yaml_props.items():
			self.__dict__[k] = kwargs[k] if k in kwargs else v
				
	def __repr__(self):
		return "%s(%s)"%(self.__class__.__name__, ', '.join(['%s=%r'%(k,getattr(self,k)) for k,v in self.__class__.yaml_props.items() if v != getattr(self,k)]))


class DB(object):
	FILENAME_FMT = "%Y-%m-%d__%H.%M.%S.yaml"
	
	@classmethod
	def load(self, path, when=None):
		files = sorted(map(lambda s: datetime.strptime(s, DB.FILENAME_FMT), os.listdir(path)), reverse=True)
		if not files:
			raise Exception("No database files at: %s"%path)
		i = 0
		while when and i < len(files) and when > files[i]:
			i+=1
		if i == len(files):
			raise Exception("No database files before %s"%when.isoformat())
		name = os.path.join(path, files[i].strftime(DB.FILENAME_FMT))
		print("Loading %s"%name)
		with open(name, encoding="utf-8") as f:
			obj = yaml.load(f)
		return (obj, name)
		
	@classmethod
	def save(self, obj,  path):
		self.check(path) # first make sure the DB is in a consistant state
		name = datetime.utcnow().strftime(DB.FILENAME_FMT) # get Timestamp 
		if os.path.exists(os.path.join(path, name)): # Not sure why this might happen
			raise Exception("This file already exists!  Try again later.")
		print("Saving DB %s in %s"%(path, name))
		# Write a 'saving' file while we write the real data.   Delete it when the write is successful
		with open(os.path.join(path, 'saving'), 'w', encoding='utf-8') as f:
			f.write(name)
			f.flush()
			os.fsync(f.fileno())
		# Write the real data
		filename = os.path.join(path, name)
		with open(filename, 'w', encoding='utf-8') as f:
			yaml.dump(obj, f, width=80, indent=4)
			f.flush()
			os.fsync(f.fileno())
		# Delete the 'saving' file
		os.remove(os.path.join(path, 'saving'))
		print("Save Successful")
		return filename
		
		
	@classmethod
	def check(self, path):
		if not os.path.exists(path):
			print("Creating DB Directory (%s)"%path)
			os.makedirs(path)
		if not os.path.isdir(path):
			raise Exception("DB path is not a directory (%s)"%path)
		saving = os.path.join(path, 'saving')
		if os.path.exists(saving):
			with open(saving, encoding="utf-8") as f:
				corrupt = f.read().strip()
			print("%s file is corrupt... deleting it...")
			os.remove(os.path.join(path,corrupt))
			os.remove(saving)
		print("DB OK.")

