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
import ast

from l7stats_netifyd_uds import netifyd
import time
from random import randint
from l7stats_flow_manager import CollectdFlowMan


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
                print(f"{fp} doesn't exist")
            else:
                print(f"{fp} exists after attempting to unlink")
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

SOCKET_ENDPOINT   = "unix:///var/run/netifyd/netifyd.sock"
SLEEP_PERIOD      = randint(1, 5)
APP_UPDATE_ITVL   = 30
app_to_cat        = dict()
APP_PROTO_FILE    = "/etc/netify-fwa/app-proto-data.json"
APP_CAT_FILE      = "/etc/netify-fwa/netify-categories.json"
nd                = netifyd()
fh                = gen_socket(SOCKET_ENDPOINT)
fl                = CollectdFlowMan()
eh                = threading.Event()

signal.signal(signal.SIGHUP,  sig_handler)
signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT,  sig_handler)


for fp in (APP_PROTO_FILE, APP_CAT_FILE):
    with open(fp,mode="r") as f:
         s = f.read()

    if isinstance(s, str):
        app_to_cat[fp] = ast.literal_eval(s)
        assert isinstance(app_to_cat[fp], dict) == True
    else:
        raise RuntimeError("app mapping failure..")

# start off a thread to report data every APP_UPDATE_ITVL secs
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

        if jd['type'] == 'noop':
            print("detected noop, continuing...")
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

            app_name_str = jd['flow']['detected_application_name']
            app_int, *app_trail = app_name_str.split("netify")
            if 1 == len(app_trail):
                app_int = app_int.rstrip(".")
                app_name = app_trail[0].lstrip(".")
                print(f"app_int == {app_int}, app_name = {app_name}")
                app_cat = app_to_cat[APP_CAT_FILE ]['applications'][str(app_int)]
                for k,v in app_to_cat[APP_PROTO_FILE]["application_category_tags"].items():
                    if str(app_cat) == str(v):
                        app_cat_name = k
                        break
            else:
                print(f"failure.... read in {app_name_str}, unable to parse further")
                app_name     = "unknown"
                app_cat      = "unknown"
                app_cat_name = "unknown"

            print(f"app_cat = {app_cat}, app_cat_name = {app_cat_name}")

            iface_name = jd['interface']

            if digest:
                fl.addflow(digest, app_name, app_cat_name, iface_name)

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

    except KeyError as ke:
        print(f"hit key error for : {ke}")
        print(jd)
        continue
    except Exception as e:
        print(f"hit general exception: {e}")
        continue
