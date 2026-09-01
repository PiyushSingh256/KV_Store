from common.store import Store
import threading
import pytest

def test_set_get_round():
    store=Store()
    store.set("user1","rahul")
    assert store.get("user1")=="rahul"

def test_missing_key():
    store=Store()
    with pytest.raises(KeyError):
        store.get("missing")

def test_delete_key():
    store=Store()
    store.set("key","delete")
    store.delete("key")
    with pytest.raises(KeyError):
        store.get("key")

def test_del_missing():
    store=Store()
    with pytest.raises(KeyError):
        store.delete("error")

def test_concurrency_somke_test():
    store=Store()
    threads=[]
    for i in range(50):
        thread=threading.Thread(
            target=store.set,
            args=(f"key{i}",f"value{i}")
        )
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    for i in range(50):
        assert store.get(f"key{i}")==f"value{i}"