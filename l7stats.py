import sys
import signal

NETIFY_FWA_DIR = "/usr/share/netify-fwa/"
sys.path.insert(1, NETIFY_FWA_DIR)
import nfa_netifyd
import time
from random import randint
from flow_manager import CollectdFlowMan

SOCKET_ENDPOINT = "unix:///var/run/netifyd/netifyd.sock"
SLEEP_PERIOD = randint(1, 5)

nd = nfa_netifyd.netifyd()
fh = nd.connect(uri=SOCKET_ENDPOINT)
fl = CollectdFlowMan()


def sig_alarm_handler(s, f):
    fl.sendappdata(30)


signal.signal(signal.SIGALRM, sig_alarm_handler)

while True:
    try:
        jd = nd.read()

        if jd is None:
            nd.close()
            fh = None
            print("backing off for a sec...")
            time.sleep(SLEEP_PERIOD)
            continue

        if jd['type'] == 'flow':
            if jd['flow']['other_type'] != 'remote': continue
            if not jd['internal']: continue

            if jd['flow']['ip_protocol'] != 6 and \
                    jd['flow']['ip_protocol'] != 17 and \
                    jd['flow']['ip_protocol'] != 132 and \
                    jd['flow']['ip_protocol'] != 136: continue

            if jd['flow']['detected_protocol'] == 5 or \
                    jd['flow']['detected_protocol'] == 8: continue

            digest = jd['flow']['digest']
            app_name = jd['flow']['detected_application_name'].split(".")[-1]

            # TODO - Parse JSON files for app to category mappings
            app_cat = 0
            iface_name = jd['interface']

            fl.addflow(digest, app_name, app_cat, iface_name)

        if jd['type'] == 'flow_purge':
            bytes_tx = int(jd['flow']['local_bytes'])
            bytes_rx = int(jd['flow']['other_bytes'])
            if digest:
                fl.updateflow(digest, bytes_tx, bytes_rx, 1)

        if jd['type'] == 'flow_status':
            bytes_tx = int(jd['flow']['local_bytes'])
            bytes_rx = int(jd['flow']['other_bytes'])
            if digest:
                fl.updateflow(digest, bytes_tx, bytes_rx, 0)

        if jd['type'] == 'agent_status':
            print("ignoring agent_status shit")
            pass

    except Exception as err:
        print(str(err))
        continue
    except KeyboardInterrupt:
        nd.close()
