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
		return obj
		
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
		with open(os.path.join(path, name), 'w', encoding='utf-8') as f:
			yaml.dump(obj, f, width=80, indent=4)
			f.flush()
			os.fsync(f.fileno())
		# Delete the 'saving' file
		os.remove(os.path.join(path, 'saving'))
		print("Save Successful")
		
		
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

