import socket
import threading
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


    def __del__(self):
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

        # Begin listening for input from chat room
        self.thread_listen = threading.Thread(target=self.clientListen, daemon=True)
        self.thread_listen.start()

        # main thread is for taking user input and sending data
        self.clientInput()


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
        while True:
            # Read length of incoming message from server
            msg_header = self.client.recv(self.HEADER_BYTES)
            msg_len = int.from_bytes(msg_header, byteorder="big")

            # Read message payload from server
            payload = self.client.recv(msg_len).decode("utf-8")

            print(payload)
     

client = Client()

input()

print("hit end")


