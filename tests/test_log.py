from common.log import Replication
import threading

def test_append_assings_sequnce_number():
    log=Replication()
    seq1=log.append("SET","name","rohit")
    seq2=log.append("SET","age",20)
    assert seq1==1
    assert seq2==2

def test_get_since_returns_correct_subset():
    log=Replication()
    log.append("SET","name","rohit")
    log.append("SET","age",20)
    log.append("DELETE","age")

    result=log.get_since(1)
    assert result==[
        {
            "seq":2,
            "command_type":"SET",
            "key":"age",
            "value":20
        },
        {
            "seq":3,
            "command_type":"DELETE",
            "key":"age",
            "value":None 
        }
    ]

def test_get_since_zero_returns_all_entries():
    log=Replication()
    log.append("SET","name","rohit")
    log.append("SET","age",20)
    log.append("DELETE","age")
    result=log.get_since(0)

    assert len(result)==3
    assert [entry["seq"] for entry in result]==[1,2,3]

def test_entry_shape():
    log=Replication()
    log.append("SET","name","rohit")
    result=log.get_since(0)
    assert result[0]=={
        "seq":1,
        "command_type":"SET",
        "key":"name",
        "value":"rohit"
    }

def test_concurrent_append():
    log=Replication()
    seq_number=[]
    threads=[]
    def append_entry(i):
        seq=log.append(
            "SET",
            f"Key{i}",
            f"value{i}"
        )
        seq_number.append(seq)
    for i in range(100):
        thread=threading.Thread(
            target=append_entry,
            args=(i,)
        )
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    assert len(set(seq_number))==100
    assert sorted(seq_number)==list(range(1,101))   