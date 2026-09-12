import socket
from common.protocol import decode
from leader.replica_manager import ReplicaManager

def test_broadcast_delivers_to_replica():
    manager=ReplicaManager()
    sock_a,sock_b=socket.socketpair()
    manager.add_replica(sock_a)
    entry={
        "seq":1,
        "common_type":"SET",
        "key":"x",
        "value":"y"
    }
    manager.broadcast(entry)
    recived=decode(sock_b)
    assert recived=={
        "type":"REPLICATE",
        "entry":entry
    }
    sock_a.close()
    sock_b.close()

def test_broadcast_removes_dead_replica():
    manager=ReplicaManager()
    sock_a,sock_b=socket.socketpair()
    manager.add_replica(sock_a)
    sock_b.close()
    entry={
        "seq":1,
        "command_type":"SET",
        "key":"x",
        "value":"y"
    }
    manager.broadcast(entry)
    assert sock_a not in manager._replica
    sock_a.close()