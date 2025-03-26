from rtp_socket import RTPReceiverSocket, RTPSenderSocket

serverPort = 40000

serverSocketRecv = RTPReceiverSocket()
serverSocketRecv.bind('', serverPort)  # Bind once here (outside the loop)

print("The server is ready to receive")

while True:
    message, clientAddress = serverSocketRecv.recv()  # No bind() here
    modifiedMessage = message.decode().upper().encode()
    
    # Create a new sender socket per request
    serverSocketSender = RTPSenderSocket()
    serverSocketSender.connect(clientAddress[0], clientAddress[1])
    serverSocketSender.send(modifiedMessage)
    serverSocketSender.close()