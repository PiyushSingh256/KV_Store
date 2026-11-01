import json
import struct
import socket

class IdleTimeout(Exception):
    """No bytes of the next frame arrived before the socket timeout.
    The stream is still in sync, so the caller may keep using the connection."""

class FrameTimeout(ConnectionError):
    """Timed out after part of a frame was already read.
    The stream is out of sync, so the connection must be closed."""

def encode(message:dict):
    payload=json.dumps(message).encode("utf-8")  
    header=struct.pack(">I",len(payload))
    return header+payload

def recv_exact(sock:socket.socket,n,idle_ok=True):
    data=b""
    while len(data)<n:
        try:
            chunk=sock.recv(n-len(data))
        except socket.timeout:
            if idle_ok and not data:
                raise IdleTimeout("no data before timeout")
            raise FrameTimeout("Timed out in the middle of a frame")
        if not chunk:
            raise ConnectionError("Connection closed while reciving data")
        data+=chunk
    return data


def decode(sock:socket.socket):
    header=recv_exact(sock,4)
    payload_length=struct.unpack(">I",header)[0]
    payload=recv_exact(sock,payload_length)
    message=json.loads(payload.decode("utf-8"))
    return message