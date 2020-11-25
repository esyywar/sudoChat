import socket
import select
import json
import sys

class Client:
    def __init__(self):
        # Read configuration data from config file
        with open("config.json") as json_config:
            config = json.load(json_config)

        self.SERVER_IP = config["server-ip"]
        self.SERVER_PORT = config["server-port"]
        self.HEADER_BYTES = config["header-bytes"]

        # Initialize the socket client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sendUsername()

    def sendUsername(self):
        # Get a username for the active user
        self.username = input("Enter your username: ")

        if len(self.username) < 3 or len(self.username) > 30:
            print("Sorry, username must be between 3 and 30 characters long!")
            self.sendUsername()

        # Prepare to transmit username header
        username_header = len(self.username).to_bytes(self.HEADER_BYTES, byteorder="big")

        try:
            self.client.connect((self.SERVER_IP, self.SERVER_PORT))
            self.client.setblocking(False)

            # Send the username header and username to the server
            self.client.send(username_header + self.username.encode('utf-8'))
        except:
            print("Username send to server failed...")
            sys.exit()
            

client = Client()
input()


