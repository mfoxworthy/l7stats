# openwrt Engine
# Copyright (C) 2022 IPSquared, Inc. <https://www.ipsquared.com)>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

###############
#
# Written by:
#
# gchadda
# mfoxworthy
#
###############


import os
import threading
import signal

from l7stats_netifyd_uds import netifyd
import time
from random import randint
from l7stats_flow_manager import CollectdFlowMan

# TODO incorporate syslog package


def update_data(e, t):
    b = -1
    while not e.isSet():
        if b >= 0:
            fl.sendappdata(t)
        else:
            b += 1
        time.sleep(t)

def cleanup():
    global nd
    global eh
    nd.close()
    eh.set()

def sig_handler(s, f):
    print(f"Received stack {repr(s)} on frame {repr(f)}")
    cleanup()
    os._exit(0)

def gen_socket(e):
    fp = e.split("unix://")[-1]
    err = True

    try:
        retsock = nd.connect(uri=e)
    except:
        try:
            print(f"unlinking {fp}")
            os.unlink(fp)
        except OSError:
            if not os.path.exists(fp):
                print("f{fp} doesn't exist")
    else:
        err = False

    if err:
        if 0 == os.system("/etc/init.d/luci_statistics restart") and \
           0 == os.system("/etc/init.d/l7stats restart"):
            print("Successfully restarted luci and l7 stats")
            retsock = nd.connect(uri=e)
        else:
            retsock = None

    return retsock

SOCKET_ENDPOINT = "unix:///var/run/netifyd/netifyd.sock"
SLEEP_PERIOD = randint(1, 5)
APP_UPDATE_ITVL = 30

nd = netifyd()
fh = gen_socket(SOCKET_ENDPOINT)
fl = CollectdFlowMan()
eh = threading.Event()

signal.signal(signal.SIGHUP,  sig_handler)
signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT,  sig_handler)

# start off a thread to report data every 30 secs
threading.Thread(target=update_data, args=(eh, APP_UPDATE_ITVL)).start()

while True:
    try:
        jd = nd.read()

        if jd is None:
            nd.close()
            fh = None
            print(f"backing off for {SLEEP_PERIOD}..")
            time.sleep(SLEEP_PERIOD)
            nd = netifyd()
            fh = gen_socket(SOCKET_ENDPOINT)
            continue

        digest = jd['flow']['digest']

        if jd['type'] == 'flow':
            if jd['flow']['other_type'] != 'remote': continue

            if jd['flow']['ip_protocol'] != 6 and \
                    jd['flow']['ip_protocol'] != 17 and \
                    jd['flow']['ip_protocol'] != 132 and \
                    jd['flow']['ip_protocol'] != 136: continue

            if jd['flow']['detected_protocol'] == 5 or \
                    jd['flow']['detected_protocol'] == 8: continue

            app_name = jd['flow']['detected_application_name'].split(".")[-1]

            # TODO - Parse JSON files for app to category mappings
            app_cat = 0
            iface_name = jd['interface']

            fl.addflow(digest, app_name, app_cat, iface_name)

        if jd['type'] == 'flow_purge':
            bytes_tx = int(jd['flow']['local_bytes'])
            bytes_rx = int(jd['flow']['other_bytes'])
            tot_bytes = int(jd['flow']['total_bytes'])
            if digest:
                fl.updateflow(digest, bytes_tx, bytes_rx, tot_bytes, 1, 0)

        if jd['type'] == 'flow_status':
            bytes_tx = int(jd['flow']['local_bytes'])
            bytes_rx = int(jd['flow']['other_bytes'])
            tot_bytes = int(jd['flow']['total_bytes'])
            if digest:
                fl.updateflow(digest, bytes_tx, bytes_rx, tot_bytes, 0, 1)

        if jd['type'] == 'agent_status':
            """ we explicitly ignore agent_status ; not implemented """
            pass

    except Exception as err:
        print(str(err))
        continue

