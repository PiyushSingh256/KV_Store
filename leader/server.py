import socket
import threading
from common.protocol import decode,encode
from common.store import Store
from leader.replica_manager import ReplicaManager

class Server:
    def __init__(self,host="0.0.0.0",port=6380,replica_port=6381):
        self.replica_port=replica_port
        self.replica_manager=ReplicaManager()
        self.host=host
        self.port=port
        self.store=Store()
    def start(self):
        client_thread=threading.Thread(
            target=self._accept_client,
            daemon=True
        )
        replica_thread=threading.Thread(
            target=self._accept_replicas,
            daemon=True
        )
        client_thread.start()
        replica_thread.start()

        client_thread.join()
        replica_thread.join()

    def _accept_client(self):
        server_socket=socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        server_socket.bind((self.host,self.port))
        server_socket.listen()
        print(f"Client server listening on {self.host}:{self.port}")
        while True:
            conn,addr=server_socket.accept()
            thread=threading.Thread(
                target=self.handle_client,
                args=(conn,),
                daemon=True
            )
            thread.start()

    def _accept_replicas(self):
        replica_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        replica_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
        replica_socket.bind(
            (self.host,self.replica_port)
        )
        replica_socket.listen()
        print(f"Replica server listening on "
            f"{self.host}:{self.replica_port}"
        )
        while True:
            conn,addr=replica_socket.accept()
            thread=threading.Thread(
                target=self.handle_replica,
                args=(conn,),
                daemon=True
            )
            thread.start()
    
    def handle_client(self,conn):
        try:
            while True:
                try:
                    message=decode(conn)
                except ConnectionError:
                    break
                response=self.handle_message(message)
                conn.sendall(encode(response))
        finally:
            conn.close()

    def handle_replica(self,conn):
        try:
            message=decode(conn)
            self.replica_manager.add_replica(conn)
            while True:
                try:
                    message=decode(conn)
                except ConnectionError:
                    break
                if message["type"]=="ACK":
                    self.replica_manager.update_ack(
                        conn,message["seq"]
                    )
        finally:
            self.replica_manager.remove_replica(conn)
            conn.close()


    def handle_message(self,message):
        command_type=message["type"]
        if command_type=="SET":
            self.store.set(
                message["key"],
                message["value"]
            )
            return {"status":"OK"}
        elif command_type=="GET":
            try:
                value=self.store.get(message["key"])
                return {
                    "status":"OK",
                    "value":value
                }
            except KeyError:
                return {
                    "status":"ERROR",
                    "message":"Key not found"
                }
        elif command_type=="DELETE":
            try:
                self.store.delete(message["key"])
                return {"status":"OK"}
            except KeyError:
                return {
                    "status":"ERROR",
                    "message":"key not found"
                }
        else:
            return{
                "status":"ERROR",
                "message":"Unknown command type"
            }   

if __name__=="__main__":
    server=Server()
    server.start()