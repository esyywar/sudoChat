import socket
import threading
import select
import json

class ChatRoom:
    def __init__(self):
        self.socketList = []
        self.clientDict = {}

        # Read configuration data from config file
        with open("config.json") as json_config:
            config = json.load(json_config)

        self.SERVER_IP = config["server-ip"]
        self.SERVER_PORT = config["server-port"]
        self.HEADER_BYTES = config["header-bytes"]

        # Init socket object for internet interface
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server.bind((self.SERVER_IP, self.SERVER_PORT))

        # Add our server socket to the socket list
        self.socketList.append(self.server)

        print("< Welcome to the Chat Room! >")

        # Listen for messages and connections
        self.server.listen()

        t1 = threading.Thread(target=self.acceptConnections, args=(), daemon=True)
        t1.start()

    def acceptConnections(self):
        print("< ChatRoom is now accepting connections! >")

        while True:
            # I/O level polling for activity on the listed sockets (listens for data packet on sockets)
            active_sockets, _, _ = select.select(self.socketList, [], self.socketList)

            # Iterate over sockets where activity has been found
            for active_socket in active_sockets:

                # If activity on server socket, we handle a new client is connecting
                if active_socket == self.server:
                    # accept connection from a client socket and append to chat room list
                    client_socket, _ = self.server.accept()
                    self.socketList.append(client_socket)

                    # Call method to get username and store in clientDict
                    username = self.getData(client_socket)
                    self.clientDict[client_socket] = username

                    print(f"< {username} has entered the chat!")

                # If activity is from a client socket
                else:
                    pass


    def getData(self, client_socket) -> str:
        try:
            # Read header packet which gives length of payload
            msg_header = client_socket.recv(self.HEADER_BYTES)
            msg_len = int.from_bytes(msg_header, byteorder="big")
            
            # Read message payload from client
            payload = client_socket.recv(msg_len).decode('utf-8')

            return payload
        except Exception as e:
            print("Data receive failed: " + str(e))

            return None

    def relayMessage(self, message: str, senderSocket):
        pass

    def closeChat(self):
        pass



chat = ChatRoom()
input()