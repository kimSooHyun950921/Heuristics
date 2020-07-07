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
    if len(out_addrs) == 1 and len(in_addrs) >= 2:
        return True
    return False
    

def get_cluster_num(addrs, max_cluster_num):
    cls_num = -1
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
    
    
def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(in_addrs) >= 2 and len(out_addrs) == 1:
        return True
    return False


def find_non_cluster_addr(addrs):
    non_cluster_addr_list = []
    for addr in addrs:
        cluster_num = cdq.get_cluster_number([addr]).pop()
        if cluster_num == -1:
            non_cluster_addr_list.append(cluster_num)
    return non_cluster_addr_list
            
    
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
    if len(c_dict) == 0:
        print("NO INPUTS!")
        return
    max_cluster_num = cdq.get_max_clustered()
    print("[ADD_DB DEBUG - max_cluster_num]", max_cluster_num)
    for _, addrs in c_dict.items():
        print("[ADD_DB DEBUG - addrs]",addrs)
        cluster_num_list = sorted(list(cdq.get_cluster_number(addrs)))
        print("[ADD_DB DEBUG - cluster_num_list]", cluster_num_list)
        if len(cluster_num_list) == 1:
            if cluster_num_list[0] == -1:
                cluster_num = max_cluster_num + 1
                max_cluster_num = cluster_num
                execute_list = list(zip([cluster_num]*len(addrs), addrs))
                print("[ADD_DB DEBUG - first execute_list]", execute_list)
                cdq.update_cluster_many(execute_list)
        else:
            cluster_num = -1
            for num in cluster_num_list:
                if num != -1:
                    cluster_num = num
                    break
            print("[ADD_DB DEBUG - cluster_num, cluster_num_list]", cluster_num, cluster_num_list)
            for num in cluster_num_list:
                if num != cluster_num:
                    if num != -1:
                        addr = cdq.find_addr_from_cluster_num(num)
                        print("[ADD_DB DEBUG -cluster_num여러개, -1아닌경우addr]", addr)
                    else:
                        addr = find_non_cluster_addr(addrs)
                        print("[ADD_DB DEBUG -cluster_num여러개, -1인경우addr]", addr)
                else:
                    addr = addrs
                    
                execute_list = list(zip([cluster_num]*len(addr), addr))
                print("[ADD_DB DEBUG - second execute_list]", execute_list)
                cdq.update_cluster_many(execute_list)
            
             
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
    for tx in txes:
        tx_indexes = dq.get_txid(tx)
        in_addrs = dq.get_addr_txin(tx_indexes)
        out_addrs = dq.get_addr_txout(tx_indexes)
        print("[MULTIINPUT DEBUG - check inputs numof in, out addrs]",len(in_addrs), len(out_addrs))
        if is_mi_cond(in_addrs, out_addrs):
            print("[MULTIINPUT DEBUG - is_mi_cond in_addrs]", len(in_addrs), in_addrs)
            print("[MULTIINPUT DEBUG - is_mi_cond, out_addrs]", len(out_addrs))
            ##### update cluster dict #################
            '''
            1. cluster_dict의 key와 item을 돌면서
            2. 현재 만들어진 address_set과 교집합이 있는가? 판단
            3. 교집합이 있다면 그 집합에 넣을것
            4. 교집합이 없다면 cluster 번호를 새로 만들것
            '''
            need_new_cls_num = True
            for key, addr_set in cluster_dict.items():
                print("[MULTIINPUT DEBUG - loop addr_set]",key, addr_set)
                if len(addr_set & in_addrs) > 0:
                    cluster_dict[key].union(in_addrs)
                    print("[MULTIINPUT DEBUG - after union cluster_dict]", cluster_dict)
                    need_new_cls_num = False
                    break
            if need_new_cls_num:
                if len(cluster_dict.keys()) == 0:
                    cls_num = 0
                else:
                    cls_num_set = sorted(list(cluster_dict.keys()))
                    print("[MULTIINPUT DEBUG - sorted cls_num_set]", cls_num_set)
                    cls_num = set(cls_num_set).pop() + 1
                    print("[MULTIINPUT DEBUG - cls_num]", cls_num)
                cluster_dict.update({cls_num:in_addrs})
            ############################################    
    return cluster_dict
    
    
def main():
    term = 10000
    start_height = 0
    end_height = dq.get_max_height()
    pool_num = multiprocessing.cpu_count()//2  
    addr_dict = dict()
    max_cluster_num = 0
    print("CLSUTER TABLE MADE")
    time.sleep(5)
    stime = time.time()
    try:
        for sheight in range(0, end_height):
            cdq.begin_transactions()
            cluster_dict = multi_input(sheight)
            print("[MAIN DEBUG - cluster_dict]", cluster_dict)
            cluster_set = set(cluster_dict.keys())
            # 공통이 있는지 찾아 공통주소가 있으면 합치기
            for i in cluster_dict.keys():
                for j in addr_dict.keys():
                    if len(addr_dict[j] & cluster_dict[i]) > 0:
                        addr_dict[j] = addr_dict[j].union(cluster_dict[i])
                        cluster_set = cluster_set - {i}
            print("[MAIN DEBUG - first addr_dict]", addr_dict)
            # 공통된것이 없는경우 마지막에 붙여넣기
            if len(list(addr_dict.keys())) > 1:
                max_cluster_num = sorted(list(addr_dict.keys())).pop()+1
            for i in list(cluster_set):
                addr_dict[max_cluster_num] = \
                addr_dict.get(max_cluster_num, set()).union(cluster_dict[i])
                max_cluster_num += 1
            print("[MAIN DEBUG - second addr_dict]", addr_dict)
            add_db(addr_dict)                                 
            cdq.commit_transactions()

            etime = time.time()
            print('height: {}, time:{}'.format(sheight, etime-stime))
    except KeyboardInterrupt:
        print('Keyboard Interrupt Detected! Commit transactions...')
        cdq.commit_transactions()
                
    finally:
        cdq.commit_transactions()
        cdq.db_close()

            
if __name__=="__main__":
    main()