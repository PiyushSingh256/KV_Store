import socket
from common.protocol import encode,decode
import pytest

def test_small_message():
    sock_a,sock_b=socket.socketpair()
    message={
        "type":"GET",
        "key":"user:1"
        }
    sock_a.sendall(encode(message))
    decoded=decode(sock_b)
    assert decoded==message
    sock_a.close()
    sock_b.close()

def test_large_message():
    sock_a,sock_b=socket.socketpair()
    message={
        "type":"SET",
        "key":"bulk",
        "value":"x"*50000
    }
    sock_a.sendall(encode(message))
    decoded=decode(sock_b)
    assert message==decoded
    sock_a.close()
    sock_b.close()

def test_connection_closed_mid_read():
    sock_a,sock_b=socket.socketpair()
    sock_a.send(b"\x00\x00")
    sock_a.close()
    with pytest.raises(ConnectionError):
        decode(sock_b)
    sock_b.close()