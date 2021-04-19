import socket
import select
import hashlib
import time
from threading import Thread, Timer

class RUDP:

    WINDOW_SIZE = 1024
    TIMEOUT = 0.5

    # packet constants
    SEQNUM_SIZE = 8
    LENGTH_SIZE = 2
    CHECKSUM_SIZE = 16
    __checksum_start__ = SEQNUM_SIZE + LENGTH_SIZE
    __checksum_end__ = __checksum_start__ + CHECKSUM_SIZE
    MAX_IP_SIZE = 65535
    MAX_DATA_SIZE = 65481

    # constructor for RUDP object
    def __init__(self, address, port):
        self.__sock__ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__send_buffer__ = {}
        self.__recv_buffer__ = {}
        self.__address__ = address
        self.__port__ = port
        self.__acked_packets__ = set()
        self.__timers__ = {}
        self.__send_start__ = 0
        self.__recv_start__ = 0
        self.__seqnum_send__ = 0
        self.__running__ = True
        self.listen_thread = Thread(target=self.listenRUDP, name="listen_thread")
        self.listen_thread.start()


    def send_ack(self, seq_num, address):
        print(f"Sending ack for Seq Num: {seq_num}")
        self.__sock__.sendto(self.create_packet(seq_num, b""), address)
        

    def create_packet(self, seq_num, data):
        length = len(data)
        if length > self.MAX_DATA_SIZE:
            print(f'Length: {length}')
            raise ValueError('Data too long')
            
        pkt = bytearray()
        pkt += seq_num.to_bytes(self.SEQNUM_SIZE, 'big')
        pkt += length.to_bytes(self.LENGTH_SIZE, 'big')
        pkt += bytearray(self.CHECKSUM_SIZE)
        pkt += data

        pkt[self.__checksum_start__:self.__checksum_end__] = hashlib.md5(pkt).digest()
        return bytes(pkt)


    def get_packet_info(self, packet):
        packet = bytearray(packet)
        
        checksum = packet[self.__checksum_start__ : self.__checksum_end__]
        packet[self.__checksum_start__ : self.__checksum_end__] = bytearray(self.CHECKSUM_SIZE)
        assert hashlib.md5(packet).digest() == checksum, "Corrupted Packet: Different Checksum"

        seq_num = int.from_bytes(packet[ : self.SEQNUM_SIZE], "big")
        packet_length = int.from_bytes(
            packet[self.SEQNUM_SIZE : self.SEQNUM_SIZE + self.LENGTH_SIZE], "big"
        )
        data = bytes(packet[self.__checksum_end__ : self.__checksum_end__ + packet_length])
        return seq_num, data


    def packet_recevied(self, packet, address):
        try:
            seq_num, data = self.get_packet_info(packet)
            print(f'Received: Seq No: {seq_num}')
        except AssertionError:
            print('Corrupted packet received')
            return
        if not data:
            self.__acked_packets__.add(seq_num)
            while self.__send_start__ in self.__acked_packets__:
                self.__timers__[self.__send_start__].cancel()
                del self.__timers__[self.__send_start__]
                del self.__send_buffer__[self.__send_start__]
                self.__acked_packets__.remove(self.__send_start__)
                print(f'Removed {self.__send_start__} from send buffer.')
                self.__send_start__ += 1
            print(f'Updated {self.__send_start__}')
        elif self.__recv_start__ <= seq_num < self.__recv_start__ + self.WINDOW_SIZE:
            self.send_ack(seq_num, address)
            self.__recv_buffer__[seq_num] = data
            print(f'Received new packet with Seq Number : {seq_num}.')
        elif self.__recv_start__ - self.WINDOW_SIZE <= seq_num < self.__recv_start__:
            self.send_ack(seq_num, address)
        else:
            print(f'Outside window: {self.__recv_start__}, Seq Num : {seq_num}')


    def listenRUDP(self):
        while self.__running__:
            try:
                r_list, _, _ = select.select([self.__sock__], [], [], 0.1)
                if r_list != [self.__sock__]:
                    continue
                packet, address = self.__sock__.recvfrom(self.MAX_IP_SIZE)
                self.packet_recevied(packet, address)
            except (ConnectionRefusedError, ConnectionAbortedError, OSError):
                print("Connection closed.")
                self.__send_buffer__.clear()
                self.__running__ = False

    def bindRUDP(self):
        self.__sock__.bind((self.__address__, self.__port__))

    def connectRUDP(self):
        self.__sock__.connect((self.__address__, self.__port__))

    def recvRUDP(self):
        buffer = bytearray()
        if self.__recv_start__ in self.__recv_buffer__:
            buffer += self.__recv_buffer__[self.__recv_start__]
            self.__recv_start__ += 1
            print(f"Window Slided from {self.__recv_start__}")
        return bytes(buffer)

    def sendRUDP(self, data):
        if self.__seqnum_send__ >= self.__send_start__ + self.WINDOW_SIZE:
            raise Exception('Send Buffer Overflow')
        packet = self.create_packet(self.__seqnum_send__, data)
        self.__send_buffer__[self.__seqnum_send__] = packet
        self.start_timer(self.__seqnum_send__)
        self.__sock__.sendall(packet)
        self.__seqnum_send__ += 1

    def closeRUDP(self, timeout=120):
        timed_out = False

        def flush_timeout():
            nonlocal timed_out
            timed_out = True
            self.__send_buffer__ = {}

        if timeout:
            Timer(timeout, flush_timeout).start()
        while self.__send_buffer__:
            time.sleep(1)
        for timer in self.__timers__.values():
            timer.cancel()
        self.__running__ = False
        self.__sock__.close()
        if timed_out:
            raise TimeoutError
    
    def start_timer(self, seq_num):
        timer = Timer(self.TIMEOUT, self.handle_timeout, (seq_num,))
        timer.start()
        self.__timers__[self.__seqnum_send__] = timer

    def handle_timeout(self, seq_num):
        if not self.__running__:
            return
        print(f"Timed out for Seq Num : {seq_num}")
        try:
            self.__sock__.send(self.__send_buffer__[seq_num])
        except KeyError:
            print(f"{seq_num} not in send buffer during timeout.")
        except (ConnectionRefusedError, ConnectionAbortedError):
            print(f"Connection closed. Seq Num : {seq_num}.")
            self.__send_buffer__.clear()
            self.closeRUDP()
        else:
            self.start_timer(seq_num)