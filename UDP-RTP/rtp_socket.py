import socket
from utils import PacketHeader, compute_checksum
import time
from collections import defaultdict


class RTPSenderSocket:
    def __init__(self, window_size=128):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.sock.settimeout(0.5)
        self.window_size = window_size
        self.seq_num = 0
        self.receiver_addr = None
        self.buffer_size = 2048
        self.chunk_size = 1472 - 16  # 1472 is the maximum size of a packet
        self.n_packets = None
    
    def verify_checksum(self, header):
        """Verify packet checksum"""
        saved_checksum = header.checksum
        header.checksum = 0
        return compute_checksum(header) == saved_checksum

    def connect(self, receiver_ip, receiver_port):
        """Initiate connection with START packet."""
        self.receiver_addr = (receiver_ip, receiver_port)
        # Send START packet and wait for ACK (existing logic from sender.py)
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
            self.sock.sendto(bytes(start_header), (receiver_ip, receiver_port))
            try:
                print("Waiting for ACK at start")
                ack_data, _ = self.sock.recvfrom(self.buffer_size)
                ack_header = PacketHeader(ack_data[:16])
                if (ack_header.type == 3 and  # ACK type
                        ack_header.seq_num == 1):
                    if (self.verify_checksum(ack_header)):
                        break
                    else:
                        print("Invalid checksum for start ACK")
            except (socket.timeout, ValueError):
                print("Timeout when waiting for ACK")
                continue
        print("Connection established")

    def send(self, data):
        """Reliably send data using sliding window."""
        # Split data into chunks, add RTP headers, manage window and retransmissions
        # (Adapt logic from sender.py's data transmission phase)
        chunks = [data[i:i+self.chunk_size]
                  for i in range(0, len(data), self.chunk_size)]
        self.n_packets = len(chunks)

        # Create a packet dictionary to store all packets
        packet_dict = {}
        for i in range(self.n_packets):
            seq_num = i + 1
            chunk = chunks[i]
            header = PacketHeader(
                type=2,  # Data type
                seq_num=seq_num,
                length=len(chunk),
                checksum=0
            )
            header.checksum = compute_checksum(bytes(header) + chunk)
            packet_dict[seq_num] = bytes(header) + chunk

        # Sliding window mechanism implementation
        start = 1  # First data packet seq_num

        print(f"Sending {self.n_packets} packets")

        received = set()
        while start <= self.n_packets:
            end = start + self.window_size
            if end > self.n_packets:
                end = self.n_packets
            for seq_num in range(start, end + 1):
                if seq_num not in received:
                    self.sock.sendto(packet_dict[seq_num], self.receiver_addr)
                    print(f"Sending packet {seq_num} with {start}")
            # Wait for ACKs
            try:
                ack_data, _ = self.sock.recvfrom(self.buffer_size)
                ack_header = PacketHeader(ack_data[:16])

                if ack_header.type == 3 and self.verify_checksum(ack_header):
                    # Move window
                    print(f"Received ACK for packet {ack_header.seq_num}")
                    received_seq_num = ack_header.seq_num

                    if start <= received_seq_num:
                        received.add(received_seq_num)
                        # Remove all acknowledged packets
                        while start in received:
                            start += 1
            except (socket.timeout, ValueError):
                # retransmit packets
                pass
        

    def close(self):
        """Terminate connection with END packet."""
        # Send END packet and handle ACK/timeout (existing logic from sender.py)
        # END handshake
        end_seq_num = self.n_packets + 1
        end_header = PacketHeader(
            type=1,  # END type
            seq_num=end_seq_num,
            length=0,
            checksum=0
        )
        end_header.checksum = compute_checksum(end_header)

        end_time = time.time() + 0.5
        while time.time() < end_time:
            self.sock.sendto(bytes(end_header), self.receiver_addr)
            try:
                print("Waiting for END ACK")
                ack_data, _ = self.sock.recvfrom(self.buffer_size)
                ack_header = PacketHeader(ack_data[:16])
                if (ack_header.type == 3
                    and ack_header.seq_num == end_seq_num + 1
                        and self.verify_checksum(ack_header)):
                    print("Connection closed")
                    break
            except (socket.timeout, ValueError):
                pass
        self.sock.close()


class RTPReceiverSocket:
    def __init__(self, window_size=128):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.sock.settimeout(0.5)
        self.window_size = window_size
        self.buffer_size = 2048

    # Support function to send ACK
    def send_ack(self, ack_seq_num, address):
        ack_header = PacketHeader(
            type=3,
            seq_num=ack_seq_num,
            length=0,
            checksum=0
        )
        ack_header.checksum = compute_checksum(ack_header)
        self.sock.sendto(bytes(ack_header), address)

    def verify_checksum(self, header, payload):
        """Verify packet checksum"""
        saved_checksum = header.checksum
        header.checksum = 0
        calculated = compute_checksum(bytes(header) + payload)
        # print(f"Calculated checksum: {calculated} with saved checksum: {saved_checksum}")
        header.checksum = saved_checksum
        return calculated == saved_checksum

    def bind(self, ip, port):
        self.sock.bind((ip, port))

    def recv(self):
        """Return in-order data and send ACKs."""
        # Process packets, buffer out-of-order, send ACKs (logic from receiver.py)
        # ...
        # print("Receiver is listening")
        start_seq_num = 0
        data_buffer = defaultdict(bytes)
        received_data = bytearray()
        connection_established = -1000  # Ensure only one sender can connect

        while True:
            # print("Waiting for package")
            try:
                package, address = self.sock.recvfrom(self.buffer_size)
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
            except ValueError:  
                # Wrong format
                # print("Wrong format packet")
                continue

            # Ensure payload only contains data
            # print(f"Received package type: {header.type} Reading payload")
            payload = package[16:16+header.length]

            # Drop package if checksum is invalid
            if not self.verify_checksum(header, payload):
                # print(f"Invalid checksum: {header.checksum} with {header.seq_num}")
                if connection_established == address:
                    self.send_ack(start_seq_num, address)
                continue

            # print("Valid package")

            # Start handshake
            if header.type == 0 and not connection_established == address:
                # print("Start handshake")
                if header.seq_num == 0:
                    self.send_ack(1, address)
                    connection_established = address
                    start_seq_num = 1
                continue

            if header.type == 0 and connection_established == address:
                if header.seq_num == 0:  # Resend ACK
                    # print("Resend start ACK")
                    self.send_ack(1, address)
                    continue

            # Data transmission
            if header.type == 2 and connection_established == address:
                seq_num = header.seq_num
                # print(f"Data transmission with seq_num: {seq_num} with {start_seq_num}")

                if seq_num < start_seq_num + self.window_size:
                    self.send_ack(seq_num, address)
                    if seq_num >= start_seq_num:
                        if seq_num not in data_buffer:
                            data_buffer[seq_num] = payload

                        # In order delivery
                        while start_seq_num in data_buffer:
                            # print(f"Received packet {start_seq_num}")
                            received_data.extend(data_buffer[start_seq_num])
                            del data_buffer[start_seq_num]
                            start_seq_num += 1
                # Drop out of window packets seq_num >= start_seq_num + window_size case
            # End handshake
            if header.type == 1 and connection_established == address:
                # print("End handshake")
                # print(f"Header seq_num: {header.seq_num} with {start_seq_num}")
                if header.seq_num == start_seq_num:
                    self.send_ack(start_seq_num + 1, address)
                    break
        return received_data, address        
        

    def close(self):
        self.sock.close()
