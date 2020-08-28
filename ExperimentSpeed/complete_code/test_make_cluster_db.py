import os
import sys
import time
import sqlite3
import test_db_query as dq
from test_cluster_db_query import ClusterDB

def main():
    start_addr = 0
    end_addr = dq.get_max_address()
    print("max_addr:", end_addr)
    cdq = ClusterDB('/home/dnlab/DataHDD/dbv3cluster.db')
    cdq.create_cluster_table() 
    stime = time.time()
    for i in range(start_addr, end_addr, 10000):    
        cdq.begin_transactions()
        addr_list = dq.get_addr_many(i, i + 10000)
        cdq.insert_cluster_many(addr_list)
        etime = time.time()
        print('addr index: {}, time:{}'.format(i, etime-stime))
        cdq.commit_transactions()
            
if __name__=="__main__":
    main()
