#!/usr/bin python3

import socket
import threading
import select
import json


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
        self.MAX_ROOMS =  config["max-chat-rooms"]

        commands = config["commands"]
        
        # Commands b/w server and root client
        self.CMD_LIST_ROOMS = commands["list-rooms"]
        self.CMD_GET_ROOM = commands["get-room"]
        self.CMD_CREATE_ROOM = commands["create-room"]



class MainServer(Base):
    def __init__(self):
        super().__init__()
        # List of sockets to poll for activity
        self.socketList = []

        # Dictionary of sockets -> usernames
        self.connectedUsers = {}

        # Dict of ChatRoom name -> ChatRoom objects
        self.openRooms = {}

        # Init server socket object for internet interface
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.SERVER_IP, self.SERVER_PORT))
        self.socketList.append(self.server)

        print("<SudoChat>")

        # Initialize the main chat room in parallel thread
        self.mainRoom = ChatRoom(self.SERVER_PORT + 1, "Group Chat")
        self.openRooms[self.mainRoom.NAME] = self.mainRoom
        t1 = threading.Thread(target=self.mainRoom.startChat)
        t1.start()

        # Listen for messages and connections
        self.server.listen()

        self.serverMain()

    
    def __del__(self):
        print("Main server thread closing...")
        self.server.close()

    
    def serverMain(self):
        while True:
            # OS level polling for activity on the listed sockets (listens for data packet on sockets)
            active_sockets, _, _ = select.select(self.socketList, [], self.socketList)

            for active_socket in active_sockets:
                if active_socket == self.server:
                    # accept connection from a client socket
                    client_socket, _ = self.server.accept()

                    # Call method to get username and store in clientDict
                    username = self.getData(client_socket)

                    if username is None:
                        continue

                    self.socketList.append(client_socket)
                    self.connectedUsers[client_socket] = username
                else:
                    # Parse commands from client socket
                    message = self.getData(active_socket)

                    # If no message, the client has disconnected
                    if not message or message == self.DISCON_MSG:
                        self.socketList.remove(active_socket)
                        continue
                    
                    if message == self.CMD_LIST_ROOMS:
                        self.listChatRooms(active_socket)
                    elif message == self.CMD_GET_ROOM:
                        self.sendPort(active_socket)
                    elif message == self.CMD_CREATE_ROOM:
                        self.openChatRoom(active_socket)


    def getData(self, client_socket) -> str:
        try:
            # Read header packet which gives length of payload
            msg_header = client_socket.recv(self.HEADER_BYTES)
            msg_len = int.from_bytes(msg_header, byteorder="big")
            
            # Read message payload from client
            payload = client_socket.recv(msg_len).decode("utf-8")

            return payload
        except:
            return None


    def sendData(self, dest_socket, message: str) -> None:
        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")
        data = message.encode("utf-8")

        dest_socket.send(header + data)


    # Client requests to see all the open chatrooms
    def listChatRooms(self, client_socket):
        try:
            self.sendData(client_socket, "ACK")

            # Send back number of chatrooms
            numRooms = len(self.openRooms)
            self.sendData(client_socket, str(numRooms))

            response = self.getData(client_socket)

            assert(response == "ACK")

            # Iterate through room names and send to client
            for roomName in self.openRooms.keys():
                self.sendData(client_socket, roomName)
        except:
            print("<Send chat room list failed>")


    # Client requests entry to room: get room name and send back port
    def sendPort(self, client_socket):
        try:
            self.sendData(client_socket, "ACK")

            roomName = self.getData(client_socket)

            # If room name found, send back the port
            if self.openRooms.get(roomName):
                self.sendData(client_socket, str(self.openRooms[roomName].PORT))
            else:
                self.sendData(client_socket, "NACK")
        except:
            print("<Send port to client failed>")


    def openChatRoom(self, client_socket):
        try:
            # Check if we have reached limit num of rooms
            if len(self.openRooms) < self.MAX_ROOMS:
                self.sendData(client_socket, "ACK")
            else:
                self.sendData(client_socket, "NACK")
                return

            name = self.getData(client_socket)

            # If name valid, start room in next port and send port num to client
            if name not in self.openRooms.keys():
                port = self.SERVER_PORT + len(self.openRooms) + 1

                chat = ChatRoom(port, name)
                t1 = threading.Thread(target=chat.startChat)

                # Append to list of chat rooms
                self.openRooms[name] = chat

                t1.start()            

                self.sendData(client_socket, str(port))
            else:
                self.sendData(client_socket, "NACK")
        except:
            pass



