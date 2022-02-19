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
# TODO incorporate syslog package


from threading import RLock
from l7stats_collectd_uds import Collectd
import socket


class CollectdFlowMan:

    def __init__(self):
        self._flow = {}
        self._app = {}
        self._cat = {}
        self._csocket = Collectd()
        self._lock = RLock()

    def addflow(self, dig, app, cat, iface):
        app_int_name = app + "_" + iface
        if app_int_name not in self._app.keys():
            with self._lock:
                self._app.update({app_int_name: {"bytes_tx": 0, "bytes_rx": 0, "tot_bytes": 0}})
        with self._lock:
            self._flow.update(
                {dig: {"app_name": app, "app_cat": cat, "iface_name": iface, "bytes_tx": 0,
                          "bytes_rx": 0, "tot_bytes": 0, "purge": 0, "status": 0}})

    def _delflow(self, dig):
        _ = self._flow.pop(dig)
        if dig in self._flow.keys():
            print("Digest not found...\n", dig)

    def updateflow(self, dig, tx_bytes, rx_bytes, t_bytes, purge, status):
        if status == 1:
            self._flow[dig]["status"] = 1
        u_bit = self._flow[dig]["status"]
        c_app = self._flow[dig]["app_name"] + "_" + self._flow[dig]["iface_name"]

        if dig in self._flow.keys():
            with self._lock:
                if purge == 1 and u_bit == 0:
                    self._app[c_app]['bytes_tx'] += tx_bytes
                    self._app[c_app]['bytes_rx'] += rx_bytes
                    self._app[c_app]['tot_bytes'] += t_bytes
                    self._delflow(dig)
                else:
                    c_tx = self._flow[dig]['bytes_tx']
                    c_rx = self._flow[dig]['bytes_rx']
                    c_tot = self._flow[dig]['tot_bytes']
                    self._flow[dig]['bytes_tx'] = tx_bytes
                    self._flow[dig]['bytes_tx'] = rx_bytes
                    self._flow[dig]['tot_bytes'] = t_bytes
                    self._app[c_app]['bytes_tx'] += tx_bytes - c_tx
                    self._app[c_app]['bytes_rx'] += rx_bytes - c_rx
                    self._app[c_app]['tot_bytes'] += t_bytes - c_tot

    def sendappdata(self, interval):
        interval = {"interval": interval}

        try:
            hostname = socket.gethostname()
        except Exception as e:
            hostname = "fixyernamedude"
            print("Please set the hostname")
        with self._lock:
            for i in list(self._app):
                id_rxtx = hostname + "/application_" + i + "/if_octets"
                id_tot = hostname + "/application_" + i + "/total_bytes"
                txbytes = self._app[i]['bytes_tx']
                rxbytes = self._app[i]['bytes_rx']
                tbytes = self._app[i]['tot_bytes']
                cd_if = ["N", txbytes, rxbytes]
                cd_tot = ["N", tbytes]
                self._csocket.putval(id_rxtx, cd_if, interval)
                self._csocket.putval(id_tot, cd_tot, interval)

    def sendcatdata(self):
        """"""
        # TODO Send catagory flows to collectd socket