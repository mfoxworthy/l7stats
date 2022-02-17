import threading
from collectd_unixsock import Collectd

class CollectdFlowMan:

    def __init__(self):
        self.flow_dict = {}
        self.app_group_dict = {}

    def addflow(self, digest, app_name, app_group, iface_name, bytes_tx, bytes_rx, purge):
        """ add flow"""

    def _delflow(self, digest):
        """ delete flow after purge type"""

    def updateflow(self, digest, bytes_tx, bytes_rx, purge):
        """ calculate delta and update byte counters """

    def sendappdata(self):
        """Send flows to collectd socket"""

    def sendcatdata(self):
        """Send catagory flows to collectd socket"""
