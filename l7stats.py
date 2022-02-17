# Contributors:
#
# mfoxworthy
# gchadda
#
# /

import socket
import sys
import json
from uci import Uci
from os.path import exists
from flow_manager import CollectdFlowMan


debug_mode = True
max_size_debug = 2 ** 17
buffer_sz = 2 ** 17
flow_dict = {}
app_group_dict = {}


def sock_listener(socket_path):
    json_str = str()
    f = CollectdFlowMan()
    temp = str()
    ready_to_send = False
    print("Opening socket...")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if exists(socket_path):
        server.connect(socket_path)
    else:
        print("Socket file doesn't exist")
    while True:
        datagram = server.recv(buffer_sz)
        if not datagram:
            break
        else:
            j_datagram = datagram.decode('utf-8')
            j_datagram = j_datagram.replace('"', "'")

            try:
                temp = json.loads(j_datagram)
            except:
                for i, c in enumerate(j_datagram):
                    try:
                        if j_datagram[i] == "}" and j_datagram[i + 1] != ",":
                            ready_to_send = True
                    except IndexError:
                        ready_to_send = True
                    except Exception as e:
                        print(
                            "Rx issue in e", repr(e),
                            "\nFatal")
                    finally:
                        json_str += j_datagram[i]
                        if ready_to_send:
                            # reset state
                            ready_to_send = False

                            # TODO #1 make external def
                            mqtt_sub.publish(topic, json_str)
                            print(f"Publishing {len(json_str)} bytes")
                            if debug_mode and len(json_str) < max_size_debug:
                                print(f"{json_str}")
                            json_str = str()
            else:
                json_str += str(temp)

                # TODO #1 make external def
                mqtt_sub.publish(topic, json_str)
                print(f"Publishing {len(json_str)} bytes")
                if debug_mode and len(json_str) < max_size_debug:
                    print(f"{json_str}")
                json_str = str()


if __name__ == '__main__':
    u = Uci()
    try:
        config = u.get_all("l7stats", "config")
    except Exception as e:
        print(e)
    else:
        print("Configuration file loaded")
    socket_path = config["socket_path"]
    sock_listener(socket_path)
