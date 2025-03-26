from socket import *

serverName = 'localhost'  # Replace with server's IP or hostname
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_DGRAM)

message = input('Input lowercase sentence: ')
clientSocket.sendto(message.encode(), (serverName, serverPort))

modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
print(f'From Server: {modifiedMessage.decode()}')

clientSocket.close()