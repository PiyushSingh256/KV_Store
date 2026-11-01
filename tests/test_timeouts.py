import socket
import threading
import time
import pytest
from common.protocol import encode,decode,IdleTimeout,FrameTimeout
from leader.replica_manager import ReplicaManager
from leader.server import Server
from replica.client import ReplicaClient

def free_port():
    s=socket.socket()
    s.bind(("127.0.0.1",0))
    port=s.getsockname()[1]
    s.close()
    return port

def start_server(**kwargs):
    server=Server(
        host="127.0.0.1",
        port=free_port(),
        replica_port=free_port(),
        **kwargs
    )
    threading.Thread(target=server.start,daemon=True).start()
    deadline=time.time()+2
    while time.time()<deadline:
        try:
            for p in (server.port,server.replica_port):
                socket.create_connection(("127.0.0.1",p),timeout=0.2).close()
            return server
        except OSError:
            time.sleep(0.02)
    raise RuntimeError("server did not start")

def connect(port):
    sock=socket.create_connection(("127.0.0.1",port))
    sock.settimeout(3)
    return sock

def test_idle_timeout_at_frame_boundary_keeps_stream_usable():
    a,b=socket.socketpair()
    b.settimeout(0.1)
    with pytest.raises(IdleTimeout):
        decode(b)
    a.sendall(encode({"type":"GET","key":"k"}))
    assert decode(b)=={"type":"GET","key":"k"}
    a.close()
    b.close()

def test_timeout_mid_header_is_frame_timeout():
    a,b=socket.socketpair()
    b.settimeout(0.1)
    a.sendall(b"\x00\x00")
    with pytest.raises(FrameTimeout):
        decode(b)
    a.close()
    b.close()

def test_timeout_mid_payload_is_frame_timeout():
    a,b=socket.socketpair()
    b.settimeout(0.1)
    frame=encode({"type":"SET","key":"k","value":"v"*100})
    a.sendall(frame[:10])
    with pytest.raises(FrameTimeout):
        decode(b)
    a.close()
    b.close()

def test_frame_timeout_is_a_connection_error():
    assert issubclass(FrameTimeout,ConnectionError)

def test_leader_closes_silent_client():
    server=start_server(client_idle_timeout=0.3)
    sock=connect(server.port)
    start=time.time()
    assert sock.recv(1)==b""
    assert time.time()-start<2
    sock.close()

def test_leader_closes_client_stuck_mid_frame():
    server=start_server(client_idle_timeout=0.3)
    sock=connect(server.port)
    sock.sendall(b"\x00\x00")
    assert sock.recv(1)==b""
    sock.close()

def test_active_client_is_not_closed():
    server=start_server(client_idle_timeout=0.5)
    sock=connect(server.port)
    for i in range(4):
        sock.sendall(encode({"type":"SET","key":"k","value":str(i)}))
        assert decode(sock)=={"status":"OK"}
        time.sleep(0.2)
    sock.close()

def test_leader_closes_replica_that_never_handshakes():
    server=start_server(replica_io_timeout=0.3)
    sock=connect(server.replica_port)
    assert sock.recv(1)==b""
    sock.close()

def test_idle_replica_stays_registered_and_still_receives():
    server=start_server(replica_io_timeout=0.2)
    rep=connect(server.replica_port)
    rep.sendall(encode({"type":"HANDSHAKE","last_seq":0}))
    time.sleep(0.8)
    assert len(server.replica_manager._replica)==1
    client=connect(server.port)
    client.sendall(encode({"type":"SET","key":"a","value":"1"}))
    assert decode(client)=={"status":"OK"}
    message=decode(rep)
    assert message["type"]=="REPLICATE"
    assert message["entry"]["key"]=="a"
    client.close()
    rep.close()

def test_broadcast_drops_replica_that_stops_reading():
    manager=ReplicaManager()
    a,b=socket.socketpair()
    a.settimeout(0.2)
    manager.add_replica(a)
    big={"seq":1,"command_type":"SET","key":"k","value":"x"*5_000_000}
    start=time.time()
    manager.broadcast(big)
    assert time.time()-start<2
    assert a not in manager._replica
    assert a.fileno()==-1
    b.close()

def test_replica_client_survives_leader_silence():
    listener=socket.socket()
    listener.bind(("127.0.0.1",0))
    listener.listen()
    port=listener.getsockname()[1]
    client=ReplicaClient("127.0.0.1",port,connect_timeout=1,io_timeout=0.2)
    thread=threading.Thread(target=client.connect_and_run,daemon=True)
    thread.start()
    conn,_=listener.accept()
    conn.settimeout(3)
    assert decode(conn)["type"]=="HANDSHAKE"
    time.sleep(0.8)
    assert thread.is_alive()
    entry={"seq":1,"command_type":"SET","key":"a","value":"1"}
    conn.sendall(encode({"type":"REPLICATE","entry":entry}))
    assert decode(conn)=={"type":"ACK","seq":1}
    conn.close()
    thread.join(timeout=2)
    assert not thread.is_alive()
    listener.close()