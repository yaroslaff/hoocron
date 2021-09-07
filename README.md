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



## Cron with webhook trigger

Now, lets make it more interesting, we will also run job if get HTTP request

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

# See also

[Redis plugin](https://github.com/yaroslaff/hoocron-plugin-redis)