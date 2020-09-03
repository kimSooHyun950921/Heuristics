import os
import sys
import time
import sqlite3
import cluster_db_query as cdq
import db_query as dq

def main():
    start_addr = 0
    end_addr = dq.get_addr_max()
    print("max_addr:", end_addr)
    time.sleep(4)
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
