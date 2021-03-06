import os
import sys
import time
import sqlite3
import multiprocessing
from test_secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

import test_cluster_db_query as cdq
import test_db_query as dq

rpc_ip = '127.0.0.1'
rpc_port = '8332'
timeout = 300

def get_rpc():
    return AuthServiceProxy(f'http://{rpc_user}:{rpc_password}@{rpc_ip}:{rpc_port}', timeout=timeout)


def find_non_cluster_addr(addrs):
    non_cluster_addr_list = []
    for addr in addrs:
        cluster_num_set = cdq.get_cluster_number([addr])
        if len(cluster_num_set) <= 0:
            print("NoClusterNum!", addr)
            continue
        cluster_num = cluster_num_set.pop()
        if cluster_num == -1:
            non_cluster_addr_list.append(addr)
    return non_cluster_addr_list


def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(in_addrs) >= 2 and len(out_addrs) == 1:
        return True
    return False

                
def get_cluster_num(addrs, max_cluster_num):
    cls_num_set = set(cdq.get_cluster_number(addrs))
    #all same cluster
    if len(cls_num_set) == 1:
        cls_num = cls_num_set.pop()
        if cls_num == -1:
            cls_num = max_cluster_num + 1
            max_cluster_num = cls_num 
    else:
        cls_num = cdq.get_min_clustered(addrs)
    return cls_num, max_cluster_num


def update_cluster(addrs, cluster_num):
    try:
        cluster_nums = [cluster_num] * len(addrs)
        cluster_list = list(zip(addrs, cluster_nums))

        cdq.insert_cluster_many(cluster_list)

        return True
    except Exception as e:
        print(e)
        return False
    
        
def add_db(c_dict):
    '''
     database에 update 해야함
     1. db에서 주소에 해당하는 값이 모두 동일하다면
         - 클러스터 번호설정 ==> 그대로 냅두면 되는듯
         - 클러스터 번호가 -1 이라면 max값 설정
     2. db에 해당하는 주소가 동일하지 않다면
         - -1이 아닌 최소값으로 설정
     3. 클러스터번호에 설정하는 주소가 있다
    '''
    print("DB ADD..")
    if len(c_dict) == 0:
        print("NO INPUTS!")
        return
    max_cluster_num = cdq.get_max_clustered()

    for _, addrs in c_dict.items():
        cluster_num_list = sorted(list(cdq.get_cluster_number(addrs)))

        if len(cluster_num_list) == 1:
            if cluster_num_list[0] == -1:
                cluster_num = max_cluster_num + 1
                max_cluster_num = cluster_num
                
                execute_list = list(zip([cluster_num]*len(addrs), addrs))
                                
                start_time = time.time()
                cdq.update_cluster_many(execute_list)
                end_time = time.time()
                setime = end_time - start_time
        else:
            cluster_num = -1
            start_time = time.time()
            for num in cluster_num_list:
                if num != -1:
                    cluster_num = num
                    break
            end_time = time.time()
            for num in cluster_num_list:
                if num != cluster_num:
                    if num != -1:
                        addr = cdq.find_addr_from_cluster_num(num)                        
                        execute_list = list(zip([cluster_num]*len(addr), addr))
                        cdq.update_cluster_many(execute_list)
                        
                    else:
                        addr = find_non_cluster_addr(addrs)
                        if addr == None:
                            continue
                        execute_list = list(zip([cluster_num]*len(addr), addr))
                        cdq.update_cluster_many(execute_list)
                else:
                    addr = addrs
                    execute_list = list(zip([cluster_num]*len(addr), addr))                    
                    cdq.update_cluster_many(execute_list)
                    
    #print("ALL TIME: ", all_time)
    #print("ALL UPDATE TIME: ", all_update_time)
                    


                
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


def multi_input(height):
    cluster_dict = dict()
    txes = rpc_command(height)
    max_cluster_num = 0 
    mi_addr = set()
    all_addr = set()
    for tx in txes:
        tx_indexes = dq.get_txid(tx)
        in_addrs = dq.get_addr_txin(tx_indexes)
        out_addrs = dq.get_addr_txout(tx_indexes)
        
        if is_mi_cond(in_addrs, out_addrs):
            #print(tx, in_addrs)

            ##### update cluster dict #################
            '''
            1. cluster_dict의 key와 item을 돌면서
            2. 현재 만들어진 address_set과 교집합이 있는가? 판단
            3. 교집합이 있다면 그 집합에 넣을것
            4. 교집합이 없다면 cluster 번호를 새로 만들것
            '''
            need_new_cls_num = True
            for key, addr_set in cluster_dict.items():
                if len(addr_set & in_addrs) > 0:
                    cluster_dict[key] = cluster_dict[key].union(in_addrs)
                    need_new_cls_num = False
                    break
            if need_new_cls_num:
                if len(cluster_dict.keys()) == 0:
                    cls_num = 0
                else:
                    cls_num_set = sorted(list(cluster_dict.keys()))
                    cls_num = cls_num_set[-1] + 1
                cluster_dict.update({cls_num:in_addrs})
            ############################################
    return cluster_dict
    
    
def main():
    term = 1000
    start_height = 405650
    end_height =407650
    pool_num = multiprocessing.cpu_count()//2  
    mi_set = set()
    all_set = set()
    stime = time.time()
    try:
        for sheight, eheight in zip(range(start_height, end_height, term), \
                                    range(start_height+term, end_height+term, term)):
            addr_dict = dict()
            max_cluster_num = 0
            cdq.begin_transactions()

            if eheight >= end_height:
                eheight = end_height + 1

            with multiprocessing.Pool(pool_num) as p:
                start_time = time.time()
                result = p.imap(multi_input, range(sheight, eheight))
                end_time = time.time()
                print("MAPEND: ", end_time - start_time)

                for_start_time = time.time()
                for cluster_dict in result:
                    cluster_set = set(cluster_dict.keys())
                    for i in cluster_dict.keys():
                        for j in addr_dict.keys():
                            if len(addr_dict[j] & cluster_dict[i]) > 0:
                                addr_dict[j] = addr_dict[j].union(cluster_dict[i])
                    if len(list(addr_dict.keys())) > 1:
                        if len(addr_dict) == 0:
                            max_cluster_num = 0
                        else:
                            max_cluster_num = sorted(list(addr_dict.keys()))[-1]+1
                    for i in list(cluster_set):
                        addr_dict[max_cluster_num] = \
                        addr_dict.get(max_cluster_num, set()).union(cluster_dict[i])
                        max_cluster_num += 1
                for_end_time = time.time()
                #print(f'reduce TIME:{for_end_time - for_start_time}')
                
                print("REDUCEEND: ", for_end_time - for_start_time)
                start_time = time.time()
                add_db(addr_dict)       
                end_time = time.time()
                print(f'ADD DB TIME:{end_time - start_time}')
            cdq.commit_transactions()

            etime = time.time()
            print('height: {}, time:{}'.format(eheight, etime-stime))
    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected! Commit transactions...')
        cdq.commit_transactions()
                
    finally:
        cdq.commit_transactions()
        cdq.db_close()

            
if __name__=="__main__":
    main()
