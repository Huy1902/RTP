import binascii

from scapy.all import Packet, IntField


class PacketHeader(Packet):
    """
    Packet header class.
    16 bytes for 4 integers fields.
    """
    name = "PacketHeader"
    fields_desc = [
        IntField("type", 0),
        IntField("seq_num", 0),
        IntField("length", 0),
        IntField("checksum", 0),
    ]


def compute_checksum(pkt):
    '''
    Compute the checksum of the packet (ensure it always is a 32-bit
    unsigned integer).
    
    Used to detect errors in transmitted packets.
    '''
    return binascii.crc32(bytes(pkt)) & 0xFFFFFFFF