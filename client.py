import socket
import threading
import json
import sys
import time

class Client:
    def __init__(self):
        # Read configuration data from config file
        with open("config.json") as json_config:
            config = json.load(json_config)

        self.SERVER_IP = config["server-ip"]
        self.SERVER_PORT = config["server-port"]
        self.HEADER_BYTES = config["header-bytes"]
        self.DISCON_MSG = config["disconnect-msg"]

        # Initialize the socket client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sendUsername()


    def __del__(self):
        self.sendData(self.DISCON_MSG)
        self.client.close()
        print("Client closed.")


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

            # Send the username header and username to the server
            self.client.send(username_header + self.username.encode('utf-8'))

        except:
            print("Username send to server failed...")
            sys.exit()

        # start threads for sending and receiving data
        self.send_thread = threading.Thread(target=self.clientInput)
        self.read_thread = threading.Thread(target=self.clientListen)
        self.send_thread.start()
        self.read_thread.start()
        self.send_thread.join()
        self.read_thread.join()


    def clientInput(self):
        while True:
            print(f"<{self.username}>", end=" ")
            message = input()

            if message is None:
                continue

            msg_header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")

            try:
                self.client.send(msg_header + message.encode('utf-8'))
            except:
                print("Message could not be sent...")
                break

    def clientListen(self):
        print("client is listening for messages...")

        while True:
            # Read length of incoming message from server
            msg_header = self.client.recv(self.HEADER_BYTES)
            msg_len = int.from_bytes(msg_header, byteorder="big")

            # Read message payload from server
            payload = self.client.recv(msg_len).decode("utf-8")

            if not payload:
                print("clientListen error")
                break

            print(payload)

    
    def sendData(self, message: str):
        if not message:
            return

        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")

        self.client.send(header + message.encode("utf-8"))
     

client = Client()


