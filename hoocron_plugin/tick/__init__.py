from hoocron_plugin import HoocronJobBase
import time

class TickJob(HoocronJobBase):
    
    def __init__(self):
        self.name = 'TICK'
        self._started = time.time()

    def run(self):
        print(f"Tick! (uptime: {int(time.time() - self._started)} seconds)")
        return "ticked"
    
    def activate(self):
        return {
            'cron_period': [[self.name, '10s']],
            'redis_job': [self.name]
        }

tick_job = TickJob()

jobs = [ tick_job ]
