# l7stats Engine
# Copyright (C) 2022 IPSquared, Inc. <https://www.ipsquared.com>
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
# Written by:
#
# mfoxworthy
# gchadda
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
        if dig not in self._flow.keys():
            print("Digest not found...\n", dig)
        else:
            _ = self._flow.pop(dig, None)

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
                    self._flow[dig]['bytes_tx'] = tx_bytes
                    self._flow[dig]['bytes_tx'] = rx_bytes
                    self._flow[dig]['tot_bytes'] = t_bytes
                    self._app[c_app]['bytes_tx'] += tx_bytes - self._flow[dig]['bytes_tx']
                    self._app[c_app]['bytes_rx'] += rx_bytes - self._flow[dig]['bytes_rx']
                    self._app[c_app]['tot_bytes'] += t_bytes - self._flow[dig]['tot_bytes']

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