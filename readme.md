# RUDP - Reliable UDP in Application Layer

## Introduction

RUDP is an application layer transport protocol designed to provide reliability over the UDP protocol.

## Implementation

The implementation has been done in python 3. Only the inbuilt library functions of the language are used.

## Running

1. Make a socket of the RUDP type `sock_fd = RUDP(address, port)`
2. Then use the methods of the socket to send and receive packets from the sender or to send packets.

### File Transfer

-   Receiver Side - Run `python file_transfer.py receiver`
-   Sender Side - Run `python file_transfer.py sender <file_name>` on the sender side.

This will run the RUDP on localhost.
To run for different addresses, you can specify the address using -a tag and port using the -p keyword specifier.

### Automated testing

Automated Testing is done using netem tool which simulates various network conditions like packet drop. First of all, `transfer_test.py` is run from tests folder which runs the test. Then `plot.py` is run which plots all the results.

## Changes during Phase 2

Initially we thought to implement both blocking and non blocking mode in RUDP, but we simply implemented blocking RUDP by default since it does not make any changes in the reliability of the protocol.

## Group Details

Sukrit 2018A7PS0205H

Kumar Pranjal 2018A7PS0163H

Sneh Lohia 2018A7PS0171H

Pranay Pant 2018A7PS0161H

Dhiraaj Desai 2018A7PS0146H
