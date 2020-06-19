#DB Query
import sqlite3

db_index = '/media/dnlab/0602da39-763c-42b0-b186-f929ac6b3f66/index_620000.db'
db_txhash = '/media/dnlab/0602da39-763c-42b0-b186-f929ac6b3f66/index_620000.db'
index_conn = sqlite3.connect(db_index)
#txhash_conn = sqlite3.connect(db_txhash)
tcur = index_conn.cursor()
#tcur = txhash_conn.cursor()


def get_txid(txhash):
    tx_indexes = None
    try:
        tcur.execute('''SELECT DISTINCT id FROM TxID WHERE txhash = '{}'; '''.format(txhash))
        tx_indexes = tcur.fetchall()
        #print("txhash:", txhash,"tx_indexes", tx_indexes)
        return tx_indexes[0][0]
    except Exception as e:
        print("[ERROR] txhash:", txhash,"tx_indexes:",tx_indexes,"get_txid", e)
        return None


def get_addr_txin(tx_indexes):
    try:
        tcur.execute('''SELECT DISTINCT addr FROM TxIn WHERE tx = '{}'; '''.format(tx_indexes))
        address_list = [str(addr[0]) for addr in tcur.fetchall()]
        return set(address_list)

    except Exception as e:
        print("[ERROR]",tx_indexes, "get_addr_txin", e)
        return None


def get_addr_txout(tx_indexes):
    try:
        tcur.execute('''SELECT DISTINCT addr FROM TxOut WHERE tx = '{}'; '''.format(tx_indexes))
        address_list = [str(addr[0]) for addr in tcur.fetchall()]
        return set(address_list)
    except Exception as e:
        print("get_addr_txout", e)
        return None


def get_max():
    tcur.execute('''SELECT MAX(id) FROM TxID ''')
    return tcur.fetchone()[0]

    
def get_addr_many(start, end):
    tcur.execute(f'''SELECT id, -1 FROM TxID WHERE id BETWEEN {start} AND {end} ORDER BY id ASC;''')
    return list(tcur.fetchall())
    
