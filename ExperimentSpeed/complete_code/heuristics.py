import test_db_query as dq
from test_secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

rpc_ip = '127.0.0.1'
rpc_port = '8332'
timeout = 300


def get_rpc():
    return AuthServiceProxy(f'http://{rpc_user}:{rpc_password}@{rpc_ip}:{rpc_port}', timeout=timeout)


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


def is_mi_cond(in_addrs, out_addrs):
    if in_addrs == None or out_addrs == None:
        return False
    if len(in_addrs) <= 0: 
        return False
    return True


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