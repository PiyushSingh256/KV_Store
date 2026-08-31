import json
import struct
import socket

def encode(message:dict):
    payload=json.dumps(message).encode("utf-8")  
    header=struct.pack(">I",len(payload))
    return header+payload

def recv_exact(sock:socket.socket,n):
    data=b""
    while len(data)<n:
        chunk=sock.recv(n-len(data))
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