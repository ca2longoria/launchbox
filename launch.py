#!/bin/env python3

import re
import os
import sys
import json
import boto3

import os.path


if 'Helper funcs':
	def _defget(k,*r,default=None):
		for a in r:
			if k in a:
				return a[k]
		if isinstance(default,Exception):
			raise default('key (%s) not found in provided objects')
		return default

	def _endict(*r):
		d = {}
		def chain(r):
			for a in r:
				it = a.items() if hasattr(a,'items') else iter(a)
				for k,v in it:
					yield k,v
		for k,v in chain(r):
			d[k] = v
		return d

	def _getob(a,keys,prefix=None):
		for k in keys:
			a = a[k]
		return a

if 'Helper classes':
	class _rodict(dict):
		_locked = False
		_relock = False
		def __init__(self,*r,**kw):
			super().__init__(*r,**kw)
		def lock(self):
			self._locked = True
			return self
		def unlock(self,relock=False):
			self._locked = False
			self._relock = relock
			return self
		def __setitem__(self,k,v):
			if self._locked:
				raise Exception('rodict is locked, cannot set item')
			if self._relock:
				self.lock()
				self._relock = False
			return dict.__setitem__(self,k,v)
		def __delitem__(self,k):
			if self._locked:
				raise Exception('rodict is locked, cannot del item')
			if self._relock:
				self.lock()
				self._relock = False
			return dict.__delitem__(self,k)

if 'Config matters':
	def _confstep(a,k):
		k1 = k
		v = a[k]
		if k[0] == '@':
			k1 = k[1:]
			v = a[v]
		if k[0] == '=':
			k1 = k[1:] # literal assignment, skip list conversion
			v = a[v]
		elif type(v) is list:
			v = _getob(a,v)
		return (k1,v)

	def _confrec(a):
		t = {}
		for key in a.keys():
			k,v = _confstep(a,key)
			if isinstance(v,dict):
				v = _confrec(v)
			t[k] = v
		return t
	
	_config_class_table = _rodict().lock()
	class _MetaA(type):
		def __init__(c,name,bases,ns):
			#print('MetaA',c,name,bases)
			if hasattr(c,'_root'):
				rt = c._root()
				b = c
				x = 0
				while not b is object:
					br = [a for a in b.__bases__ if issubclass(b,rt)]
					#print('br',br)
					if len(br):
						b = br[0]
						x += 1
					else:
						break
				setattr(c,'_depth',x)
				_config_class_table.unlock(True)[name] = c
	
	class _AA: pass
	class _A(_AA,metaclass=_MetaA):
		def __getitem__(self,k):
			return getattr(self,k)
		@staticmethod
		def _root():
			return _AA
		@property
		def dict(self):
			a = dict(self.__dict__)
			for k in a.keys():
				b = getattr(self,k)
				if isinstance(b,_A):
					b = b.dict
				a[k] = b
			return a
	
	def _attrapply(a,d):
		ret = a if not a is None else _A()
		for k in d.keys():
			b = d[k]
			if len(k) and k[0] == '=':
				k = k[1:]
				# no change to b, assign as literal
			elif isinstance(b,dict):
				b = _attrapply(None,b)
			setattr(ret,k,b)
		return ret
	
	#_config_table = _rodict().lock()
	class Config(_A):
		def __init__(self,ob,assumejson=True):
			if type(ob) is str and assumejson:
				with open(ob,'r') as f:
					try:
						ob = json.loads(f.read())
					except json.decoder.JSONDecodeError as e:
						pass # ob stays a path for _mod to handle
			_attrapply(self,self._mod(ob))
		
		def _mod(self,ob):
			return ob
		
		@staticmethod
		def match(path):
			return not not re.search(r'\.json$',path)

		@staticmethod
		def determine(path,table=None):
			''' Sort table's classes by depth of inheritance, so the deepest inherited
			    classes will be checked against the path first, and return the first
					match. '''
			t = table or _config_class_table
			r = sorted(t.values(),key=lambda a:a._depth,reverse=True)
			r = [c for c in r if hasattr(c,'match')]
			for c in r:
				if c.match(path):
					return c

		@staticmethod
		def determine_n(*pr,table=None):
			''' Like determine(), but checks a number of paths, rather than one. '''
			t = table or _config_class_table
			r = sorted(t.values(),key=lambda a:a._depth,reverse=True)
			r = [c for c in r if hasattr(c,'match')]
			ret = []
			for p in pr:
				for c in r:
					if c.match(p):
						ret.append(c)
						break
			return ret

		@classmethod
		def render(cls,path,table=None):
			''' initialize a Config object based off determine()'s result. '''
			c = cls.determine(path,table=table)
			return c(path)
		
		@classmethod
		def render_n(cls,*pr,table=None):
			r = cls.determine_n(*pr,table=table)
			return [(p,c(p) if c else None) for p,c in zip(pr,r)]
		
		@classmethod
		def find(cls,target='.',check=None,table=None,maxdepth=-1):
			table = table if not table is None else {}
			#check = check or (lambda p:re.search(r'\.json$',p))
			#check = check or (lambda p:cls.match(p))
			check = check or (lambda p:cls.determine(p))
			depth0 = len(target.split(os.sep))
			for d,dirs,files in os.walk(target):
				depth1 = len(d.split(os.sep))
				if maxdepth >= 0 and depth1-depth0 >= maxdepth:
					continue
				for p in filter(check,(os.path.join(d,f) for f in files)):
					name = re.sub(r'^(.*'+os.sep+r')?([^.]+)(\..*)?$',r'\2',p)
					#_config_table.unlock(True)[name] = p
					table[name] = p
			return table
	
	class ConfigAlias(Config):
		def _mod(self,ob):
			return _confrec(ob)
		@staticmethod
		def match(path):
			return not not re.search(r'\.a\.json$',path)
	
	class ConfigList(Config):
		def __init__(self,*r,**kw):
			super().__init__(*r,assumejson=False,**kw)
		def _mod(self,ob_path):
			with open(ob_path,'r') as f:
				r = [json.loads(re.sub(r'\r?\n$','',s)) for s in f.readlines()]
			return {'=rows':r}
		@staticmethod
		def match(path):
			return not not re.search(r'\.jsonl$',path)
	
