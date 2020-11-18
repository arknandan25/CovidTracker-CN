import socket
import select
import errno
import sys
import random
import Crypto.Cipher.AES as AES
import pickle
import os


HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1235

# Create a socket,socket.SOCK_STREAM - TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
server_socket.bind((IP, PORT))
server_socket.listen()
# List of sockets for select.select() for handling multiple connections simultaneoulsy
sockets_list = [server_socket]
# List of connected clients - socket as a key, user header and name as data
clients = {}
print(f'Listening for connections on {IP}:{PORT}...')

# Handles message receiving
def receive_message(client_socket):

    try:
        msg = client_socket.recv(1028)
        x=pickle.loads(msg)
        decrypto = AES.new(x[1], AES.MODE_CTR, counter=lambda: x[2])
        msg1 = decrypto.decrypt(x[3])
        message_header=x[4]
        message_length = int(message_header.decode('utf-8').strip())
        return {'header':message_header,'len':message_length,'encrypted_data':x[3],'data': msg1}

    except:
        print("The connection was closed abruptly by the client!")
        return False

while True:
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    # Iterate over notified sockets searching for new connections
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            # Accept new connection
            # That gives us new socket - client socket, connected to this given client only, it's unique for that client     
            client_socket, client_address = server_socket.accept()

            # Client should send his name right away, receive it
            user = receive_message(client_socket)
            # If False - client disconnected before he sent his name
            if user is False:
                continue
            # Add accepted socket to select.select() list
            sockets_list.append(client_socket)
            # Also save username and username header
            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

        # Else existing socket is sending a message
        else:

            # Receive update here
            message = receive_message(notified_socket)

            # If False, client disconnected, delete the client from list
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            print(f'Received message from {user["data"].decode("utf-8")}:\n Encrypted message:\n{message["encrypted_data"]}\n\nDecrypted message:{message["data"].decode("utf-8")}\n')

            # Iterate over connected clients and broadcast message
            for client_socket in clients:

                # But don't sent it to sender
                if client_socket != notified_socket:
                    client_socket.send( user['header']+user['data'] +message['header']+ message['data'])

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
        
