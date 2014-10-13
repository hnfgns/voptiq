voptiq
======

voptiq ains to visualize optiq trace. It comes with a graph model that captures optiq planning sets and provides a cli
and web interface(powered by bottle.py) to easily interact with the trace the data.

ps: currently voptiq only extracts and prints out planning iterations. the vision is to make the web ui more interactive.


usage
=====
* make sure voptiq.py is executable with `chmod +x voptiq.py`
* simply run `voptiq.py -w` to start web server and navigate to web ui
* feed the path of your optiq trace either in absolute path or relative to where voptiq.py resides
