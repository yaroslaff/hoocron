import time
import os
from threading import Thread

class CronJob:
	"""
		CronJob is wrapper around Job, but not child class
	"""
	def __init__(self, job, period):
		self.job = job
		self.period = period
		self.last_executed = None
	
	def next(self):
		if self.last_executed:
			return self.last_executed + self.period
		else:
			return int(time.time())

	def executed(self):
		self.last_executed = int(time.time())

class CronHook:
	def __init__(self):
		self.jobs = list()
	
	def __repr__(self):
		return f'cron ({len(self.jobs)})'

	def add_argument_group(self, parser):
		g = parser.add_argument_group('Periodical hook (cron)')
		g.add_argument('-p', '--cron-period', nargs=2, metavar=('CODENAME', 'TIMESPEC'), action='append', help='-p ECHO 10s')
	
	def configure(self, jobs, args):
		
		for cp in args.cron_period:
			job_name = cp[0]
			hook_spec = cp[1]
			job = jobs[job_name]

			try:
				period = int(hook_spec)
			
			except ValueError:
				num = int(hook_spec[:-1])
				suffix = hook_spec[-1]
				mul = {
					's': 1,
					'm': 60,
					'h': 3600,
					'd': 86400
				}[suffix.lower()]
				period = num*mul

			j = CronJob(job, period)
			self.jobs.append(j)


	# A thread that produces data
	def thread(self, execute_q):

		print(f"<{os.getpid()}> started cron thread with {len(self.jobs)} jobs: {' '.join(list(j.job.name for j in self.jobs))}")

		while True:
			next = min(map(lambda j: j.next(), self.jobs))
			now = int(time.time())
			if next > time.time():
				time.sleep(next-now)
				# get new now
				now = int(time.time())
			
			for j in self.jobs:
				if j.next() <= int(time.time()):
					execute_q.put((j.job, 'cron'))
					j.executed()

	def start(self, execute_q):
		cron_th = Thread(target = self.thread, args =(execute_q, ))
		cron_th.start()


hooks = [ CronHook() ]
