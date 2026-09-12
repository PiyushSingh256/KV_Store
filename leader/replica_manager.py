import threading
from common.protocol import encode

class ReplicaManager:
    def __init__(self):
        self._replica={}
        self._lock=threading.Lock()
    def add_replica(self,conn):
        with self._lock:
            self._replica[conn]={
                "last_acked_seq":0
            }
    def remove_replica(self,conn):
        with self._lock:
            self._replica.pop(conn,None)
    def broadcast(self,entry):
        message={
            "type":"REPLICATE",
            "entry":entry
        }
        data=encode(message)
        failed_replica=[]
        with self._lock:
            for conn in self._replica:
                try:
                    conn.sendall(data)
                except (ConnectionError,OSError):
                    failed_replica.append(conn)
        for conn in failed_replica:
            self.remove_replica(conn)
    def update_ack(self,conn,seq):
        with self._lock:
            if conn in self._replica:
                self._replica[conn]["last_acked_seq"]=seq