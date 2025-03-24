import socket
import sys
import time
from collections import OrderedDict
from utils import PacketHeader, compute_checksum

class RTPClient:
    def __init__(self, window_size=128):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.5)
        self.window_size = window_size
        self.seq_num = 0
        self.server_addr = None
        self.unacked = OrderedDict()
        self.chunk_size = 1472 - 16  # Max UDP payload
        self.buffer_size = 2048

    def connect(self, server_ip, server_port):
        """Establish RTP connection with START handshake"""
        self.server_addr = (server_ip, server_port)
        start_header = PacketHeader(
            type=0, seq_num=0, length=0, checksum=0
        )
        start_header.checksum = compute_checksum(bytes(start_header) + b'')

        while True:
            self.sock.sendto(bytes(start_header), self.server_addr)
            try:
                ack_data, _ = self.sock.recvfrom(self.buffer_size)
                ack_header = PacketHeader(ack_data[:16])
                if ack_header.type == 3 and ack_header.seq_num == 1:
                    if compute_checksum(ack_data[:16]) == ack_header.checksum:
                        self.seq_num = 1  # DATA starts at 1
                        return
            except socket.timeout:
                continue

    def send(self, data):
        """Reliably send data using sliding window"""
        chunks = [data[i:i+self.chunk_size] 
                 for i in range(0, len(data), self.chunk_size)]
        
        # Create all packets
        packets = {}
        for idx, chunk in enumerate(chunks):
            seq = idx + 1
            header = PacketHeader(
                type=2, seq_num=seq, length=len(chunk), checksum=0
            )
            header.checksum = compute_checksum(bytes(header) + chunk)
            packets[seq] = bytes(header) + chunk

        base = 1
        next_seq = 1
        total = len(chunks)

        while base <= total:
            # Send window
            while next_seq < base + self.window_size and next_seq <= total:
                if next_seq not in self.unacked:
                    self.sock.sendto(packets[next_seq], self.server_addr)
                    self.unacked[next_seq] = time.time()
                next_seq += 1

            # Wait for ACKs
            try:
                ack_data, _ = self.sock.recvfrom(self.buffer_size)
                ack_header = PacketHeader(ack_data[:16])
                if ack_header.type == 3 and ack_header.seq_num > base:
                    while base <= ack_header.seq_num - 1:
                        if base in self.unacked:
                            del self.unacked[base]
                        base += 1
            except (socket.timeout, ValueError):
                # Retransmit all unacked
                for seq in list(self.unacked.keys()):
                    if time.time() - self.unacked[seq] > 0.5:
                        self.sock.sendto(packets[seq], self.server_addr)
                        self.unacked[seq] = time.time()

    def close(self):
        """Terminate connection with END packet"""
        end_header = PacketHeader(
            type=1, seq_num=self.seq_num, length=0, checksum=0
        )
        end_header.checksum = compute_checksum(bytes(end_header))
        
        end_time = time.time() + 0.5
        while time.time() < end_time:
            self.sock.sendto(bytes(end_header), self.server_addr)
            try:
                ack_data, _ = self.sock.recvfrom(self.buffer_size)
                ack_header = PacketHeader(ack_data[:16])
                if ack_header.type == 3:
                    break
            except socket.timeout:
                continue
        self.sock.close()

if __name__ == "__main__":
    client = RTPClient(window_size=128)
    client.connect("localhost", 50000)
    data = sys.stdin.buffer.read()
    client.send(data)
    client.close()