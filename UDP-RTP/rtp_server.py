import socket
import sys
from collections import defaultdict
from utils import PacketHeader, compute_checksum

class RTPServer:
    def __init__(self, window_size=128):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.5)
        self.window_size = window_size
        self.expected_seq = 0
        self.buffer = defaultdict(bytes)
        self.active_client = None
        self.buffer_size = 2048

    def bind(self, ip, port):
        self.sock.bind((ip, port))

    def accept(self):
        """Wait for START packet from client"""
        while True:
            try:
                pkt, addr = self.sock.recvfrom(self.buffer_size)
                header = PacketHeader(pkt[:16])
                if header.type == 0 and header.seq_num == 0:
                    ack_header = PacketHeader(
                        type=3, seq_num=1, length=0, checksum=0
                    )
                    ack_header.checksum = compute_checksum(bytes(ack_header))
                    self.sock.sendto(bytes(ack_header), addr)
                    self.active_client = addr
                    self.expected_seq = 1
                    return addr
            except socket.timeout:
                continue

    def recv(self):
        """Receive data from client with reliability"""
        data = bytearray()
        while True:
            try:
                pkt, addr = self.sock.recvfrom(self.buffer_size)
                if addr != self.active_client:
                    continue

                header = PacketHeader(pkt[:16])
                payload = pkt[16:16+header.length]

                # Verify checksum
                saved_checksum = header.checksum
                header.checksum = 0
                if compute_checksum(bytes(header) + payload) != saved_checksum:
                    continue

                # Handle END
                if header.type == 1:
                    ack_header = PacketHeader(
                        type=3, seq_num=header.seq_num + 1, checksum=0
                    )
                    ack_header.checksum = compute_checksum(bytes(ack_header))
                    self.sock.sendto(bytes(ack_header), addr)
                    return data

                # Store data and send ACK
                if header.seq_num >= self.expected_seq:
                    self.buffer[header.seq_num] = payload
                    ack_header = PacketHeader(
                        type=3, seq_num=self.expected_seq, checksum=0
                    )
                    ack_header.checksum = compute_checksum(bytes(ack_header))
                    self.sock.sendto(bytes(ack_header), addr)

                # Deliver in-order data
                while self.expected_seq in self.buffer:
                    data.extend(self.buffer[self.expected_seq])
                    del self.buffer[self.expected_seq]
                    self.expected_seq += 1

            except socket.timeout:
                continue

    def close(self):
        self.sock.close()

if __name__ == "__main__":
    server = RTPServer(window_size=128)
    server.bind("localhost", 40000)
    print("Server listening...")
    client_addr = server.accept()
    print(f"Connected to {client_addr}")
    received_data = server.recv()
    sys.stdout.buffer.write(received_data)
    server.close()