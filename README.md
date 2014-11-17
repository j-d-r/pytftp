pytftp
======

This is currently a **partial** implementation of the server portion of "The
TFTP Protocol (Revision 2)" as described in
[RFC 783](https://tools.ietf.org/html/rfc783). The TFTP protocol is designed
for ease of implementation, and does not have any security considerations in
the specification.

Note that RFC 783 is obsoleted by
[RFC 1350](https://tools.ietf.org/html/rfc1350).

Partial Implementation
----------------------

Notably absent from this version of the implementation is support for the
following:

* "mail" mode
* handling of duplicated packets
* timeout and retransmission of packets
* limiting locations from where files may be read or written

Usage
-----

To start the TFTP server, run `python tftpd.py`. The TFTP server will listen
on port 69 and handle TFTP transfers until it is terminated.

License
-------

See file "LICENSE".