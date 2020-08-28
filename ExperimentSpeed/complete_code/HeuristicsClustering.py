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
    

def is_resume():
    cur_address = cdq.get_max_address()
    max_address = dq.get_max_address()
    if cur_address == max_address:
        return False
    return True


def resume():
    if is_resume():
        term = 10000
        start_height = cdq.get_max_height()
        end_height = dq.gext_max_height()
        pool_num = multiprocessing.cpu_count()//2
        s_index = cdq.get_max_address()
        u = uf.UnionFind(dq.get_max_address() - s_index + 1)
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
                            u.union(int(addr_1) - s_index, int(addr_2) - s_index)           
                etime = time.time()
                print('height: {}, time:{}'.format(eheight, etime-stime))
            del u.rank

    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected! Commit transactions...')
        cdq.commit_transactions()
        
    addr_list = []
    count = 0
    for index, cluster in enumerate(u.par):
        addr_list.append((str(index + s_index), u.find(cluster) + s_index))
        count += 1
    df = pd.DataFrame(addr_list, columns =['Address', 'ClusterNum'])
    mi_group = mi_df.groupby('ClusterNum')

    for cluster_number, addr_group in mi_group:
        if cluster_number != -1:
            addr_list = list(addr_group.Address)
            cluster_num_list = list(cdq.get_cluster_number(addr_list))
            if len(cluster_num_list) <= 1:
                if cluster_num == -1:
                    insert_cluster_many(list(zip(addr_list, [cluster_number] * len(addr_list))))
                else:
                    insert_cluster_many(list(zip(addr_list, [cluster_num] * len(addr_list))))
            else:
                cluster_num_list.sort()
                cluster_num = cluster_num_list.pop(0)
                if cluster_num == -1:
                    cluster_num = cluster_num_list.pop(0)
                #TODO 만약 같은 주소가 존재한다면 update 그렇지 않다면 insert
                update_cluster_many(list(zip([cluster_num] * len(addr_list), addr_list)))
                
            
            
                
        
        
    
    '''
    지속적인 비트코인 주소를 업데이트하는 함수
    1. 현재주소와, 최대주소 비교 (Meta Table 만드는것 추천)
    2. 현재주소와 최대주소가 다르다면, Clustering 시작
    3. start_height = Metatable.blk.+1
       end_height = dq.get_max_height()
    4. index = cur_addr
    5. uf.UnionFind(max_addr - cur_addr + 1)
    6. 아래와 유사
       ** u.union(int(addr_1) - index, int(addr_2) - index) ** ==> 함수 1 union
          addr_list.append((str(index) + index, u.find(cluster)+index)) ==> 함수 2 Clustering
          df = pd.DataFrame(addr_list) 
          for cluster_list groupby 해서 주소리스트를 가져옴: ==> dbwrite
            - 주소들이 포함된 모든 클러스터 번호를 가져옴
              만약 클러스터 번호가 없다면 그대로 add
            - 클러스터 번호가 1개라면 그 번호로 클러스터 add
            - 만약 클러스터 번호가 여러개라면 가장 작은것으로 add후
              다른 클러스터가 있는것은 update
    '''
    
    
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

