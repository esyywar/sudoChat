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

        # Enter main loop for chat room with daemon thread
        #main = threading.Thread(target=self.serverMain, daemon=True)
        #main.start()

        self.serverMain()


    def serverMain(self):
        print("< ChatRoom is now accepting connections! >")

        while True:
            # I/O level polling for activity on the listed sockets (listens for data packet on sockets)
            active_sockets, _, _ = select.select(self.socketList, [], self.socketList)

            # Iterate over sockets where activity has been found
            for active_socket in active_sockets:

                # If activity on server socket, we handle a new client is connecting
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

                    print(f"< {username} has entered the chat! ({len(self.socketList) - 1} users online)>")

                # If activity is from a client socket
                else:
                    message = self.getData(active_socket)

                    # If no message, the client has disconnected
                    if not message:
                        continue

                    # Get username of the message sender
                    sender = self.clientDict[active_socket]

                    msg_prefix = f"<{sender}> "

                    print(msg_prefix + message)

                    # Header and data to send clients
                    msg_header = (len(msg_prefix) + len(message)).to_bytes(self.HEADER_BYTES, byteorder="big")
                    msg_data = (msg_prefix + message).encode("utf-8")

                    # Relay the message to all client sockets except the sender and server
                    for client in self.socketList:
                        if client != active_socket and client != self.server:
                            print("sending data th another guy...")
                            self.server.send(msg_header + msg_data)


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
                self.socketList.remove(client_socket)
                user = self.clientDict[client_socket]
                del self.clientDict[client_socket]

                print(f"< {user} has disconnected ({len(self.socketList) - 1} users online)>")
            else:
                print("Data receive failed: " + str(e))
            
            return None


    def closeChat(self):
        self.server.close()


chat = ChatRoom()