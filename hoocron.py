#!/usr/bin/env python3

from queue import Queue
from threading import Thread
import time
import os
import importlib
import pkgutil
import argparse
import subprocess

args = None
hooks = list()


class Job:
	def __init__(self, name, cmd):
		self.name = name
		self.cmd = cmd

		# hook-specific data
		self.hook_name = None
		self.hook = None

	def execute(self):
		rc = subprocess.run(self.cmd)
		return rc

	@staticmethod
	def filter(jobs, hook_name):
		return list(filter(lambda j: j.hook_name == hook_name, jobs.values()))

	def __repr__(self):
		return f'{self.name}: {self.cmd}'


jobs = dict()


def load_submodules():
	global hooks
	sub_parser = argparse.ArgumentParser(add_help=False)
	sub_parser.add_argument('-m', '--module', metavar='MODULE', nargs='+', help='load hoocron_MODULE extension module')

	args, extras = sub_parser.parse_known_args()
	#print("LOAD SUBMODULES:", args)
	#print(args.module)

	for modinfo in pkgutil.iter_modules():
		if modinfo.name.startswith('hoocron_'):
			print("Loading module", modinfo.name)
			m = importlib.import_module(modinfo.name)
			hooks.extend(m.hooks)

def get_args():

	parser = argparse.ArgumentParser(description='HooCron, Cron with Hooks')
	parser.add_argument('-j', '--job', nargs='+', action='append', help='-j ECHO /bin/echo "zzzz"')
	parser.add_argument('-m', '--module', metavar='MODULE', nargs='+', help='load hoocron_MODULE extension module')

	for hook in hooks:
		hook.add_argument_group(parser)



	return parser.parse_args()


		
# A thread that consumes data
def master(execute_q):
	try:
		while True:
			# Get some data
			(j, source) = execute_q.get()
			# Process the data
			print(f"run {j.name	} from {source}")
			rc = j.execute()
			print(f"return code for {j.name} is {rc.returncode}")

	except KeyboardInterrupt:
		print("Master got Keboard Interrupt")

def main():	
	global args, jobs
	
	load_submodules()

	args = get_args()

	for j in args.job:
		job_name = j[0]
		job_command = j[1:]
		jobs[job_name] = Job(job_name, job_command)

	for hook in hooks:
		hook.configure(jobs, args)


	# Create the shared queue and launch both threads
	execute_q = Queue()

	master_th = Thread(target = master, args =(execute_q, ))
	#cron_th = Thread(target = ch.thread, args =(jobs, execute_q, ))
	master_th.start()
	#cron_th.start()

	for hook in hooks:
		print("Start hook submodule", hook)
		hook.start(execute_q)


main()