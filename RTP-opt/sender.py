import argparse
import socket
import sys
import time

from utils import PacketHeader, compute_checksum

chunk_size = 1472 - 16 # 1472 is the maximum size of a packet
buffer_size = 2048

def verify_checksum(header):
    """Verify packet checksum"""
    saved_checksum = header.checksum
    header.checksum = 0
    return compute_checksum(header) == saved_checksum

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
    start_header.checksum = compute_checksum(bytes(start_header) + b'')
    
    # Send START until ACK is received
    while True:
        print("Sending START")
        s.sendto(bytes(start_header), (receiver_ip, receiver_port))
        try:
            print("Waiting for ACK at start")
            ack_data, _ = s.recvfrom(buffer_size)
            ack_header = PacketHeader(ack_data[:16])
            if(ack_header.type == 3 and #ACK type
                ack_header.seq_num == 1):
                    if(verify_checksum(ack_header)):
                        break
                    else:
                        print("Invalid checksum for start ACK")
        except (socket.timeout, ValueError):
            print("Timeout when waiting for ACK")
            continue
    
    print("Connection established")
    # Data transmission
    data = sys.stdin.buffer.read()
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    n_packets = len(chunks)
    
    # Create a packet dictionary to store all packets
    packet_dict = {}
    for i in range(n_packets):
        seq_num = i + 1
        chunk = chunks[i]
        header = PacketHeader(
            type=2, # Data type
            seq_num=seq_num,
            length=len(chunk),
            checksum=0
        )
        header.checksum = compute_checksum(bytes(header) + chunk)
        packet_dict[seq_num] = bytes(header) + chunk
    
    # Sliding window mechanism implementation
    start = 1 # First data packet seq_num
    
    print(f"Sending {n_packets} packets")
    
    received = set()
    while start <= n_packets:
        end = start + window_size
        if end > n_packets:
            end = n_packets
        for seq_num in range(start, end + 1):
            if seq_num not in received:
                s.sendto(packet_dict[seq_num], (receiver_ip, receiver_port))
                print(f"Sending packet {seq_num} with {start}")
        # Wait for ACKs
        try:
            ack_data, _ = s.recvfrom(buffer_size)
            ack_header = PacketHeader(ack_data[:16])
            
            if ack_header.type == 3 and verify_checksum(ack_header):
                # Move window
                print(f"Received ACK for packet {ack_header.seq_num}")
                received_seq_num = ack_header.seq_num
                
                if start <= received_seq_num:
                    received.add(received_seq_num)
                    # Remove all acknowledged packets
                    while start in received:
                        start += 1
        except (socket.timeout,ValueError):
            # retransmit packets
            pass
        
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
            print("Waiting for END ACK")
            ack_data, _ = s.recvfrom(buffer_size)
            ack_header = PacketHeader(ack_data[:16])
            if (ack_header.type == 3 
                and ack_header.seq_num == end_seq_num  + 1
                and verify_checksum(ack_header)):
                print("Connection closed")
                break
        except (socket.timeout, ValueError):
            pass


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
