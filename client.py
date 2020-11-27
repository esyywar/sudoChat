from enum import Enum, auto

import socket
import threading

import msvcrt

import json
import sys


class States(Enum):
    MAIN_MENU = auto()
    ENTER_MAIN = auto()
    SHOW_CHATS = auto()
    CREATE_CHAT = auto()
    EXIT = auto()



class FSM_Client:
    def __init__(self):
        self.stateDict = {
            "0": States.MAIN_MENU,
            "1": States.ENTER_MAIN,
            "2": States.SHOW_CHATS,
            "3": States.CREATE_CHAT,
            "4": States.EXIT
        }

        self.state = States.MAIN_MENU

        print("\n<Welcome to SudoChat!>")

        self.username = input("Please enter your username: ")

        print(f"\n<Hello, {self.username}!>")

        # Enter the state machine
        self.state_machine()

    
    def __del__(self):
        if self.username:
            print(f"<Goodbye, {self.username}>")

    
    def state_machine(self):
        while True:
            if self.state == States.MAIN_MENU:
                self.menu()
            elif self.state == States.ENTER_MAIN:
                self.main_room()
            elif self.state == States.SHOW_CHATS:
                self.show_chatrooms()
            elif self.state == States.CREATE_CHAT:
                self.create_chatroom()
            elif self.state == States.EXIT:
                break
            else:
                self.state = States.MAIN_MENU

    
    def menu(self):
        while True:
            print("\nEnter a number for one of the following options:")
            print("1 - Enter main chat room")
            print("2 - Show all chat rooms")
            print("3 - Create a chat room")
            print("4 - Close")

            choice = input()

            if self.stateDict.get(choice):
                self.state = self.stateDict[choice]
                break
            else:
                print("<Invalid input - please try again!>")


    def main_room(self):
        print("\n")
        
        # Enter main chat room (remain here till user exits from the client object)
        Client(5001, self.username)

        # Return to main menu after exiting the chat room
        self.state = States.MAIN_MENU


    def show_chatrooms(self):
        print("showing chatroom")
        self.state = States.MAIN_MENU


    def enter_chatroom(self):
        print("entering chatroom")
        self.state = States.MAIN_MENU


    def create_chatroom(self):
        print("creating chatroom")
        self.state = States.MAIN_MENU



class Client:
    def __init__(self, port: int, username: str):
        # Read configuration data from config file
        with open("config.json") as json_config:
            config = json.load(json_config)

        self.SERVER_PORT = port
        self.USERNAME = username

        self.SERVER_IP = config["server-ip"]
        self.HEADER_BYTES = config["header-bytes"]
        self.DISCON_MSG = config["disconnect-msg"]
        self.EXIT_MSG = config["exit-msg"]

        # Initialize the socket client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Initialize threads for listening, sending data
        self.send_thread = threading.Thread(target=self.clientInput, daemon=True)
        self.read_thread = threading.Thread(target=self.clientListen, daemon=True)

        self.connectRoom()


    def __del__(self):
        # Disconnect from the chatroom
        try:
            self.sendData(self.DISCON_MSG)
        except:
            pass

        self.client.close()
        print("<You have exited the chat room.>")


    def connectRoom(self):
        try:
            self.client.connect((self.SERVER_IP, self.SERVER_PORT))

            # Send the username header and username to the server
            self.sendData(self.USERNAME)
        except:
            print("Connection to chat failed...")
            return

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



start = FSM_Client()