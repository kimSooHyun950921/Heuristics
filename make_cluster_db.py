import os
import sys
import time
import sqlite3
import multiprocessing
from secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

import cluster_db_query as cdq
import db_query as dq

rpc_ip = '127.0.0.1'
rpc_port = '8332'
timeout = 300

def get_rpc():
    return AuthServiceProxy(f'http://{rpc_user}:{rpc_password}@{rpc_ip}:{rpc_port}', timeout=timeout)


def get_data(start):
    addrs = dq.get_addr_many(start, start + 1000)
    return addrs
    
    for tx in txes:
        tx_indexes = dq.get_txid(tx)
        in_addrs = dq.get_addr_txin(tx_indexes)
        out_addrs = dq.get_addr_txout(tx_indexes)
        if in_addrs == None or out_addrs == None:
            return None
        
        all_addrs = list(in_addrs.union(out_addrs))
        if len(all_addrs) == 0:
            return None
        
        cluster_nums = [-1] * len(all_addrs)
        cluster_list = list(zip(all_addrs, cluster_nums))
        return cluster_list
    
    
def main():
    term = 1000
    start_tx = 0
    end_tx = dq.get_max()
    pool_num = multiprocessing.cpu_count()//2

    cdq.create_cluster_table()
    cdq.create_meta_table()
    print("CLSUTER TABLE MADE")
    time.sleep(5)
    
    stime = time.time()
    cdq.begin_transactions()
    for i in range(start_tx, end_tx, 1000):    
        addr_list = get_data(i)
        cdq.insert_cluster_many(addr_list)
        etime = time.time()
        print('tx index: {}, time:{}'.format(i, etime-stime))
    cdq.commit_transactions()
            
if __name__=="__main__":
    main()
