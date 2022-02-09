#Contributors:
#
#mfoxworthy
#gchadda
#
#/


import paho.mqtt.client as mqtt
import socket
import sys
import json
import os

debug_mode     = True
max_size_debug = 100

def get_topic(NET_IF):
    with open("/sys/class/net/" + NET_IF + "/address") as f:
        temp = f.readlines()
    mac = temp[0].strip().replace(":","")
    print(mac)
    return "netifyd/" + mac

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

def sock_listener(topic, socket_path, username, password, server_address):
    json_str = str()
    temp = str()
    ready_to_send = False
    print("Opening socket...")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.connect(socket_path)
    mqtt_sub = mqtt.Client(client_id="", clean_session=True, userdata=None, transport="tcp")
    mqtt_sub.enable_logger()
    mqtt_sub.username_pw_set(username=username, password=password)
    mqtt_sub.connect(server_address)
    mqtt_sub.on_connect = on_connect
    mqtt_sub.loop_start()
    print("Listening...")
    while True:
        datagram = server.recv(1024)
        if not datagram:
            break
        else:
             j_datagram = datagram.decode('utf-8')
             j_datagram = j_datagram.replace('"', "'")

             try:
                 temp = json.loads(j_datagram)
             except:
                 for i,c in enumerate(j_datagram):
                     try:
                         if j_datagram[i] == "}" and j_datagram[i+1] != ",":
                             ready_to_send = True
                     except IndexError:
                         ready_to_send = True
                     except Exception as e:
                         #print(e)
                         print("wtf while processing")
                     finally:
                         json_str += j_datagram[i]
                         if ready_to_send:
                             #reset state
                             ready_to_send = False

                             #TODO #1 make external def
                             mqtt_sub.publish(topic, json_str)
                             print(f"Publishing {len(json_str)} bytes")
                             if debug_mode and len(json_str) < max_size_debug:
                                 print(f"{json_str}")
                             json_str = str()
             else:
                 json_str += str(temp)

                 #TODO #1 make external def
                 mqtt_sub.publish(topic, json_str)
                 print(f"Publishing {len(json_str)} bytes")
                 if debug_mode and len(json_str) < max_size_debug:
                     print(f"{json_str}")
                 json_str = str()

if __name__ == '__main__':
    topic = get_topic("eth1")
    username = "sturdynet"
    password = "SturdyNet100!"
    server_address = "54.213.151.89"
    socket_path = "/var/run/netifyd/netifyd.sock"
    sock_listener(topic, socket_path, username, password, server_address)
