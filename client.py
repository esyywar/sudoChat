import socket
import threading

import msvcrt

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
        self.DISCON_MSG = config["disconnect-msg"]
        self.EXIT_MSG = config["exit-msg"]

        # Initialize the socket client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Initialize threads for listening, sending data
        self.send_thread = threading.Thread(target=self.clientInput, daemon=True)
        self.read_thread = threading.Thread(target=self.clientListen, daemon=True)

        self.sendUsername()


    def __del__(self):
        # Disconnect from the chatroom
        try:
            self.sendData(self.DISCON_MSG)
        except:
            pass

        self.client.close()
        print("<You have exited the chat room.>")


    def sendUsername(self):
        # Get a username for the active user
        self.username = input("Enter your username: ")

        if len(self.username) < 3 or len(self.username) > 30:
            print("Sorry, username must be between 3 and 30 characters long!")
            self.sendUsername()

        try:
            self.client.connect((self.SERVER_IP, 5001))

            # Send the username header and username to the server
            self.sendData(self.username)

        except:
            print("Username send to server failed...")
            sys.exit()

        # start threads for sending and receiving data
        self.send_thread.start()
        self.read_thread.start()

        # Continue running while threads active
        self.send_thread.join()
        self.read_thread.join()


    def clientInput(self):
        while True:
            print("<You>", end=" ")
            message = input()

            if message is None:
                continue
            elif message == self.EXIT_MSG:
                self.sendData(self.DISCON_MSG)
                self.client.close()
                break

            try:
                self.sendData(message)
            except:
                print("Message could not be sent...")
                break


    def clientListen(self):
        while True:
            # Read length of incoming message from server
            try:
                msg_header = self.client.recv(self.HEADER_BYTES)
            except:
                break

            msg_len = int.from_bytes(msg_header, byteorder="big")

            # Read message payload from server
            payload = self.client.recv(msg_len).decode("utf-8")

            if not payload:
                continue

            print("\r" + payload)
            print("\r<You> ", end="")

    
    def sendData(self, message: str):
        if not message:
            return

        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")

        self.client.send(header + message.encode("utf-8"))
     

client = Client()