if 'Launch matters':
	class Launch:
		def __init__(self,
				iid=None,typ=None,ami=None,key=None,
				sub=None,sec=None,tags=None):
			self._iid  = iid
			self._typ  = typ
			self._ami  = ami
			self._key  = key
			self._sub  = sub
			self._sec  = sec
			self._tags = tags
			self._ins = None # instance object
		
		@property
		def instance(self):
			if self._ins:
				n = self._ins
			elif self._iid:
				e = boto3.resource('ec2')
				n = e.Instance(self._iid)
			else:
				raise Exception('PERISH')
			return n
		
		def create(self,**kw):
			kw2 = {
				'ImageId':self._ami,
				'InstanceType':self._typ,
				'SubnetId':self._sub,
				'KeyName':self._key,
				'MinCount':1,
				'MaxCount':1
			}
			for k,v in kw.items():
				kw2[k] = v
			if self._tags:
				kw2['TagSpecifications'] = [{
					'ResourceType':'instance',
					'Tags':[{'Key':a,'Value':b} for a,b in self._tags.items()]
				}]
			for k in 'ImageId,InstanceType,SubnetId,KeyName'.split(','):
				assert k in kw2 and kw2[k], 'key (%s) not found in Launch args' % (k,)
			try:
				e = boto3.resource('ec2')
				n = e.create_instances(**kw2)[0]
				self._ins = n
				self._iid = n.id
			except Exception as e:
				raise e
				return None
			return n
		
		def stop(self):
			return self.instance.stop()
		
		def terminate(self):
			pass

if 'Action nonsense':
	_action_table = _rodict().lock()
	class _ActionMeta(type):
		def __init__(c,name,bases,dct):
			_action_table.unlock(True)[name] = c
		@property
		def table(c):
			return _action_table
	
	class Action(metaclass=_ActionMeta):
		def __init__(self,*r):
			self._args = list(r)
		def act(self,*r,**kw):
			#print('act',self._args)
			#print('act',[a.__dict__ for a in self._args])
			return 'act(*(%s),**(%s))' % (str(r),str(kw))
	
	def _import_actions(target):
		import importlib
		# Iterate through imported modules within target directory.
		def mods(target):
			for d,dnames,files in os.walk(target):
				fr = [os.path.join(d,f) for f in files if re.search(r'\.py$',f)]
				for py in fr:
					name = re.sub(r'.*'+os.sep+r'(\w+)\.py$',r'\1',py)
					name = re.sub(os.sep,'.',py)[:-3]
					m = importlib.import_module(name,package=py)
					yield (m,name,py)
		# Now go through modules to grab Action classes.
		list(mods(target))
		# ^ Wait this is done with the meta class... do nothing!
			
	Action.gather = _import_actions

