from rtp_socket import RTPReceiverSocket
import sys
import argparse

def receiver(receiver_ip, receiver_port, window_size):
    rtp_socket = RTPReceiverSocket(window_size)
    rtp_socket.bind(receiver_ip, receiver_port)
    
    
    data = rtp_socket.recv()
    if data:
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
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

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
