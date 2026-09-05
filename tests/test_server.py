import socket
import threading
import time
import pytest
from common.protocol import encode,decode
from leader.server import Server

@pytest.fixture(scope="module")
def running_server():
    server=Server(host="127.0.0.1",port=6381)
    thread=threading.Thread(
        target=server.start,
        daemon=True
    )
    thread.start()
    time.sleep(0.1)
    yield server.port

def test_set_then_get(running_server):
    sock=socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    sock.connect(("127.0.0.1",running_server))
    set_message={
        "type":"SET",
        "key":"name",
        "value":"amit"
    }
    sock.sendall(encode(set_message))
    response=decode(sock)
    assert response=={
        "status":"OK"
    }
    get_message={
        "type":"GET",
        "key":"name"
    }
    sock.sendall(encode(get_message))
    response=decode(sock)
    assert response=={
        "status":"OK",
        "value":"amit"
    }
    sock.close()

def test_get_missing_key(running_server):
    sock=socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    sock.connect(("127.0.0.1",running_server))
    message={
        "type":"GET",
        "key":"does_not_exist"
    }
    sock.sendall(encode(message))
    response=decode(sock)
    assert response=={
        "status":"ERROR",
        "message":"Key not found"
    }
    sock.close()

def test_delete(running_server):
    sock=socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    sock.connect(("127.0.0.1",running_server))
    set_message={
        "type":"SET",
        "key":"age",
        "value":20
    }
    sock.sendall(encode(set_message))
    response=decode(sock)
    assert response=={
        "status":"OK"
    }
    delete_message={
        "type":"DELETE",
        "key":"age"
    }
    sock.sendall(encode(delete_message))
    response=decode(sock)
    assert response=={
        "status":"OK"
    }
    get_message={
        "type":"GET",
        "key":"age"
    }
    sock.sendall(encode(get_message))
    response=decode(sock)
    assert response=={
        "status":"ERROR",
        "message":"Key not found"
    }
    sock.close()

def test_unknown_command(running_server):
    sock=socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    sock.connect(("127.0.0.1",running_server))
    message={
        "type":"INVALID"
    }
    sock.sendall(encode(message))
    response=decode(sock)
    assert response=={
        "status":"ERROR",
        "message":"Unknown command type"
    }
    sock.close()