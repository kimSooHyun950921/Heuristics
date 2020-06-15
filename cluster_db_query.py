import sys
import time
import sqlite3
import multiprocessing
from secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

db_path = '/home/dnlab/BitcoinBlockSampler/cluster.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()


def create_meta_table():
    cur.execute('''CREATE TABLE IF NOT EXISTS Meta (
                     key TEXT PRIMARY KEY,
                     value INTEGER);
                ''')
    
    
def update_meta_table(key, value):
    cur.execute('''INSERT OR IGNORE INTO Meta (
                        key, value) VALUES (
                        ?, ?);
                ''', (key, value))
    cur.execute('''UPDATE Meta SET value = ? WHERE key = ?;
                ''', (value, key))
    

def get_meta(key):
    cur.execute('''SELECT value FROM Meta WHERE key = ?''', (key,))
    result = cur.fetchone()
    if result is not None:
        result = result[0]
    return result
    
    
def create_cluster_table():
    cur.execute('''CREATE TABLE IF NOT EXISTS Cluster (
                     address TEXT PRIMARY KEY,
                     number INTEGER NOT NULL);
                ''')
    
    
def insert_cluster(address, number):
    cur.execute('''INSERT OR IGNORE INTO Cluster (
                       address, number) VALUES (
                       ?, ?);
                    ''', (address, number))

    
def insert_cluster_many(addr_list):
    #print(addr_list)
    cur.executemany('''INSERT OR IGNORE INTO Cluster VALUES (?, ?)''',addr_list)
    
    
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


def get_cluster_number(addrss):
    cur.execute(f'''SELECT number FROM Cluster WHERE address IN ('{",".join(addrss)}')'''.replace('\'',''))
    cls_num = []
    for addr_tuple in cur.fetchall():
        cls_num.append(addr_tuple[0])
    return set(cls_num)


def get_all_cluster():
    try:
        cur.execute('''SELECT DISTINCT * FROM Cluster; ''')
        addr_dict = dict()
        for addr in cur.fetchall():
            addr_dict.update({addr[0]:addr[1]})
        return addr_dict
    except Exception as e:
        return None


def update_cluster(addrs, cluster_num):
    #try:
        print(type(addrs[0]))
        cluster_nums = [cluster_num] * len(addrs)
        cluster_list = list(zip(addrs, cluster_nums))
        print(cluster_list)
        
        ####begintransaction######                 
        insert_cluster_many(cluster_list)
        ####end commit ###########
    #    return True
    #except Exception as e:
     #   print(e)
      #  return False