import time
import os
import sys
from threading import Thread
from queue import Queue, Empty

from hoocron_plugin import HoocronHookBase

class StopException(Exception):
    pass

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

class CronHook(HoocronHookBase):
    def __init__(self):
        self.jobs = list()
        self.th = None
        self.q = None
	
    def __repr__(self):
        return f'cron ({len(self.jobs)})'

    def add_argument_group(self, parser):
        g = parser.add_argument_group('Periodical hook (cron)')
        g.add_argument('-p', '--cron-period', nargs=2, metavar=('JOB', 'TIMESPEC'), action='append', help='-p ECHO 10s')
	
    def configure(self, jobs, args):
        if not args.cron_period:
            return

        for cp in args.cron_period:
            job_name = cp[0]
            hook_spec = cp[1]
            try:
                job = jobs[job_name]
            except KeyError:
                print("ERROR: Not found job", job_name)
                sys.exit(1)

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


    def sleepstop(self, until):
        while time.time() <= until:
            try:
                cmd = self.q.get_nowait()
                if cmd == 'stop':
                    raise StopException
            except Empty:
                time.sleep(1)
                pass


	# A thread that produces data
    def thread(self, execute_q):

        print(f"started cron thread with {len(self.jobs)} jobs: {' '.join(list(j.job.name for j in self.jobs))}")

        while True:
            try:
                next = min(map(lambda j: j.next(), self.jobs))
                if next > time.time():
                    try:
                        self.sleepstop(next)
                    except StopException:
                        print("cron thread stopped")
                        return
                
                for j in self.jobs:
                    if j.next() <= int(time.time()):
                        execute_q.put((j.job, 'cron'))
                        j.executed()
            except KeyboardInterrupt as e:
                print("CRON thread got KI")

    def empty(self):
        return not bool(self.jobs)

    def stop(self):
        print("stopping cron")
        self.q.put('stop')

    def running(self):
        return bool(self.th)

    def start(self, execute_q):
        if self.jobs:
            self.q = Queue()
            self.th = Thread(target = self.thread, args =(execute_q, ))
            self.th.start()
            
        else:
            print("Warning: do not start cron because no jobs assigned")


hooks = [ CronHook() ]
