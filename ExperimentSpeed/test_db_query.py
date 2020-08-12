#DB Query
import sqlite3

db_index = '/home/dnlab/DataSSD/dbv3-index.db'
db_core = '/home/dnlab/DataSSD/dbv3-core.db'

index_conn = sqlite3.connect(db_index)
core_conn = sqlite3.connect(db_core)
tcur = index_conn.cursor()
ccur = core_conn.cursor()

def get_utxo(tx):
    try:
        ccur.execute('''SELECT TxOut.addr AS addr
                        FROM TxOut
                        WHERE NOT EXISTS (SELECT *
                                          FROM TxIn
                                          WHERE TxIn.ptx = TxOut.tx AND
                                                TxIn.pn = TxOut.n) AND
                        TxOut.tx == {}
                        GROUP BY tx, n;'''.format(tx))
        result = ccur.fetchall()
        utxo_addr = [addr[0] for addr in result]
        return utxo_addr
    except Exception as e:
        print("[ERROR] tx:", tx,"error:", e)
        return []
    
    
def find_tx_first_appeared_address(addr):
    #select distinct min(tx) from TxIn where addr=307960014
    query = f'''select TxOut.tx, BlkTx.blk from TxOut
               INNER JOIN BlkTx ON BlkTx.tx = TxOut.tx
               where Txout.addr == {addr}
               LIMIT 1;'''
    ccur.execute(query)
    return ccur.fetchone()[0]


def find_addr_value(addr, tx):
    ccur.execute(f'''select distinct btc from TxOut where addr={addr} and tx={tx}''')
    return ccur.fetchone()[0]
    
    
def get_txhash_from_txid(txid):
    try:
        tcur.execute('''select addr from AddrID where id = {};'''.format(txid))
        tx_hash = tcur.fetchone()
        return tx_hash[0]
    except Exception as e:
        print("[ERROR] txid:",txid,"error:",e)
        

def get_addrid_from_addr(addr):
    try:
        tcur.execute('''select id from AddrID where addr = "{}";'''.format(addr))
        tx_hash = tcur.fetchone()
        return int(tx_hash[0])
    except Exception as e:
        print("[ERROR] error:",e)


def get_txid(txhash):
    tx_indexes = None
    try:
        tcur.execute('''SELECT DISTINCT id FROM TxID WHERE txid = '{}'; '''.format(txhash))
        tx_indexes = tcur.fetchall()
        #print("txhash:", txhash,"tx_indexes", tx_indexes)
        return tx_indexes[0][0]
    except Exception as e:
        print("[ERROR] txhash:", txhash,"tx_indexes:",tx_indexes,"get_txid", e)
        return None


def get_addr_txin(tx_indexes):
    try:
        query = '''SELECT TxOut.addr AS addr
                   FROM TxIn
                   INNER JOIN TxOut ON TxIn.ptx = TxOut.tx AND TxIn.pn = TxOut.n
                   WHERE TxIn.tx == {};'''.format(tx_indexes)
        ccur.execute(query)
        address_list = [str(addr[0]) for addr in ccur.fetchall()]
        return set(address_list)

    except Exception as e:
        print("[ERROR]",tx_indexes, "get_addr_txin", e)
        return None


def get_addr_txout(tx_indexes):
    try:
        ccur.execute('''SELECT DISTINCT addr FROM TxOut WHERE tx = '{}'; '''.format(tx_indexes))
        address_list = [str(addr[0]) for addr in ccur.fetchall()]
        return set(address_list)
    except Exception as e:
        print("get_addr_txout", e)
        return None


def get_max():
    tcur.execute('''SELECT MAX(id) FROM TxID ''')
    return tcur.fetchone()[0]


def get_max_height():
    tcur.execute('''SELECT MAX(id) FROM BlkID; ''')
    return tcur.fetchone()[0]


def get_max_address():
    tcur.execute('''select MAX(id) from AddrID; ''')
    return tcur.fetchone()[0]


def get_addr_many(start, end):
    tcur.execute(f'''SELECT id, -1 FROM AddrID WHERE id BETWEEN {start} AND {end} ORDER BY id ASC;''')
    return list(tcur.fetchall())
    
