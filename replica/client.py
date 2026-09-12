import socket
from common.protocol import encode,decode
from common.store import Store

class ReplicaClient:
    def __init__(self,leader_host,leader_port):
        self.leader_host=leader_host
        self.leader_port=leader_port
        self.store=Store()
    def connect_and_run(self):
        conn=socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        try:
            conn.connect(
                (self.leader_host,self.leader_port)
            )
            handshake={
                "type": "HANDSHAKE",
                "last_seq":0
            }
            conn.sendall(encode(handshake))
            while True:
                try:
                    message=decode(conn)
                except ConnectionError:
                    break
                if message["type"]!="REPLICATE":
                    print(
                        f"Warning: unexpected message type"
                        f"{message['type']}"
                    )
                    continue
                entry=message["entry"]
                command_type=entry["command_type"]
                if command_type=="SET":
                    self.store.set(
                        entry["key"],
                        entry["value"]
                    )
                elif command_type=="DELETE":
                    try:
                        self.store.delete(entry["key"])
                    except KeyError:
                        print(
                            f"Warning: DELETE for missing key"
                            f"{entry['key']}"
                        )
                        continue
                else:
                    print(
                        f"Warning: unknown command type"
                        f"{command_type}"
                    )
                    continue
                ack={
                    "type":"ACK",
                    "seq":entry["seq"]
                }
                conn.sendall(encode(ack))
        finally:
            conn.close()