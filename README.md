This is the initial version of the l7stat program. 

The basis for the development is to send layer 7 protocol statistics to a MQTT broker and a collectd plugin. 
The L7 protocol data is derived froma UNIX socket provided by the netifyd engine.
JSON data is passed to the MQTT publisher and then on to the broker. L7 data is also parsed and provided to collectd. This data is then provided to the output plugins
configured in collectd.

This initial body has been developed by:

Gurjot Chadda
Michael Foxworthy

We have not decided on the license yet, therefore this project will remain private.
