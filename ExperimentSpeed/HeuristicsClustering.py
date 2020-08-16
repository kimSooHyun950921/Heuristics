import os
import sys
import time
import sqlite3
import multiprocessing
import heuristics
import unionfind as uf

from test_secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from test_cluster_db_query import ClusterDB
import test_db_query as dq

rpc_ip = '127.0.0.1'
rpc_port = '8332'
timeout = 300

def get_rpc():
    return AuthServiceProxy(f'http://{rpc_user}:{rpc_password}@{rpc_ip}:{rpc_port}', timeout=timeout)

def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(in_addrs) <= 0: 
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
            print("Cannot assign requested address!")
            time.sleep(3)
    return txes


def make_addr_set(addr1, addr2):
    if int(addr1) > int(addr2):
        return (addr2, addr1)
    return (addr1, addr2)


def multi_input(height):
    txes = rpc_command(height)
    all_addr = list()
    for tx in txes:
        tx_indexes = dq.get_txid(tx)
        in_addrs = dq.get_addr_txin(tx_indexes)
        out_addrs = dq.get_addr_txout(tx_indexes)
        
        if is_mi_cond(in_addrs, out_addrs):
            first_addr = in_addrs.pop()
            while len(in_addrs) > 0:
                second_addr = in_addrs.pop()      
                addr_set = make_addr_set(first_addr, second_addr)
                all_addr.append(addr_set)
                
    return all_addr


def db_write(stime, cdq, u):
    addr_list = []
    count = 0
    cdq.create_cluster_table()
    for index, cluster in enumerate(u.par):
        addr_list.append((str(index),u.find(cluster)))
        if count % 10000 == 0:
            cdq.begin_transactions()
            cdq.insert_cluster_many(addr_list)
            cdq.commit_transactions()
            etime = time.time()
            print(f"COUNT {count} END, TOTAL TIME: {etime - stime},\
                    {addr_list[len(addr_list)-1]}")
            del addr_list
            addr_list = list()
        count += 1
        
    while len(addr_list) > 0:
        cdq.begin_transactions()
        cdq.insert_cluster_many(addr_list)
        cdq.commit_transactions()
        etime = time.time()
        print(f"COUNT {count} END, TOTAL TIME: {etime - stime},\
                {addr_list[len(addr_list)-1]}")
        del addr_list
        addr_list = list()
    etime = time.time()
    
    del u.par
    print(f"CLUSTERING END:{etime - stime}")  
    
    
def main(args):
    
    term = 10000
    start_height = 1
    end_height = dq.get_max_height()
    pool_num = multiprocessing.cpu_count()//2  
    cdq = ClusterDB(args.dbpath)
    
    stime = time.time()
    u = uf.UnionFind(int(dq.get_max_address())+1)
    try:
        for sheight, eheight in zip(range(start_height, end_height, term), \
                                    range(start_height+term, end_height+term, term)):
            if eheight >= end_height:
                eheight = end_height + 1

            with multiprocessing.Pool(pool_num) as p:
                result = p.imap(multi_input, range(sheight, eheight))
                for addr_list in result:
                    for addr_set in addr_list:
                        addr_1 = addr_set[0]
                        addr_2 = addr_set[1]
                        u.union(int(addr_1), int(addr_2))           
            etime = time.time()
            print('height: {}, time:{}'.format(eheight, etime-stime))
        del u.rank
        db_write(stime, cdq, u)

    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected! Commit transactions...')
        cdq.commit_transactions()

            
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Heuristics Clusterings')
    parser.add_argument('--dbpath', '-d', type=str,
                        required=True,
                        help='insert make dbpath')
    parser.add_argument('--resume', '-r', type=bool,
                        default=False,
                        help='execute resume')

    args = parser.parse_args()
    main(args)
