
from launch import Action, Launch


scripts = {
	'ubuntu':'''#!/bin/bash
echo "Who be ye?"
echo I LIVE | tee /tmp/hello
echo "I am `whoami`"
'''
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
		userscript = scripts[prof.buildup.script]
		a,lconf = self.act_setup()
		if run:
			return a.create(
				UserData=userscript)
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
		

