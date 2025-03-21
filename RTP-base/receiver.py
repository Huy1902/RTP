import argparse
import socket
from collections import defaultdict
import sys

from utils import PacketHeader, compute_checksum

buffer_size = 2048
no_port = -1000

def verify_checksum(header, payload):
    """Verify packet checksum"""
    saved_checksum = header.checksum
    header.checksum = 0
    calculated = compute_checksum(bytes(header) + payload)
    # print(f"Calculated checksum: {calculated} with saved checksum: {saved_checksum}")
    header.checksum = saved_checksum
    return calculated == saved_checksum

    

def receiver(receiver_ip, receiver_port, window_size):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.5)
    s.bind((receiver_ip, receiver_port))
    
    expected_seq_num = 0
    data_buffer = defaultdict(bytes) # Avoid key error
    received_data = bytearray()
    connection_established = no_port # Ensure only one sender can connect
    
    # Support function to send ACK
    def send_ack(ack_seq_num, address):
        ack_header = PacketHeader(
            type=3,
            seq_num=ack_seq_num,
            length=0,
            checksum=0
        )
        ack_header.checksum = compute_checksum(ack_header)
        s.sendto(bytes(ack_header), address)
    
    # print("Receiver is listening")
    
    while True:
        # print("Waiting for package")
        try:
            package, address = s.recvfrom(buffer_size)
        except socket.timeout:
            # print("Timeout when waiting package")
            continue
        
        # print("Received package")
        # Check valid package
        if (len(package) < 16):
            # print("Invalid length packet")
            continue
        
        try:
            header = PacketHeader(package[:16])
        except: # Wrong format
            # print("Wrong format packet")
            continue
        
        # Ensure payload only contains data
        # print(f"Received package type: {header.type} Reading payload")
        payload = package[16:16+header.length]
        
        # Drop package if checksum is invalid
        if not verify_checksum(header, payload):
            # print(f"Invalid checksum: {header.checksum} with {header.seq_num}")
            if connection_established == address:
                send_ack(expected_seq_num, address)
            continue
        
        # print("Valid package")
        
        # Start handshake
        if header.type == 0 and not connection_established == address:
            # print("Start handshake")
            if header.seq_num == 0:
                send_ack(1, address)
                connection_established = address
                expected_seq_num = 1
            continue
        
        if header.type == 0 and connection_established == address:
            if header.seq_num == 0: # Resend ACK
                # print("Resend start ACK")
                send_ack(1, address)
                continue
    
        # Data transmission
        if header.type == 2 and connection_established == address:
            seq_num = header.seq_num
            # print(f"Data transmission with seq_num: {seq_num}")
            
            if seq_num < expected_seq_num:
                send_ack(expected_seq_num, address)
            elif seq_num < expected_seq_num + window_size:
                if seq_num not in data_buffer:
                    data_buffer[seq_num] = payload
                
                # In order delivery
                while expected_seq_num in data_buffer:
                    received_data.extend(data_buffer[expected_seq_num])
                    del data_buffer[expected_seq_num]
                    expected_seq_num += 1
            # Drop out of window packets seq_num >= expected_seq_num + window_size case
            
                send_ack(expected_seq_num, address)
            
        # End handshake
        if header.type == 1 and connection_established:
            if header.seq_num == expected_seq_num:
                send_ack(expected_seq_num + 1, address)
                sys.stdout.buffer.write(received_data)
                sys.stdout.buffer.flush()
                break
            
    s.close()
    # while True:
    #     # Receive packet; address includes both IP and port


    #     # Extract header and payload
    #     pkt_header = PacketHeader(pkt[:16])
    #     msg = pkt[16 : 16 + pkt_header.length]

    #     # Verity checksum
    #     pkt_checksum = pkt_header.checksum
    #     pkt_header.checksum = 0
    #     computed_checksum = compute_checksum(pkt_header / msg)
    #     if pkt_checksum != computed_checksum:
    #         print("checksums not match")
    #     print(msg)


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
