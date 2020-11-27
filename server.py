import socket
import threading
import select
import json


class ChatServer:
    def __init__(self):

        self.chatRooms = []
        self.socketList = []

        # Read configuration data from config file
        with open("config.json") as json_config:
            config = json.load(json_config)

        # Config constands
        self.SERVER_IP = config["server-ip"]
        self.SERVER_PORT = config["server-port"]
        self.HEADER_BYTES = config["header-bytes"]
        self.DISCON_MSG = config["disconnect-msg"]
        self.MAX_ROOMS =  config["max-chat-rooms"]

        # Commands sent from client to server
        self.commands = [
            "LIST_CHATROOMS",
            "OPEN_CHATROOM",
            "ENTER_CHATROOM"
        ]

        # Init server socket object for internet interface
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.SERVER_IP, self.SERVER_PORT))

        # Add our server socket to the socket list
        self.socketList.append(self.server)
        print("<SudoChat>")

        # Initialize the main chat room
        self.mainRoom = ChatRoom(self.SERVER_PORT + 1, "Group Chat")

        # Listen for messages and connections
        self.server.listen()


    def __del__(self):
        for room in self.chatRooms:
            del room
        
        print()


    def openChatRoom(self, initial_user):
        pass


    def closeChatRoom(self):
        pass



class ChatRoom:
    def __init__(self, port: int, name: str):
        self.socketList = []
        self.clientDict = {}

        # Read configuration data from config file
        with open("config.json") as json_config:
            config = json.load(json_config)

        self.SERVER_IP = config["server-ip"]
        self.HEADER_BYTES = config["header-bytes"]
        self.DISCON_MSG = config["disconnect-msg"]
        self.PORT = port
        self.NAME = name

        # Init socket object for internet interface
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.SERVER_IP, self.PORT))

        # Add our server socket to the socket list
        self.socketList.append(self.server)

        print(f"\n<Welcome to the {self.NAME} Room!>")

        # Listen for messages and connections
        self.server.listen()

        self.serverMain()

    
    def __del__(self):
        self.server.close()


    def serverMain(self):
        while True:
            # OS level polling for activity on the listed sockets (listens for data packet on sockets)
            active_sockets, _, _ = select.select(self.socketList, [], self.socketList)

            # Iterate over sockets where activity has been found
            for active_socket in active_sockets:

                # If activity on server socket, a new client is connecting
                if active_socket == self.server:
                    # accept connection from a client socket
                    client_socket, _ = self.server.accept()

                    # Call method to get username and store in clientDict
                    username = self.getData(client_socket)

                    if username is None:
                        continue

                    # Append to socket list and enter in clientDict
                    self.socketList.append(client_socket)
                    self.clientDict[client_socket] = username

                    # Welcome message for the new client
                    self.sendData(client_socket, f"<Welcome to the {self.NAME} Room!>")

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

    
    def sendData(self, dest_socket, message: str):
        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")
        data = message.encode('utf-8')

        dest_socket.send(header + data)


    def broadcast(self, sender_socket, message: str):
        header = len(message).to_bytes(self.HEADER_BYTES, byteorder="big")
        data = message.encode('utf-8')

        for sock in self.socketList:
            if sock != self.server and sock != sender_socket:
                sock.send(header + data)

    
    def disconnectClient(self, exit_socket):
        # If socket has already been removed then exit
        if exit_socket not in self.socketList:
            return

        self.socketList.remove(exit_socket)
        user = self.clientDict[exit_socket]
        del self.clientDict[exit_socket]

        notif = f"<{user} has disconnected ({len(self.socketList) - 1} users online)>"

        print(notif)
        self.broadcast(exit_socket, notif)


chat = ChatServer()