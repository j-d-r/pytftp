pytftp
======

This is currently a **partial** implementation of the server portion of "The
TFTP Protocol (Revision 2)" as described in
[RFC 1350](https://tools.ietf.org/html/rfc1350). The TFTP protocol is designed
for ease of implementation, and does not have any security considerations in
the specification.

Partial Implementation
----------------------

Notably absent from this version of the implementation is support for the
following:

* "mail" mode
* handling of duplicated DATA packets
* timeout and retransmission of packets

Usage
-----

To start the TFTP server, run `python tftpd.py`. The server will listen
on port 69 and handle TFTP transfers until it is terminated.

License
-------

See file "LICENSE".
