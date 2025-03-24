from socket import *

serverPort = 12000

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', 12000))  # Listens on all interfaces (default behavior)
# serverSocket.bind(('localhost', 12000))  # Restricts to localhost only

print("The server is ready to receive")

while True:
    message, clientAddress = serverSocket.recvfrom(2048)
    modifiedMessage = message.decode().upper().encode()
    serverSocket.sendto(modifiedMessage, clientAddress)