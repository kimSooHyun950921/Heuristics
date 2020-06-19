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


def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(out_addrs) <=0:
        return False
    if len(in_addrs) < 2:
        return False
    if len(out_addrs) > 2:
        return False
    return True
    
    
def get_min_cluster_num(addr, flag=0):
    ''' DON'T USE
        flag: 0 전체 최소값
        flag: 1 -1이 아닌 최소값'''
    cluster_num_list = cdq.get_min_cluster(addr)
    cluster_num_list = list()
    for addr in addr_set.keys():
        cluster_num_list.append(addr_set[addr])
    sort_cls_num_list = sorted(cluster_num_list)
    if flag == 0:
        return sort_cls_num_list[0]
    elif flag == 1:
        for num in sort_cls_num_list:
            if num > -1:
                return num
            
    
def get_cluster_num(addrs):
    cls_num = -1
    max_cluster_num  = cdq.get_meta('max_num')
    cls_num_set = set(cdq.get_cluster_number(addrs))
    #all same cluster
    if len(cls_num_set) == 1:
        cls_num = cls_num_set.pop()
        if cls_num == -1:
            cls_num = max_cluster_num + 1
            max_cluster_num = cls_num
            #####################
            #cdq.begin_transactions()
            cdq.update_meta_table('max_num', max_cluster_num)
            #cdq.commit_transactions()
            #######################

    else:
        cls_num = cdq.get_min_clustered(addrs)
    return cls_num


def update_cluster(addrs, cluster_num):
    try:
        cluster_nums = [cluster_num] * len(addrs)
        cluster_list = list(zip(addrs, cluster_nums))

        cdq.insert_cluster_many(cluster_list)

        return True
    except Exception as e:
        print(e)
        return False
    
    
def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(out_addrs) <= 0:
        return False
    if len(in_addrs) < 2:
        return False
    if len(out_addrs) > 2:
        return False
    return True

def rpc_command(height):
    while True:
        try:
            rpc_connection = get_rpc()
            block_hash = rpc_connection.getblockhash(height)
            txes = rpc_connection.getblock(block_hash)['tx']
            break
        except OSError as e:
            print("Cannot assing requested address!")
            time.sleep(3)
    return txes
        
def multi_input(height):
    txes = rpc_command(height)  
    for tx in txes:
        tx_indexes = dq.get_txid(tx)
        in_addrs = dq.get_addr_txin(tx_indexes)
        out_addrs = dq.get_addr_txout(tx_indexes)
        
        if is_mi_cond(in_addrs, out_addrs):
                cluster_num = get_cluster_num(in_addrs)
                try:
                    cdq.begin_transactions()
                except Exception as e:
                    cdq.commit_transactions()
                    cdq.begin_transactions()
                    
                update_cluster(in_addrs, cluster_num)
                
                try:
                    cdq.commit_transactions()
                except Exception as e:
                    print(e)

    
def main():
    term = 1000
    start_height = 0
    end_height = dq.get_max()
    
    ####begintransaction######
    #cdq.begin_transactions()
    cdq.update_meta_table('max_num', -1)
    cdq.commit_transactions()
    ####end commit ###########    
    
    print("CLSUTER TABLE MADE")
    time.sleep(5)
    stime = time.time()
    for height in range(0, end_height):
        multi_input(height)
        etime = time.time()
        if height % 1000 == 0:
            print('height: {}, time:{}'.format(height, etime-stime))

            
if __name__=="__main__":
    main()