class ChatRoom(Base):
    def __init__(self, port: int, name: str):
        super().__init__()
        
        # List of client sockets connected to the chat room
        self.socketList = []

        # List of previous messages (limit of 10)
        self.msgCache = []

        # Dictionary of connected sockets -> usernames
        self.clientDict = {}

        # Initialize attributes
        self.PORT = port
        self.NAME = name

        # Init socket object for internet interface
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.SERVER_IP, self.PORT))

        # Add our server socket to the socket list
        self.socketList.append(self.server)

    
    def __del__(self):
        self.server.close()


    def startChat(self):
        print(f"<Welcome to the {self.NAME} Room!>")

        # Listen for messages and connections
        self.server.listen()

        self.chatMain()


    def chatMain(self):
        while True:
            # OS level polling for activity on the listed sockets (listens for data packet on sockets)
            active_sockets, _, _ = select.select(self.socketList, [], self.socketList)

            # Iterate over sockets where activity has been found
            for active_socket in active_sockets:

                # If activity on server socket, a new client is connecting
                if active_socket == self.server:
                    # accept connection from a client socket
                    client_socket, _ = self.server.accept()

                    # Call method to get username
                    username = self.getData(client_socket)

                    if username is None:
                        continue

                    # Welcome message for the new client
                    self.sendData(client_socket, f"<Welcome to the {self.NAME} Room!>")

                    # Send notif to new client of how many users in the chat
                    notif = self.chatUsersNotif()
                    self.sendData(client_socket, notif)

                    # Send previous 5 messages to new client
                    for msg in self.msgCache[-5:]:
                        self.sendData(client_socket, msg)

                    # Append to socket list and enter in clientDict
                    self.socketList.append(client_socket)
                    self.clientDict[client_socket] = username

                    # Broadcast notification to other clients in room
                    notif = f"<{username} has entered the chat! ({len(self.socketList) - 1} users online)>"

                    print(notif)
                    self.broadcast(client_socket, notif)

                # If activity is from a client socket, get data and broadcast to other clients
                else:
                    message = self.getData(active_socket)

                    # If no message, the client has disconnected
                    if not message or message == self.DISCON_MSG:
                        self.disconnectClient(active_socket)
                        continue

                    # Get username of the message sender
                    sender = self.clientDict[active_socket]

                    msg_prefix = f"<{sender}> "

                    # Data to send clients
                    print(msg_prefix + message)
                    msg_data = (msg_prefix + message)

                    # Store message in cache
                    if len(self.msgCache) >= 10:
                        self.msgCache.pop(0)
                    self.msgCache.append(msg_data)

                    # Broadcast message
                    self.broadcast(active_socket, msg_data)


    def getData(self, client_socket) -> str:
        try:
            # Read header packet which gives length of payload
            msg_header = client_socket.recv(self.HEADER_BYTES)
            msg_len = int.from_bytes(msg_header, byteorder="big")
            
            # Read message payload from client
            payload = client_socket.recv(msg_len).decode("utf-8")

            return payload
        except Exception as e:
            # Check if error resulted from disconnection:
            if "10054" in str(e):
                self.disconnectClient(client_socket)
            else:
                print("Data receive failed: " + str(e))
            
            return None

    
    def sendData(self, dest_socket, message: str) -> None:
        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")
        data = message.encode('utf-8')

        dest_socket.send(header + data)


    def broadcast(self, sender_socket, message: str) -> None:
        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")
        data = message.encode('utf-8')

        for sock in self.socketList:
            if sock != self.server and sock != sender_socket:
                sock.send(header + data)

    
    def disconnectClient(self, exit_socket) -> None:
        # If socket has already been removed then exit
        if exit_socket not in self.socketList:
            return

        self.socketList.remove(exit_socket)
        user = self.clientDict[exit_socket]
        del self.clientDict[exit_socket]

        notif = f"<{user} has disconnected ({len(self.socketList) - 1} users online)>"

        print(notif)
        self.broadcast(exit_socket, notif)

    
    def chatUsersNotif(self) -> str:
        numUsers = len(self.clientDict.values())
        users = [user for user in self.clientDict.values()]

        if numUsers == 0:
            return "<You are the only user in the room!>"
        elif numUsers == 1:
            return f"<{users[0]} is in the room!>"
        elif numUsers == 2:
            return f"<{users[0]} and {users[1]} are in the room!>"
        elif numUsers == 3:
            return f"<{users[0]}, {users[1]} and {users[2]} are in the room!>"
        else:
            return f"<{users[0]}, {users[1]} and {numUsers - 2} others are in the room!>"


# Starting the chat server
chat = MainServer()



