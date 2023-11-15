
from launch import Action, Launch


class Script:
	def __init__(self,parts=None):
		self._parts = parts if not parts is None else []
	def add(self,*r):
		''' Add another script object as a component to render. '''
		for a in r:
			self._parts.append(a)
		return self
	def render(self):
		return '#!/bin/bash\n' + \
			'{\n'+'\n'.join((a.render() for a in self._parts))+'\n} 2>&1 | tee /tmp/script.log'

class PackageScriptAPT(Script):
	def render(self):
		return '\n'.join([
			'apt update',
			'apt install -y %s' % (' '.join(self._parts)) ])

class GitScript(Script):
	def __init__(self,table=None,dest=None):
		self._dest  = dest or '/tmp'
		self._table = table if not table is None else {}
	def render(self):
		key = self._table['_key'] if '_key' in self._table else None
		sshcom = 'GIT_SSH_COMMAND="ssh %s %s" \\\n    ' % (
			('-i \'%s\'' % (key,)) if key else '',
			'-o StrictHostKeyChecking=no')
		return '\n'.join([
			'( cd "%s"' % (self._dest,),
			'%s' % '\n'.join([\
			('  %sgit clone "%s" "%s" && \\\n' +
			'      chown -R ubuntu:ubuntu "%s"') % (sshcom,v,k,k) \
					for k,v in self._table.items() if k[0] != '_']),
			')'
		])

class BashScript(Script):
	def __init__(self,text=None,header=None):
		header = header if not header is None else ''
		text = text if not text is None else ''
		if not type(text) is str:
			text = '\n'.join(text)
		self._text = text
		self._header = header
	def render(self):
		return (self._header+'\n' if self._header else '')+self._text

class CopyScript(Script):
	def __init__(self,ob):
		ob = list(ob.items()) if type(ob) is dict else ob
		self._obs = ob

class S3Script(CopyScript):
	def render(self):
		# TODO: Determine args for recursive get.
		ret = []
		for r in self._obs:
			dest,src = r[:2]
			mkdir = 'mkdir -p "%s" && ' % (dest,) if dest[-1] == '/' else ''
			s = '%saws s3 cp "s3://%s" "%s"' % (mkdir,src,dest)
			ret.append(s)
		return '\n'.join(ret)

# TODO: This neesd to be in a config file, I think.
schemas = {
	'ubuntu': {
		# TODO: Which means another meta class so this can be a string.
		'packages':PackageScriptAPT,
		'git':GitScript,
		'shell':BashScript,
		'pull':None,
		's3':S3Script
	}
}

class LaunchBase(Action):
	def __init__(self,conf,prof=None):
		self._conf = conf
		self._prof = prof
	
	def act(self,*r,**kw):
		raise Exception('act() abstract, unimplemented')
	
	def act_setup(self):
		conf = self._conf
		prof = self._prof
		name = 'test_launchbox'
		if not prof:
			lconf = {
				'iid':None,
				'typ':'t2.micro',
				'key':conf.key.default,
				'ami':conf.ami.default,
				'sub':conf.sub.default,
				'sec':conf.sec.default
			}
		else:
			lconf = {
				'iid':None,
				'typ':conf.typ[prof.typ],
				'key':conf.key[prof.key],
				'ami':conf.ami[prof.ami],
				'sub':conf.sub[prof.sub],
				'sec':conf.sec[prof.sec]
			}
			name = prof.name
		a = Launch(tags={
				'Name':name
			},**lconf)
		return (a,lconf)

class LaunchCreate(LaunchBase):
	def act(self,run=True):
		prof = self._prof
		us = schemas[prof.buildup.schema]
		userscript = Script()
		createkw = {}
		# TODO: Move this logic into its own func, so teardown can call it, too.
		if hasattr(prof,'buildup'):
			# Has buildup object, which speicifies a schema and things to run.
			for a in prof.buildup.run:
				for k,v in a.items():
					print('k,v',k,v)
					# TODO: Have a metaclass table keeping track of keywords to look for.
					if k == 'packages':
						userscript.add(us[k](v))
					elif k == 'git':
						userscript.add(us[k](v,dest='/opt'))
					elif k == 'shell':
						userscript.add(us[k](v))
					elif k == 's3':
						userscript.add(us[k](v))
		print('script:\n%s' % (userscript.render(),))
		#return None
		createkw['UserData'] = userscript.render()
		if hasattr(prof,'iam'):
			if 'arn:aws:iam' in prof.iam:
				createkw['IamInstanceProfile'] = {'Arn':prof.iam}
			else:
				createkw['IamInstanceProfile'] = {'Name':prof.iam}
		a,lconf = self.act_setup()
		if run:
			return a.create(**createkw)
		else:
			return None

class LaunchStart(LaunchBase):
	def act(self,*r):
		prof = self._prof
		a,lconf = self.act_setup()
		return a.start()

class LaunchStop(LaunchBase):
	def act(self,*r):
		prof = self._prof
		a,lconf = self.act_setup()
		return a.stop()

class LaunchTerminate(LaunchBase):
	def act(self,*r):
		prof = self._prof
		a,lconf = self.act_setup()
		return a.terminate(prof.name)
		

