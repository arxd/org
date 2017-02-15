"""
We want to store our objects in plain txt files.
JSON is the easiest to read plain-txt format, but it only stores numbers and strings.
So we have to treat some strings as special to save object references and dates.

Each object is stored as a directory on disk.  In the directory is a bunch of JSON files for the object named with a timestamp.
Whenever the object is saved -- obj.save() -- a new file is created and the object is written to the new file.  
This serves as an automatic backup system.
"""
import json
from datetime import datetime, date
import os.path
import os
import time

class SpecialJSON(json.JSONEncoder, json.JSONDecoder):
	def default(self, obj):
		if isinstance(obj, datetime) or isinstance(obj, date):
			return obj.strftime("|d|%Y-%m-%d %H:%M:%S")
		if isinstance(obj, DBObject):
			return '|o|%s|%s'%(obj.__class__.__name__, obj._db_path)
		return json.JSONEncoder.default(self, obj)

class DBObject(object):
	"""
	This object is stored on disk as a plain text JSON file.
	Each save of the object creates a new file in the object's directory.
	Old file contents are never overwritten.
	When the object is loaded, the newest version of the file is loaded.
	"""
	LOADED = {}
	REGISTERED = {}
	REGISTERED_INLINE = {}
	DB_FMT = "%Y-%m-%d__%H.%M.%S.json"
	
	@classmethod
	def register(self, *db_props):
		""" This is a decorator function to register the class name (for loading from JSON files), 
		and for listing the properties you want to save in the database.
		"""
		def do_kls(kls):
			self.REGISTERED[kls.__name__] = kls
			kls._db_props = set(db_props)
			return kls
		return do_kls

	@classmethod
	def register_inline(self, kls):
		""" 
		"""
		DBObject.REGISTERED_INLINE[kls.__name__] = kls
		return kls


	def __new__(cls, path, kls=None):
		if path in DBObject.LOADED:
			return DBObject.LOADED[path]
		if not kls:
			return object.__new__(cls)
		return object.__new__(DBObject.REGISTERED[kls])
		
	def __init__(self, path, kls=None):
		"""
		\a db_props is a list of properties of this object to save.
		\a path sould be a directory.  If the directory does not exist then it is created.
		The datafiles for this object are put in the directory.
		"""
		if not hasattr(self, "_db_path"):
			if not os.path.isdir(path):
				if os.path.exists(path):
					raise Exception("Datastore must point to a directory, not '%'"%path)
				os.makedirs(path)
			self._db_path = path
			DBObject.LOADED[self._db_path] = self
			
			self._db_props = set()
			
			cls = self.__class__
			while cls:
				if hasattr(cls, '_db_props'):
					self._db_props.update(cls._db_props)
				cls = cls.__bases__[0] if cls.__bases__ else None
			
	
	def load(self, when=None):
		"""
		Loads the local dict properties from disk.  It loads the most recent data <= time.  
		If time is None then the most recent data is loaded.
		This method can only be called once.
		"""
		# Only load the DB Once
		if hasattr(self, '_db_loaded'):
			return self
		self._db_loaded = True
		return self.reload(when)
	
	def reload(self, when=None):
		"""
		Loads the local dict properties from disk.  It loads the most recent data <= time.  
		If time is None then the most recent data is loaded.
		"""
		files = self.db_files()
		if not files:
			raise Exception("No database files at: %s"%self._db_path)
		i = 0
		while when and i < len(files) and when > files[i]:
			i+=1
		if i == len(files):
			raise Exception("No database files before %s"%when.isoformat())
		name = os.path.join(self._db_path, files[i].strftime(DBObject.DB_FMT))
		print("LOADING %s"%name)
		f = open(name, encoding="utf-8")
		
		def str_to_obj(s):
			if s.startswith('|o|'):
				kls, path = s[3:].split('|')
				return DBObject(path, kls=kls).load(when)
			elif s.startswith('|d|'):
				try:
					return datetime.strptime(s[3:], "%Y-%m-%d %H:%M:%S")
				except ValueError:
					return s
			else:
				return s

		def convert_dict(obj):
			for k,v in obj.items():
				if isinstance(v, dict):
					convert_dict(v)
				elif isinstance(v, list):
					convert_list(v)
				elif isinstance(v, str):
					obj[k] = str_to_obj(v)
						
		def convert_list(obj):
			for i in range(0, len(obj)):
				if isinstance(obj[i], dict):
					convert_dict(obj[i])
				elif isinstance(obj[i], list):
					convert_list(obj[i])
				elif isinstance(obj[i], str):
					obj[i] = str_to_obj(obj[i])
		
		dat = json.load(f)
		convert_dict(dat)
		for k,v in dat.items():
			setattr(self, k, v)
		
		f.close()
		return self
		
	def save(self):
		"""
		Saves all the properties of this object to disk.  Each property object should be JSON serializable.
		Properties you don't want saved to disk should be prefixed with at least one underscore _dontsave.
		This does not overwrite any other data files.
		"""
		print("SAVE %s: %s"%(self._db_path, str(self._db_props)))
		name = os.path.join(self._db_path, datetime.utcnow().strftime(DBObject.DB_FMT))
		if os.path.exists(name):
			print("%s exitsts! Sleeping..."%name)
			time.sleep(2)
			self.save()
			return
		f = open(name, "w", encoding="utf-8")
		json.dump({k:v for k,v in self.__dict__.items() if k in self._db_props}, f, indent=4, cls=SpecialJSON, sort_keys=True)
		f.close()
	
	def db_files(self):
		return sorted(map(lambda s: datetime.strptime(s, DBObject.DB_FMT), os.listdir(self._db_path)), reverse=True)
	
	def clean(self):
		"""
		Keep every file newer than 10 days old.
		Keep one file per day for 30 days.
		Keep one file per month for 12 months.
		Keep one file per year forever.
		"""
		pass
		
	def __str__(self):
		return self._db_path
	
	def __eq__(self, other):
		return self._db_path == str(other)

