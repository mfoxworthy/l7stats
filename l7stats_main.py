###############
#
#
# Written by:
#
# gchadda
# mfoxworthy
#
#
#
###############


import sys
import threading

NETIFY_FWA_DIR = "/usr/share/netify-fwa/"
sys.path.insert(1, NETIFY_FWA_DIR)
import nfa_netifyd
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


SOCKET_ENDPOINT = "unix:///var/run/netifyd/netifyd.sock"
SLEEP_PERIOD = randint(1, 5)
APP_UPDATE_ITVL = 30

nd = nfa_netifyd.netifyd()
fh = nd.connect(uri=SOCKET_ENDPOINT)
fl = CollectdFlowMan()
eh = threading.Event()

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
            nd = nfa_netifyd.netifyd()
            fh = nd.connect(uri=SOCKET_ENDPOINT)
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
    except KeyboardInterrupt:
        nd.close()
        eh.set()

