import sys
import time
import sqlite3
import multiprocessing
from secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

db_path = '/home/dnlab/Jupyter-Bitcoin/Heuristics/DB/cluster_TEST.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

         
def create_cluster_table():
    cur.execute('''CREATE TABLE IF NOT EXISTS Cluster (
                     address INTEGER PRIMARY KEY,
                     number INTEGER NOT NULL);''')
    
    
def insert_cluster(address, number):
    cur.execute('''INSERT OR IGNORE INTO Cluster (
                       address, number) VALUES (?, ?);
                ''', (address, number))


def insert_cluster_many(addr_list):
    cur.executemany('''INSERT OR IGNORE INTO Cluster VALUES (?, ?)''', addr_list)
    
    
def update_cluster_many(addr_list):
    index = 0
    try:
        while index < len(addr_list):
            sample_list = addr_list[index: index+10000]
            cur.executemany('''UPDATE Cluster SET number = ? WHERE address = ?''', addr_list)
            index += 10000
        return True
    except sqlite3.Error as error:
        print(error)
        return False
    

def find_addr_from_cluster_num(num):
    '''클러스터 번호가 num인 모든 주소를 가져옴
       '''
    cur.execute('''SELECT address FROM Cluster WHERE number = {}'''.format(num))
    addr_list = [addr[0] for addr in cur.fetchall()]
    return addr_list
    
    
def begin_transactions():
    cur.execute('BEGIN TRANSACTION;')

    
def commit_transactions():
    cur.execute('COMMIT;')

    
def get_min_all_cluster(addrss):
    cur.execute(f'''SELECT MIN(number) FROM Cluster WHERE address IN ('{",".join(addrss)}')'''.replace('\'',''))
    return cur.fetchone()[0]


def get_min_clustered(addrss):
    cur.execute(f'''SELECT MIN(number) FROM Cluster WHERE address IN ('{",".join(addrss)}') and number > -1'''.replace('\'',''))
    return cur.fetchone()[0]


def get_max_clustered():
    cur.execute(f'''SELECT MAX(number) FROM Cluster''')
    return cur.fetchone()[0]


def get_cluster_number(addrss):
    try:
        cur.execute(f'''SELECT number FROM Cluster WHERE address IN ('{",".join(addrss)}')'''.replace('\'',''))
        cls_num = []
        for addr_tuple in cur.fetchall():
            cls_num.append(addr_tuple[0])
        return set(cls_num)
    except sqlite3.DatabaseError as e:
        print("[ERROR]: get_cluster_number", addrss, e)
        

def get_all_cluster():
    try:
        cur.execute('''SELECT DISTINCT * FROM Cluster; ''')
        addr_dict = dict()
        for addr in cur.fetchall():
            addr_dict.update({addr[0]:addr[1]})
        return addr_dict
    except Exception as e:
        return None

