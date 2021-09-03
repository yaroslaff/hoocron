from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import os
# from types import MethodDescriptorType
from queue import Queue, Empty


class StopException(Exception):
    pass

class RequestHandler(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def my_handler(self):
        # Find proper handler
        try:
            j = http_hook.get_job(self.method, self.path)
            http_hook.kick_job(j, f'<{os.getpid()}> HTTP {self.method} request from {self.client_address[0]}')

            self._set_response()
            self.wfile.write('OK\n'.encode('utf8'))
        except KeyError:
            self.send_error(404, "No such job hook configured")

    def do_GET(self):
        self.method = 'GET'
        self.my_handler()

    def do_POST(self):
        self.method = 'POST'
        self.my_handler()

    def log_message(self, format, *args):
        pass

class HTTPJob:
    """
		HTTPJob is wrapper around Job, but not child class
	"""
    def __init__(self, job, method):
        self.job = job
        self.method = method


class HTTPHook:
    def __init__(self):
        self.jobs = list()
        self.port = 5152
        self.address = ''
        self.th = None
        self.q = None
	
    def __repr__(self):
        return f'http ({len(self.jobs)})'
    
    def add_argument_group(self, parser):
        g = parser.add_argument_group('HTTP web hook')
        g.add_argument('--get', '--http-get', metavar='CODENAME', default=list(), action='append')
        g.add_argument('--post', '--http-post', metavar='CODENAME', default=list(), action='append')
        g.add_argument('--http-address', metavar='ADDRESS', default='')
        g.add_argument('--http-port', type=int, metavar='PORT', default=5152)

    def configure(self, jobs, args):
        self.address = args.http_address
        self.port = args.http_port

        for name in args.get:
            self.jobs.append(HTTPJob(jobs[name], 'GET'))

        for name in args.post:
            self.jobs.append(HTTPJob(jobs[name], 'POST'))

    def get_job(self, method, path):
        for hj in self.jobs:
            if hj.method == method and path == '/'+hj.job.name:
                return hj.job
        raise KeyError

    def kick_job(self, j, desc):
        self.execute_q.put((j, desc))

	# A thread that produces data
    def thread(self):
        print(f"<{os.getpid()}> started http thread on {self.address}:{self.port} with {len(self.jobs)} jobs: {' '.join(list(j.job.name for j in self.jobs))}")
        httpd = HTTPServer((self.address, self.port), RequestHandler)
        httpd.timeout = 1
        
        while True:
            httpd.handle_request()
            try:
                self.checkstop()
            except StopException:
                httpd.server_close()
                print('http thread stopped...\n')
                return

    def empty(self):
        return not bool(self.jobs)

    def stop(self):
        self.q.put('stop')

    def checkstop(self):
        try:
            cmd = self.q.get_nowait()
            if cmd == 'stop':
                raise StopException
        except Empty:
            pass


    def running(self):
        return bool(self.th)

    def start(self, execute_q):
        if self.jobs:
            self.execute_q = execute_q
            self.q = Queue()
            self.th = Thread(target = self.thread, args = ())
            self.th.start()
        else:
            print("do not start http thread")

http_hook = HTTPHook()

hooks = [ http_hook ]
