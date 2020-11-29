from enum import Enum, auto

import socket
import threading

import json
import sys


# Base class with config options
class Base:
    def __init__(self):
        with open("config.json") as json_config:
            config = json.load(json_config)

        # Config constants
        self.SERVER_IP = config["server-ip"]
        self.SERVER_PORT = config["server-port"]
        self.HEADER_BYTES = config["header-bytes"]
        self.DISCON_MSG = config["disconnect-msg"]
        self.USER_EXIT_MSG = config["exit-msg"]

        commands = config["commands"]
        
        # Commands b/w server and root client
        self.CMD_LIST_ROOMS = commands["list-rooms"]
        self.CMD_GET_ROOM = commands["get-room"]
        self.CMD_CREATE_ROOM = commands["create-room"]



# States for FSM
class States(Enum):
    MAIN_MENU = auto()
    ENTER_MAIN = auto()
    SHOW_CHATS = auto()
    CREATE_CHAT = auto()
    EXIT = auto()



class FSM_Client(Base):
    def __init__(self):
        super().__init__()

        # Dict of states for the state machine
        self.stateDict = {
            "0": States.MAIN_MENU,
            "1": States.ENTER_MAIN,
            "2": States.SHOW_CHATS,
            "3": States.CREATE_CHAT,
            "4": States.EXIT
        }

        # Initializing state
        self.STATE = States.MAIN_MENU

        # Welcome messages and get username
        print("\n<Welcome to SudoChat!>")
        self.USERNAME = input("Please enter your username: ")
        print(f"\n<Hello, {self.USERNAME}!>")

        # Create main socket for client side application
        self.rootClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 5 second timeout for response from server
        self.rootClient.settimeout(5)

        # Connect to main chat server
        self.connectServer()

    
    def connectServer(self):
        try:
            self.rootClient.connect((self.SERVER_IP, self.SERVER_PORT))
        except:
            print("<Connection to server failed.>")
            return

        self.sendData(self.USERNAME)

        self.stateMachine()

    
    def __del__(self):
        if self.USERNAME:
            print(f"\n<Goodbye, {self.USERNAME}>")

    
    def stateMachine(self):
        while True:
            if self.STATE == States.MAIN_MENU:
                self.menu()
            elif self.STATE == States.ENTER_MAIN:
                self.mainRoom()
            elif self.STATE == States.SHOW_CHATS:
                self.showChatrooms()
            elif self.STATE == States.CREATE_CHAT:
                self.createChatroom()
            elif self.STATE == States.EXIT:
                break
            else:
                self.STATE = States.MAIN_MENU

    
    def menu(self):
        while True:
            print("\nInput a number for one of the following options:")
            print("1 - Enter main chat room")
            print("2 - Show all chat rooms")
            print("3 - Create a chat room")
            print("4 - Close")

            choice = input()

            if self.stateDict.get(choice):
                self.STATE = self.stateDict[choice]
                break
            else:
                print("<Invalid input - please try again!>")


    def mainRoom(self):
        # Enter main chat room (remain here till user exits from the client object)
        chat = ChatClient(self.SERVER_PORT + 1, self.USERNAME)
        print("\n")
        chat.enterChat()

        # Return to main menu after exiting the chat room
        self.STATE = States.MAIN_MENU


    # Get list of chat rooms from server and display
    def showChatrooms(self):
        try:
            self.sendData(self.CMD_LIST_ROOMS)  

            response = self.getData()  
            assert(response == "ACK")

            numRooms = int(self.getData())

            self.sendData("ACK")

            roomNames = []

            for _ in range(0, numRooms):
                roomNames.append(self.getData())

            self.enterChatroom(roomNames)
        except:
            print("<Error in showing chat rooms>")
            self.STATE = States.MAIN_MENU


    # To enter the chatroom we get the port and then connect
    def enterChatroom(self, roomNames: list):
        print("\nInput a number to enter a chat or return to main menu:")

        for ind, val in enumerate(roomNames):
            print(f"{ind + 1} - {val}")

        print(f"{len(roomNames) + 1} - Exit to main menu")

        choice = input()

        if int(choice) > 0 and int(choice) <= len(roomNames):
            room = roomNames[int(choice) - 1]

            try:
                self.sendData(self.CMD_GET_ROOM)

                response = self.getData()
                assert response == "ACK"

                self.sendData(room)

                port = self.getData()
                assert port != "NACK"

                # Enter the chat room
                chat = ChatClient(int(port), self.USERNAME)
                print("\n")
                chat.enterChat()

                # Return to main menu after exiting the chat room
                self.STATE = States.MAIN_MENU
            except:
                print(f"<Error in connecting to {room}>")
                self.STATE = States.MAIN_MENU
                return
        else:
            self.STATE = States.MAIN_MENU


    def createChatroom(self):
        try:
            self.sendData(self.CMD_CREATE_ROOM)

            response = self.getData()
            assert response == "ACK"
        except:
            print("\n<Failed to create chat room>")
            self.STATE = States.MAIN_MENU
            return

        print("\n<What would you like to name the chat room?>")
        name = input()

        try:
            self.sendData(name)

            # Server sends back 'NACK' if name is invalid
            port = self.getData()
            assert port != "NACK"

            # Enter the new chat room
            chat = ChatClient(int(port), self.USERNAME)
            print("\n")
            chat.enterChat()

            # Return to main menu after exiting the chat room
            self.STATE = States.MAIN_MENU
        except:
            print("<This room name is already in use>")
            self.STATE = States.MAIN_MENU
            return

    
    def getData(self) -> str:
        try:
            # Read header packet which gives length of payload
            msg_header = self.rootClient.recv(self.HEADER_BYTES)
            msg_len = int.from_bytes(msg_header, byteorder="big")
            
            # Read message payload from client
            payload = self.rootClient.recv(msg_len).decode("utf-8")

            return payload
        except:
            return None


    def sendData(self, message: str):
        if not message:
            return

        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")

        self.rootClient.send(header + message.encode("utf-8"))



class ChatClient(Base):
    def __init__(self, room_port: int, username: str):
        super().__init__()

        # Set up attributes
        self.SERVER_PORT = room_port
        self.USERNAME = username

        # Initialize the socket client
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Initialize threads for listening, sending data
        self.send_thread = threading.Thread(target=self.clientInput, daemon=True)
        self.read_thread = threading.Thread(target=self.clientListen, daemon=True)

        try:
            self.client.connect((self.SERVER_IP, self.SERVER_PORT))

            # Send the username header and username to the server
            self.sendData(self.USERNAME)
        except:
            print("<Connection to chat failed>")


    def __del__(self):
        # Disconnect from the chatroom
        try:
            self.sendData(self.DISCON_MSG)
        except:
            pass

        self.client.close()
        


    def enterChat(self):
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
            elif message == self.USER_EXIT_MSG:
                self.sendData(self.DISCON_MSG)

                print("<You have exited the chat room.>")
                self.__del__()
                break

            try:
                self.sendData(message)
            except:
                print("<Message send failed>")
                break


    def clientListen(self):
        while True:
            try:
                # Read length of incoming message from server
                msg_header = self.client.recv(self.HEADER_BYTES)
                msg_len = int.from_bytes(msg_header, byteorder="big")

                # Read message payload from server
                payload = self.client.recv(msg_len).decode("utf-8")
            except:
                break

            print("\r" + payload)
            print("\r<You> ", end="")

    
    def sendData(self, message: str):
        if not message:
            return

        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")
        self.client.send(header + message.encode("utf-8"))



start = FSM_Client()