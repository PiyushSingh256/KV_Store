import threading

class Store:
    def __init__(self):
        self._data={}
        self._lock=threading.Lock()
    def set(self,key,value):
        with self._lock:
            self._data[key]=value
    def get(self,key):
        with self._lock:
            return self._data[key]
    def delete(self,key):
        with self._lock:
            del self._data[key]