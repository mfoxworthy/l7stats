###############
#
#
# Written by:
#
# mfoxworthy
# gchadda
#
#
#
################

from threading import RLock
from collectd_unixsock import Collectd
import socket


class CollectdFlowMan:

    def __init__(self):
        self._flow_dict = {}
        self._app_tot_dict = {}
        self._cat_tot_dict = {}
        self._csocket = Collectd()
        self._lock = RLock()

    def addflow(self, digest, app_name, app_cat, iface_name):
        #print("Waiting for a lock")
        app_int_name = app_name + "_" + iface_name
        if app_int_name not in self._app_tot_dict.keys():
            with self._lock:
                self._app_tot_dict.update({app_int_name: {"bytes_tx": 0, "bytes_rx": 0, "tot_bytes": 0}})
        with self._lock:
            self._flow_dict.update(
                {digest: {"app_name": app_name, "app_cat": app_cat, "iface_name": iface_name, "bytes_tx": 0,
                          "bytes_rx": 0, "tot_bytes": 0, "purge": 0, "status": 0}})

    def _delflow(self, digest):
        #print("Waiting for a lock")
        _ = self._flow_dict.pop(digest)
        if digest in self._flow_dict.keys():
            print("Digest wasn't deleted, Hmmmm. ", digest)
        else:
            print("Digest Deleted!")

    def updateflow(self, digest, bytes_tx, bytes_rx, tot_bytes, purge, status):
        if status == 1:
            self._flow_dict[digest]["status"] = 1
        #print("Waiting for a lock")
        u_bit = self._flow_dict[digest]["status"]
        c_app = self._flow_dict[digest]["app_name"] + "_" + self._flow_dict[digest]["iface_name"]

        if digest in self._flow_dict.keys():
            with self._lock:
                if purge == 1 and u_bit == 0:
                    self._app_tot_dict[c_app]['bytes_tx'] += bytes_tx
                    self._app_tot_dict[c_app]['bytes_rx'] += bytes_rx
                    self._app_tot_dict[c_app]['tot_bytes'] += tot_bytes
                    self._delflow(digest)
                    print(self._app_tot_dict)
                else:
                    c_tx = self._flow_dict[digest]['bytes_tx']
                    c_rx = self._flow_dict[digest]['bytes_rx']
                    c_tot = self._flow_dict[digest]['tot_bytes']
                    self._flow_dict[digest]['bytes_tx'] = bytes_tx
                    self._flow_dict[digest]['bytes_tx'] = bytes_rx
                    self._flow_dict[digest]['tot_bytes'] = tot_bytes
                    self._app_tot_dict[c_app]['bytes_tx'] += bytes_tx - c_tx
                    self._app_tot_dict[c_app]['bytes_rx'] += bytes_rx - c_rx
                    self._app_tot_dict[c_app]['tot_bytes'] += tot_bytes - c_tot
                    print(self._app_tot_dict)

    def sendappdata(self, interval):
        interval = {"interval": interval}
        try:
            hostname = socket.gethostname()
        except Exception as e:
            hostname = "fixyernamedude"
            print("Please set the hostname")
        print("Updating collectd socket with:" + "\n\n\n", self._app_tot_dict)
        print("\n\n\n" + "Current Flow Dict" + "\n\n\n", self._flow_dict)
        #print("Waiting for a lock")
        with self._lock:
            for i in list(self._app_tot_dict):
                identi_rxtx = hostname + "/" + i + "/if_octets"
                identi_tot = hostname + "/" + i + "/total_bytes"
                txbytes = self._app_tot_dict[i]['bytes_tx']
                rxbytes = self._app_tot_dict[i]['bytes_rx']
                totbytes = self._app_tot_dict[i]['tot_bytes']
                self._csocket.putval(identi_rxtx, "N:" + str(txbytes) + ":" + str(rxbytes), interval)
                self._csocket.putval(identi_tot, "N:" + str(totbytes), interval)

    def sendcatdata(self):
        """Send catagory flows to collectd socket"""