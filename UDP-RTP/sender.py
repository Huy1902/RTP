from rtp_socket import RTPSenderSocket
import sys
import argparse

def sender(receiver_ip, receiver_port, window_size):
    rtp_socket = RTPSenderSocket(window_size)
    rtp_socket.connect(receiver_ip, receiver_port)
    
    data = sys.stdin.buffer.read()
    rtp_socket.send(data)
    
    rtp_socket.close()
    
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
