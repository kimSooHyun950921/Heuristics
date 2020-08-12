import os
import sys
import time
import decimal
import sqlite3
import multiprocessing
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

       
def get_utxo(tx):
    '''
    utxo인지 아닌지 판단해주는코드
    1. Output Tx 의 비트코인 주소들이 쓰인 TxIn id가 현재 TxOut id보다 큰것이 없는경우
    2. retur utxo의 모든 값들 반환한다.
    '''
    utxo_list = dq.get_utxo(tx)
    if len(utxo_list) > 0:
        return True, utxo_list
    return False, None


def is_first(address, tx):
    '''
    처음나온 주소인지 아닌지 확인해주는 코드
    1. 현재 tx와 처음나온주소가 동일하다면 True를 반환 
    '''
    first_tx = dq.find_tx_first_appeared_address(address)
    if first_tx == tx:
        return True
    return False

    
def is_power_of_ten(address, tx):
    '''
    잔액주소의 판단
    - 소수점아래 4개이상은 있어야한다.
    '''
    value = dq.find_addr_value(address, tx)
    print(value)
    num_of_decimal = abs(decimal.Decimal(str(value)).as_tuple().exponent)
    print(num_of_decimal)
    if num_of_decimal >= 4:
        return True
    return False


def make_addr_set(addr1, addr2):
    if int(addr1) > int(addr2):
        return (addr2, addr1)
    return (addr1, addr2)


def is_otc_cond(in_addrs, out_addrs, tx):
    balance_address = None
    num_of_balance = 0
    if in_addrs == None or out_addrs == None:
        return None
    for out in out_addrs:
        if out in in_addrs:
            continue
        if not is_first(out, tx):
            continue
        if not is_power_of_ten(out, tx):
            continue
        balance_address = out
        num_of_balance += 1

    if balance_address == None:
        return None
    elif num_of_balance >= 2:
        return None
    else:
        return balance_address
        
    return None


def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(in_addrs) <=0:
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


def one_time_change(height):
    txes = rpc_command(height)
    all_addr = list()
    for tx in txes:
        tx_index = dq.get_txid(tx)
        in_addrs = dq.get_addr_txin(tx_index)
        out_addrs = dq.get_addr_txout(tx_index)
        
        if is_mi_cond(in_addrs, out_addrs):
            first_addr = in_addrs.pop()
            while len(in_addrs) > 0:
                second_addr = in_addrs.pop()      
                addr_set = make_addr_set(first_addr, second_addr)
                all_addr.append(addr_set)
                
            is_utxo, utxo_addrs = get_utxo(tx_index)
            if is_utxo:
                #print("UTXO:", utxo_addrs)
                otc_addr = is_otc_cond(in_addrs, out_addrs, tx_index)
                if otc_addr is not None:
                    #print("OTC:", otc_addr)
                    
                    all_addr.append(make_addr_set(first_addr, otc_addr))
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
                result = p.imap(one_time_change, range(sheight, eheight))
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

    args = parser.parse_args()
    main(args)