import threading

class Replication:
    def __init__(self):
        self._entries=[]
        self._next_seq=1
        self._lock=threading.Lock()
    def append(self,command_type,key,value=None):
        with self._lock:
            entry={
                "seq":self._next_seq,
                "command_type":command_type,
                "key":key,
                "value":value
            }
            self._entries.append(entry)
            seq=self._next_seq
            self._next_seq+=1
            return seq
    def get_since(self,seq):
        with self._lock:
            return [
                entry
                for entry in self._entries
                if entry["seq"]>seq
            ]