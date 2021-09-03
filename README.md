# hoocron
Cron with webhook trigger

# Usage examples
We will run program /bin/touch with different arguments.

Simplest case:
~~~
./hoocron.py -j J1 /bin/touch /tmp/touch -p J1 20s
~~~

This command configures *job* (what to run, command and arguments) and *hook* (when to run). 