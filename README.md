# hoocron
Hoocron is cron alternative with different hooks to trigger immediate execution of jobs

# Installation
~~~
pip3 install hoocron
~~~

# Usage examples

## Simple cron
We will run program /bin/touch with different arguments.

Simplest case:
~~~shell
$ hoocron.py -j TICK echo ...tick-tock... -p TICK 10s
started cron thread with 1 jobs: TICK
run TICK from cron
...tick-tock...
Return code for TICK: 0

run TICK from cron
...tick-tock...
Return code for TICK: 0
~~~

This command configures *job* (what to run, command and arguments) and *hook* (when to run). This very similar to cron. Here we have job named 'J' which runs `/bin/touch /tmp/touch` and configured cron period (-p) for job J to 20 seconds.

We can run many jobs at once, lets add also 'echo'

~~~shell
$ hoocron.py -j Echo5 echo tick-tock 5 seconds -j Echo10 echo tick-tock 10 seconds -p Echo5 5 -p Echo10 10

### immediately, 0s from start
run Echo5 from cron
run Echo10 from cron
tick-tock 5 seconds
tick-tock 10 seconds
Return code for Echo5: 0
Return code for Echo10: 0

### 5s from start
run Echo5 from cron
tick-tock 5 seconds
Return code for Echo5: 0

### 10s from start
run Echo5 from cron
run Echo10 from cron
tick-tock 5 seconds
tick-tock 10 seconds
...
~~~


## Webhook HTTP trigger

HTTP plugin provides HTTP GET and HTTP POST interface to start cron job right now.

Now, lets make it more interesting, we will also run job if get HTTP request using `--http-get` option (or just `--get`).

~~~shell
$ hoocron.py -j J /bin/touch /tmp/touch -p J 5m --get J
Loading hoocron_plugin.cron
Loading hoocron_plugin.http
Loading hoocron_plugin.redis
started cron thread with 1 jobs: J
started http thread on :5152 with 1 jobs: J
run J from cron
Return code for J: 0
~~~

Hoocron immediately runs Job (because cron plugin runs each job for first time right from start) and waits 5 minutes for next run. We do not want this, so we do:

~~~shell
$ curl http://localhost:5152/J
OK
~~~

This triggers hoocron execution of job J:
~~~
run J from HTTP GET request from 127.0.0.1
Return code for J: 0
~~~

### Cron with HTTP POST method
If you want to use HTTP POST method, use `--post` (or `--http-post` alias) instead of `--get`.

### Running hoocron with http in production
If you need extra HTTP features, such as https support or additional access control, run hoocron behind real webserver working as reverse proxy.

# Throttling and policies
Hoocron guarantees that only one copy of job (with same job name) is running at same time (same jobs will not overlap): hoocron will never start second copy of same job until first one is finished. 

But hoocron can not prevent same script started from any other source (e.g. from shell).

There are two policies for job, `ignore` (default) and `asap`. 

With policy `ignore`, if hoocron gets request to start job, and this job is already running, request is ignored.

With policy `asap`, if hoocron gets request to start job, and this job is already running, it will set special flag and will run same job again immediately after first instance of job is finished (and again, new request will raise flag again). Note, if there are many requests during one execution of job, it will be executed just once. 

To see difference, compare ignore policy (default) with this command:
~~~shell
hoocron.py -j J sleep 10 -p J 3
~~~

and same with `asap` policy
~~~shell
hoocron.py -j J sleep 10 -p J 3 --policy J asap
~~~

# See also

[Redis plugin](https://github.com/yaroslaff/hoocron-plugin-redis)