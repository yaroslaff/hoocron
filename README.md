# hoocron
Cron with different triggers to kick immediate execution of jobs

# Installation
~~~
pip3 install hoocron
~~~

# Usage examples

## Simple cron
We will run program /bin/touch with different arguments.

Simplest case:
~~~
hoocron.py -j J /bin/touch /tmp/touch -p J 20s
~~~

This command configures *job* (what to run, command and arguments) and *hook* (when to run). This very similar to cron.

We can run many jobs at once, lets add also 'echo'


~~~
$ bin/hoocron.py -j J1 'echo 1' -j J2 'echo a b c' -p J1 5 -p J2 10
Loading hoocron_plugin.cron
Loading hoocron_plugin.http
started cron thread with 2 jobs: J1 J2

### immediately
run J1 from cron
run J2 from cron
1
a b c
Return code for J1: 0
Return code for J2: 0

### after 5 seconds
run J1 from cron
1
Return code for J1: 0

### after 10 seconds
run J1 from cron
run J2 from cron
1
a b c
Return code for J1: 0
Return code for J2: 0
~~~


## Webhook HTTP trigger

built-in `http` plugin provides HTTP GET and HTTP POST interface to trigger cron executions.

Now, lets make it more interesting, we will also run job if get HTTP request using `--http-get` option (or just `--get`).

~~~
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

~~~
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

### Running in production
If you need extra HTTP features, such as https support or additional access control, run hoocron behind real webserver working as reverse proxy.

# Throttling and policies
Hoocron guarantees that only one copy of job (with same job name) is running at same time (same jobs will not overlap): hoocron will never start second copy of same job until first one is finished. 

But hoocron can not prevent same script started from any other source (e.g. from shell).

There are two policies for job, `ignore` (default) and `asap`. 

With policy `ignore`, if hoocron gets request to start job, and this job is already running, request is ignored.

With policy `asap`, if hoocron gets request to start job, and this job is already running, it will set special flag and will run same job again immediately after first instance of job is finished (and again, new request will raise flag again). Note, if there are many requests during one execution of job, it will be executed just once. 


# See also

[Redis plugin](https://github.com/yaroslaff/hoocron-plugin-redis)