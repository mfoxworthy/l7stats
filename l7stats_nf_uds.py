#import socket and sys
import json
import socket
import sys
import os

def Main():

    server_address = '/var/run/l7stats.sock'

    #Make sure the socket does not alredy exist
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    #create a UDS socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    #Bind the socket to the port

    print("Starting up on {}".format(server_address))
    s.bind(server_address)

    """listen waits for the client to approach
       the server to make a connection"""
    s.listen(1)

    while True:
        #Waits for a connection
        print("Waiting for a connection")
        connection, client_address = s.accept()
        fh = connection.makefile()
        try:
            print('connection from', client_address)
            #Receive the data in small chunks and retransmit it
            while True:
                data = fh.readline()
                jd = json.loads(data)
                print(jd)
        finally:
            #Free the connection
            connection.close()

if __name__ == "__main__":
    Main()