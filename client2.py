import socket
import select
import errno
import sys
import random
import Crypto.Cipher.AES as AES
import pickle
import os

#fixed header length for error detection
HEADER_LENGTH = 10
#generating key  and counter for AES encryption 
key1=os.urandom(32)
counter1= os.urandom(16)

IP = "127.0.0.1"
PORT = 1235

my_username = "JONAH_smartfridge"

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to a given ip and port
client_socket.connect((IP, PORT))
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
ciphertext = AES.new(key1, AES.MODE_CTR,counter=lambda :counter1).encrypt(username)
d={1:key1, 2:counter1, 3:ciphertext, 4:username_header}
msg=pickle.dumps(d)

client_socket.send(msg)

# Wait for user to input a message
message ="\nUpdate number:"+str(random.randint(0,2000))+".\nRegarding:Usage pattern\nLearnt user most active - 40% during afternoon, 50% during dinner time, 10% late night past 12o'clock."
# Encode message to bytes, prepare header and convert to bytes, like for username above, then send


while True:
    print(f"Your username: {my_username}\n")
    ans= input(f'Start sending/receiving update to server(y/n) > ')
    print(f"Waiting for updates from other smart fridges.....\n")
    if ans == 'y' or ans == 'Y' :
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        #client_socket.send(message_header)
        ciphertext = AES.new(key1, AES.MODE_CTR,counter=lambda :counter1).encrypt(message)
        d={1:key1, 2:counter1, 3:ciphertext,4:message_header}
        msg=pickle.dumps(d)
        client_socket.send(msg)
       
    else:
         sys.exit()
    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:
            username_header = client_socket.recv(HEADER_LENGTH)
            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive and decode username
            username = client_socket.recv(username_length).decode('utf-8')

            # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            # Print message
            print(f'\n{username} > {message}\n')

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
        sys.exit()
