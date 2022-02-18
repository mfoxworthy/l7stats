from threading import RLock
from collectd_unixsock import Collectd
import socket


class CollectdFlowMan:

    def __init__(self):
        self._flow_dict = {}
        self._app_cat_dict = {}
        self._csocket = Collectd()
        self._lock = RLock()

    def addflow(self, digest, app_name, app_cat, iface_name):
        print("Waiting for a lock")
        with self._lock:
            self._flow_dict.update(
                {digest: {"app_name": app_name, "app_cat": app_cat, "iface_name": iface_name, "bytes_tx": 0,
                         "bytes_rx": 0, "purge": 0}})

    def _delflow(self, digest):
        print("Waiting for a lock")
        with self._lock:
            self._flow_dict.pop(digest)

    def updateflow(self, digest, bytes_tx, bytes_rx, purge):
        print("Waiting for a lock")
        if digest in self._flow_dict:

            with self._lock:
                if purge == 1:
                    self._flow_dict[digest]['bytes_tx'] = self._flow_dict[digest]['bytes_tx']
                    self._flow_dict[digest]['bytes_rx'] = self._flow_dict[digest]['bytes_rx']
                    self._flow_dict[digest]['purge'] = purge
                else:
                    self._flow_dict[digest]['bytes_tx'] = self._flow_dict[digest]['bytes_tx'] + bytes_tx
                    self._flow_dict[digest]['bytes_rx'] = self._flow_dict[digest]['bytes_rx'] + bytes_rx

    def sendappdata(self, interval):
        interval = {"interval": interval}
        try:
            hostname = socket.gethostname()
        except Exception as e:
            print("Well that sucks, I don't have a name")

        print("Waiting for a lock")
        with self._lock:
            for i in self._flow_dict:
                ident = hostname + "_" + self._flow_dict[i]['app_name'] + "_" + self._flow_dict[i]['iface_name']
                txbytes = self._flow_dict[i]['bytes_tx']
                rxbytes = self._flow_dict[i]['bytes_rx']
                self._csocket.putval(ident, "N:" + rxbytes + ":" + txbytes, interval)
                if self._flow_dict[i]['purge'] == 1:
                    self._delflow(i)

    def sendcatdata(self):
        """Send catagory flows to collectd socket"""
