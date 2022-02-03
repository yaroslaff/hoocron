#!/usr/bin/env python3

from queue import Empty, Queue
from threading import Thread, get_ident
import time
import os
import sys
import importlib
import pkgutil
import argparse
import shlex
import subprocess
import pwd
import grp

from hoocron_plugin import HoocronHookBase, HoocronJobBase

args = None
hooks = list()

_stop = object()


class Job:
	def __init__(self, name, cmd):
		self.name = name
		self.cmd = cmd
		self._result = None
		self._running = False
		self.policy = 'ignore' # ignore / asap
		self._asap = False
		self.user = None
		self.group = None
		self.uid = None
		self.gid = None

		# hook-specific data
		self.hook_name = None
		self.hook = None
		
	def running(self):
		return self._running

	def result(self):
		return self._result 

	def finished(self) -> bool:
		""" return true if job is *just* finished and need cleanup """
		return self._running and self._result is not None

	def cleanup(self):
		""" clean after execution """
		self._result = None
		self._running = False
		if self._asap:
			self._asap = False
			print(f"run delayed task {self.name} asap")
			self.start()

	def _execution(self):

		def demote(user_uid, user_gid):
			def set_ids():
				os.setgid(user_gid)
				os.setuid(user_uid)

			return set_ids


		if not self._running:
			# normal case
			self._running = True # race condition possible, use semaphore
			if isinstance(self.cmd, HoocronJobBase):
				self._result = self.cmd.run()
			else:
				if self.user:
					preexec_fn = demote(self.uid, self.gid)
				else:
					preexec_fn = None

				self._result = subprocess.run(self.cmd, preexec_fn=preexec_fn).returncode

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

	def set_user_group(self, user, group):
		self.user = user
		self.group = group

		self.uid = pwd.getpwnam(self.user).pw_uid
		self.gid = grp.getgrnam(self.group).gr_gid

		print(f"Job {self} will run as {self.user}({self.uid}):{self.group}({self.gid})")

	def __repr__(self):
		return self.name


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
	loaded_hooks = list()
	loaded_jobs = list()

	for modinfo in pkgutil.iter_modules(hm.__path__):
		mname = 'hoocron_plugin.' + modinfo.name

		m = importlib.import_module(mname)

		if hasattr(m, 'hooks'): 
			for h in m.hooks:
				hooks.append(h)
				loaded_hooks.append(h.name)

		if hasattr(m, 'jobs'): 
			for j in m.jobs:
				jobs[j.name] = Job(j.name, j)
				loaded_jobs.append(j.name)
		
	print(f"Loaded Hooks: {', '.join(loaded_hooks)} Jobs: {', '.join(loaded_jobs)}")



def get_args():

	def_activate = os.getenv('ACTIVATE','').split(' ')

	parser = argparse.ArgumentParser(description='HooCron, Cron with Hooks')
	parser.add_argument('-j', '--job', nargs='+', action='append', help='-j ECHO /bin/echo "zzzz"')
	parser.add_argument('-s', '--sleep', type=float, default=1, help='Sleep period (for modules which polls)')
	parser.add_argument('--policy', nargs=2, metavar=('JOB','POLICY'), action='append', help='policy what to do when request comes when job is running. Either "ignore" or "asap"')
	parser.add_argument('-a','--activate', metavar='JOB', action='store', nargs='+', default=def_activate, help='activate these jobs with their default parameters')
	parser.add_argument('-u','--user', metavar=('JOB', 'USER', 'GROUP'), nargs=3, action='append', help='run this job as USER')

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
					print(f"Result({j.name}): {j.result()}\n")
					j.cleanup()


			if not worked:
				time.sleep(1)


	except KeyboardInterrupt:
		print("Master got Keboard Interrupt")

def main():	
	global args, jobs
	
	print(f"Starting hoocron pid: {os.getpid()}")

	load_submodules()

	args = get_args()

	if args.job:
		for j in args.job:
			job_name = j[0]
			job_command = j[1:]
			if len(job_command)==1:
				job_command = shlex.split(job_command[0])

			jobs[job_name] = Job(job_name, job_command)
			for uj in args.user:
				if uj[0]==job_name:
					jobs[job_name].set_user_group(uj[1], uj[2])

	if args.policy:
		for name, policy in args.policy:
			job = jobs[name]
			if policy in ['asap', 'ignore']:
				job.policy = policy

	for jobname in args.activate:
		if not jobname:
			# skip empty element ''
			continue
		try:
			job = jobs[jobname]
			activation = job.cmd.activate()
		except KeyError:
			print(f"No such job {jobname!r}" )
			sys.exit(1)
		except AttributeError:
			print(f"Cannot activate custom job {jobname!r}")
			sys.exit(1)
		for k, val in activation.items():
			try:
				getattr(args, k).extend(val)
			except AttributeError:
				setattr(args, k, val)

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
	