"""
Group Members

Sukrit 2018A7PS0205H
Kumar Pranjal 2018A7PS0163H
Sneh Lohia 2018A7PS0171H
Pranay Pant 2018A7PS0161H
Dhiraaj Desai 2018A7PS0146H

"""

import argparse
import ipaddress
import logging
import time
from pathlib import Path
from RUDP import RUDP

NAME_MARKER = b":name:"
END_MARKER = b":end:"

def receiver(address, port, directory, **kwargs):
    sock_fd = RUDP(str(address), port)
    sock_fd.bindRUDP()
    print(f"Receiver bound to Address: {address}, Port: {port}")
    directory.mkdir(exist_ok=True)

    file_name = None
    file = None

    while True:
        data = sock_fd.recvRUDP()
        if not data:
            if not file_name:
                time.sleep(1)
            else:
                time.sleep(0.1)
            continue
        if data.startswith(NAME_MARKER):
            file_name = data[len(NAME_MARKER) :].decode()
            file = open(directory / file_name, "wb")
            print(f"Receiving {file_name}")
            size, start_time = 0, time.time()
        elif data == END_MARKER:
            delta_time = time.time() - start_time
            file.close()
            break
        else:
            size += len(data)
            file.write(data)
    sock_fd.closeRUDP()
    try:
        speed = size / delta_time
    except ZeroDivisionError:
        speed = float("inf")
    print(
        f"Completed receiving {file_name}, {size} bytes, "
        f"{delta_time:.3f} seconds, speed={speed:.3f}BPS"
    )
    if 'result' in kwargs:
        kwargs['result']['size'] = size
        kwargs['result']['time'] = delta_time


def sender(address, port, file, **kwargs):
    sock_fd = RUDP(str(address), port)
    sock_fd.connectRUDP()

    print(f"Sending {file.name}")
    sock_fd.sendRUDP(NAME_MARKER + str(file.name).encode("utf-8"))
    file_data = file.read_bytes()
    total_size = len(file_data)
    pkt_size = RUDP.MAX_DATA_SIZE
    offset = 0

    while offset < total_size:
        try:
            sock_fd.sendRUDP(file_data[offset : offset + pkt_size])
        except Exception:
            time.sleep(1)
        else:
            offset += pkt_size
    sock_fd.sendRUDP(END_MARKER)
    sock_fd.closeRUDP()
    print(f"Completed sending {file.name}, {total_size} bytes")
    exit(0)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Send and Receive files over RUDP.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--address",
        type=ipaddress.IPv4Address,
        default="127.0.0.1",
        help="Which IP address to bind/connect to",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=3333, help="Receiver port",
    )
    subparser = parser.add_subparsers(help="Role? (receiver/sender)")
    parser_sender = subparser.add_parser("sender")
    parser_sender.add_argument("file", type=Path, help="File to send over RUDP")
    parser_sender.set_defaults(func=sender)
    parser_receiver = subparser.add_parser("receiver")
    parser_receiver.add_argument(
        "-d",
        "--directory",
        type=Path,
        default="Downloads",
        help="Receiving directory",
    )
    parser_receiver.set_defaults(func=receiver)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        raise argparse.ArgumentError(None, "Invalid role chosen")
    args.func(**vars(args))