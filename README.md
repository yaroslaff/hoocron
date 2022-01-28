# hoocron
Hoocron is cron alternative with different hooks to trigger immediate execution of jobs

# Installation
~~~
pip3 install hoocron
~~~

or, install right from repo:
~~~
pip3 install git+https://github.com/yaroslaff/hoocron
~~~

# Usage examples

## Simplest cron

Hoocron has built-in dummy job `TICK` which just print 'tick!' and report how long hoocron were running, lets call it with `--period` 5s:

~~~shell
$ hoocron.py -p TICK 5s
...
run TICK from cron
Tick! (uptime: 1 seconds)
Result(TICK): ticked

run TICK from cron
Tick! (uptime: 5 seconds)
Result(TICK): ticked
~~~

Surely we can replace dummy and useless job TICK with our better useless job MYTICK:

~~~shell
$ hoocron.py -j MYTICK echo my tick is better -p MYTICK 5s
...
run MYTICK from cron
my tick is better
Result(MYTICK): 0

run MYTICK from cron
my tick is better
Result(MYTICK): 0
~~~

This command configures *job* (what to run, command and arguments, `-j`) and *hook* (when to run, `-p` for cron-alike periodical run). This very similar to cron. 

We can run many jobs at once, lets make two echo jobs:
~~~shell
$ hoocron.py -j J1 echo every5 -j J2 echo every10 -p J1 5s -p J2 10s | grep every
every5
every10
every5
every5
every10
every5
every5
every10
~~~

## Webhook HTTP trigger

Most important feature of hoocron is different hooks which you can bind to jobs. 

HTTP plugin provides HTTP GET and HTTP POST interface to start cron job right now.

Now, lets make it more interesting, we will also run job after getting HTTP request using `--get` option.

run `hoocron.py --get TICK` and (in other session) run `curl http://localhost:5152/TICK`.

So, instead of running some cron job every N minutes, you may run it asynchronously, on demand. And you can combine both: `hoocron.py --get TICK -p TICK 1h` will run tick every hour, but you can always trigger it over HTTP.

### Cron with HTTP POST method
If you want to use HTTP POST method, use `--post` instead of `--get`.

### Other asynchronous hooks
Hoocron is easy to extend with other python modules. For example, every app in any programming language (supporting [redis](https://redis.io/)) can trigger hoocron jobs doing `LPUSH` redis command. (Need to install [Redis plugin](https://github.com/yaroslaff/hoocron-plugin-redis) for hoocron)

[Websocket](https://github.com/yaroslaff/hoocron-plugin-websocket) plugin connects to websocket (SocketIO) server (usually [ws-emit](https://github.com/yaroslaff/ws-emit)) and expect signals from server. For example, to run some job when server will have new data.

### Running hoocron with http in production
If you need extra HTTP features, such as https support or additional access control, run hoocron behind real webserver working as reverse proxy.

# Throttling and policies
Hoocron guarantees that only one copy of job (with same job name) is running at same time (same jobs will not overlap): hoocron will never start second copy of same job until first one is finished. 

But hoocron can not prevent same script started from any other source (e.g. from shell).

There are two policies for job, `ignore` (default) and `asap`. 

With policy `ignore`, if hoocron gets request to start job and this job is already running, request is ignored.

With policy `asap`, if hoocron gets request to start job and this job is already running, it will set special flag and will run same job again immediately after first instance of job is finished (and again, new request will raise flag again). Note, if there are many requests during one execution of job, it will be executed just once. 

To see difference, compare ignore policy (default) with this command:
~~~shell
hoocron.py -j J sleep 10 -p J 3
~~~

and same with `asap` policy
~~~shell
hoocron.py -j J sleep 10 -p J 3 --policy J asap
~~~

# See also

- [Redis plugin](https://github.com/yaroslaff/hoocron-plugin-redis)
- [Webhook plugin](https://github.com/yaroslaff/hoocron-plugin-websocket)