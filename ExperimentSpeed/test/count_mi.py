import os
import sys
import time
import sqlite3
import pandas as pd
import multiprocessing
from test_secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

import test_cluster_db_query as cdq
import test_db_query as dq

db_index = '/home/dnlab/Jupyter-Bitcoin/index.db'
index_conn = sqlite3.connect(db_index)
tcur = index_conn.cursor()

def all_tx():
    try:
        tcur.execute('''SELECT id FROM TxID; ''')
        tx_list = [tx[0]for tx in tcur.fetchall()]
        return set(tx_list)

    except Exception as e:
        #print("[ERROR]",tx_indexes, "get_addr_txin", e)
        return None
    
    
def get_txOut():
    try:
        tcur.execute('''select distinct(tx) from TxOut where n > 0;''')
        tx_list = [tx[0] for tx in tcur.fetchall()]
        return set(tx_list)

    except Exception as e:
        #print("[ERROR]",tx_indexes, "get_addr_txin", e)
        return None

    
def get_addr_from_tx_in(tx_list):
    try:
        tcur.execute(f'''select distinct(address) from TxIn where tx={tx_list};''')
        tx_list = [addr[0] for addr in tcur.fetchall()]
        return set(tx_list)

    except Exception as e:
        #print("[ERROR]",tx_indexes, "get_addr_txin", e)
        return None 
    

def main():
    single_out_set =  get_txOut()
    df = pd.DataFrame(single_out_set)
    df.to_csv('./txlist.csv')
    addr_set = get_addr_from_tx_in(list(single_out_set))
    print(len(addr_set))
    

if __name__ == "__main__":
    main()
    