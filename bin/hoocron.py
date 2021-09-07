#!/usr/bin/env python3

from queue import Empty, Queue
from threading import Thread, get_ident
import time
import os
import importlib
import pkgutil
import argparse
import shlex
import subprocess

args = None
hooks = list()

_stop = object()


class Job:
	def __init__(self, name, cmd):
		self.name = name
		self.cmd = cmd
		self.rc = None
		self._running = False
		self.policy = 'ignore' # ignore / asap
		self._asap = False

		# hook-specific data
		self.hook_name = None
		self.hook = None
		
	def running(self):
		return self._running

	def finished(self):
		return self.rc is not None

	def get_rc(self):
		return self.rc

	def cleanup(self):
		""" clean after execution """
		self.rc = None
		self._running = False
		if self._asap:
			self._asap = False
			print(f"run delayed task {self.name} asap")
			self.start()

	def _execution(self):
		if not self._running:
			# normal case
			self._running = True # race condition possible, use semaphore
			self.rc = subprocess.run(self.cmd)
		else:
			# duplicate run
			if self.policy == 'ignore':
				print(f"Job {self.name} already running, ignore request")
			elif self.policy == 'asap':
				print(f"Job {self.name} already running, schedule asap")
				self._asap = True
			else:
				print("Unknown policy", self.policy)
			

	def start(self):
		# rc = subprocess.run(self.cmd)
		self.exec_th = Thread(target=self._execution)
		# self.rc = None
		self.exec_th.start()

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
	if args.module is not None:
		for m in args.module:
			if not m.startswith('hoocron_plugin.'):
				mname = 'hoocron_plugin.' + m
			else:
				mname = m

			print("Loading", mname)
			m = importlib.import_module(mname)
			hooks.extend(m.hooks)

	# Load all plugins by name prefix
	hm = importlib.import_module('hoocron_plugin')

	for modinfo in pkgutil.iter_modules(hm.__path__):
		mname = 'hoocron_plugin.' + modinfo.name

		print("Loading", mname)
		m = importlib.import_module(mname)
		hooks.extend(m.hooks)

def get_args():

	parser = argparse.ArgumentParser(description='HooCron, Cron with Hooks')
	parser.add_argument('-j', '--job', nargs='+', action='append', help='-j ECHO /bin/echo "zzzz"')
	parser.add_argument('-s', '--sleep', type=float, default=1, help='Sleep period (for modules which polls)')
	parser.add_argument('--policy', nargs=2, metavar=('JOB','POLICY'), action='append', help='policy what to do when request comes when job is running. Either "ignore" or "asap"')

	for hook in hooks:
		hook.add_argument_group(parser)

	return parser.parse_args()


		
# A thread that consumes data
def master(execute_q):
	try:
		while True:

			worked = False

			# Get some data
			try:
				(j, source) = execute_q.get_nowait()

				if j is _stop:
					print("master thread stopped")
					return

				# Process the data
				print(f"run {j.name} from {source}")
				rc = j.start()
				# print(f"return code for {j.name} is {rc.returncode}")
				worked = True

			except Empty:
				pass

			
			# check jobs
			for j in jobs.values():
				if j.finished():
					print(f"Return code for {j.name}: {j.get_rc().returncode}")
					j.cleanup()


			if not worked:
				time.sleep(1)


	except KeyboardInterrupt:
		print("Master got Keboard Interrupt")

def main():	
	global args, jobs
	
	load_submodules()

	args = get_args()

	if not args.job:
		print("No jobs (-j) configured, exit.")
		return

	for j in args.job:
		job_name = j[0]
		job_command = j[1:]
		if len(job_command)==1:
			job_command = shlex.split(job_command[0])

		jobs[job_name] = Job(job_name, job_command)

	if args.policy:
		for name, policy in args.policy:
			job = jobs[name]
			if policy in ['asap', 'ignore']:
				job.policy = policy
			

	for hook in hooks:
		hook.configure(jobs, args)


	# Create the shared queue and launch both threads
	execute_q = Queue()

	master_th = Thread(target = master, args =(execute_q, ))
	#cron_th = Thread(target = ch.thread, args =(jobs, execute_q, ))
	master_th.start()
	#cron_th.start()

	started_hooks = 0
	for hook in hooks:
		if not hook.empty():
			# print("Start hook submodule", hook)
			hook.start(execute_q)
			started_hooks += 1
	
	if started_hooks:
		try:
			master_th.join()
		except KeyboardInterrupt as e:
			print("Got keybobard interrupt")
			for hook in hooks:
				if hook.running():
					hook.stop()

			execute_q.put((_stop, 'main'))
			master_th.join()
	else:
		print("Not started any hooks")
		execute_q.put((_stop, 'main'))


if __name__ == '__main__':
	main()
	