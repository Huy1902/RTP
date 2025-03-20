import argparse
import socket
import sys
import time
from collections import OrderedDict

from utils import PacketHeader, compute_checksum

buffer_size = 1472

def verify_checksum(header, payload):
    """Verify packet checksum"""
    saved_checksum = header.checksum
    header.checksum = 0
    calculated = compute_checksum(bytes(header) + payload)
    header.checksum = saved_checksum
    return calculated == saved_checksum

def sender(receiver_ip, receiver_port, window_size):
    """
    
    """
    """TODO: Open socket and send message from sys.stdin."""
    # Create a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.5)
    
    # Handshake with START packet
    start_header = PacketHeader(
        type=0,
        seq_num=0,
        length=0,
        checksum=0
    )
    start_header.checksum = compute_checksum(start_header)
    
    # Send START until ACK is received
    while True:
        s.sendto(bytes(start_header), (receiver_ip, receiver_port))
        try:
            ack_data, _ = s.recvfrom(buffer_size)
            ack_header = PacketHeader.from_bytes(ack_data[:16])
            if(ack_header.type == 3 and #ACK type
                ack_header.seq_num == 1 
                and verify_checksum(ack_header, b'')):
                break
        except (socket.timeout, ValueError):
            continue
        
    # Data transmission
    data = sys.stdin.buffer.read()
    chunks = [data[i:i+buffer_size] for i in range(0, len(data), buffer_size)]
    n_packets = len(chunks)
    
    # Sliding window mechanism implementation
    start = 1 # First data packet seq_num
    next_seq_num = 1
    packets = OrderedDict()
    
    print(f"Sending {n_packets} packets")
    
    while start <= n_packets:
        
        while next_seq_num < start + window_size and next_seq_num <= n_packets:
            # chunks start from 0
            chunk = chunks[next_seq_num-1]
            header = PacketHeader(
                type=2, # Data type
                seq_num=next_seq_num,
                length=len(chunk),
                checksum=0
            )
            # Compute checksum like tutorial
            packet = bytes(header) + chunk
            header.checksum = compute_checksum(packet)
            
            s.sendto(packet, (receiver_ip, receiver_port))
            
            # Store packet in order to resend if necessary, get time.time() to 
            # have different values for each packet
            packets[next_seq_num] = (packet, time.time())
            next_seq_num += 1
            
        # Wait for ACKs
        try:
            print("Waiting for ACKs")
            ack_data, _ = s.recvfrom(buffer_size)
            ack_header = PacketHeader.from_bytes(ack_data[:16])
            
            if ack_header.type == 3 and verify_checksum(ack_header):
                # Move window
                new_seq_num = ack_header.seq_num
                if new_seq_num > start:
                    # Remove all acknowledged packets
                    while start < new_seq_num:
                        if start in packets:
                            del packets[start]
                        start += 1
        except (socket.timeout,ValueError):
            # If timeout occurs, resend all packets in window
            for seq in range(start, min(start + window_size, next_seq_num)):
                if seq in packets:
                    packet, _ = packets[seq]
                    s.sendto(packet, (receiver_ip, receiver_port))
        
    # END handshake
    end_seq_num = n_packets + 1
    end_header = PacketHeader(
        type=1, # END type
        seq_num=end_seq_num,
        length=0,
        checksum=0
    )
    end_header.checksum = compute_checksum(end_header)
    
    end_time = time.time() + 0.5
    while time.time() < end_time:
        s.sendto(bytes(end_header), (receiver_ip, receiver_port))
        try:
            ack_data, _ = s.recvfrom(buffer_size)
            ack_header = PacketHeader.from_bytes(ack_data[:16])
            if (ack_header.type == 3 
                and ack_header.seq_num == end_seq_num  + 1
                and verify_checksum(ack_header)):
                break
        except (s.timeout, ValueError):
            continue
    
    # pkt_header = PacketHeader(type=2, seq_num=10, length=14)
    # pkt_header.checksum = compute_checksum(pkt_header / "Hello, world!\n")
    # pkt = pkt_header / "Hello, world!\n"
    # s.sendto(bytes(pkt), (receiver_ip, receiver_port))


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
