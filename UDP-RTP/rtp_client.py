from rtp_socket import RTPSenderSocket, RTPReceiverSocket
import socket
import sys

serverName = 'localhost'
serverPort = 40000  # Corrected port

# Send request using sender socket
client_sender = RTPSenderSocket()
client_sender.connect(serverName, serverPort)

# message = input('Input lowercase sentence: ')
message = sys.stdin.buffer.read()
client_sender.send(message)

# Get the sender's port before closing
sender_port = client_sender.sock.getsockname()[1]  # Uncommented line
client_sender.close()

# Listen for response using receiver socket on the sender's port
client_receiver = RTPReceiverSocket()
client_receiver.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
client_receiver.bind('', sender_port)  # Use sender_port, not serverPort

modifiedMessage, serverAddress = client_receiver.recv()
print(f'From {serverAddress}: {modifiedMessage.decode()}')
client_receiver.close()