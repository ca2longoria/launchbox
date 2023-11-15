#!/bin/env python3

import re
import os
import sys
import json
import boto3

import launch
from launch import *


if True and __name__ == '__main__':
	import argparse

	p = argparse.ArgumentParser(description='launchbox, launch ec2 instances')
	p.add_argument('action',help='Action class to initialize')
	p.add_argument('configs',nargs='*',help='config files to pass to Action')
	p.add_argument('-d','--dryrun',action='store_true',help='pass run=False int act()')
	ar = p.parse_args()
	
	debug = False
	if debug:
		print(ar)
	
	Action.gather('actions')
	conft = Config.find(maxdepth=1)
	confd = Config.find('conf.d')
	
	if debug:
		print(Action.table)
		print(conft)
		print(Config.determine(conft['conf']))
		print(Config.render(conft['conf']))
	
	confs = [ConfigAlias(conft['conf'])] + \
		[a for p,a in Config.render_n(*[confd[s] for s in ar.configs])]
	act = Action.table[ar.action](*confs)
	#res = act.act(False)
	#res = act.act(True)
	res = act.act(not ar.dryrun)
	print('res',res)


