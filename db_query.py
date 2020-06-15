#DB Query
import sqlite3

db_index = '/home/dnlab/BitcoinBlockSampler/index.db'
db_txhash = '/media/dnlab/0602da39-763c-42b0-b186-f929ac6b3f66/200529/txhash.db'
index_conn = sqlite3.connect(db_index)
txhash_conn = sqlite3.connect(db_txhash)
icur = index_conn.cursor()
tcur = txhash_conn.cursor()


def get_txid(txhash):
    try:
        icur.execute('''SELECT DISTINCT id FROM TxID WHERE txhash = '{}'; '''.format(txhash))
        tx_indexes = icur.fetchall()
        return tx_indexes[0][0]

    except Exception as e:
        return None


def get_addr_txin(tx_indexes):
    try:
        tcur.execute('''SELECT DISTINCT addr FROM TxIn WHERE tx = '{}'; '''.format(tx_indexes))
        address_list = [str(addr[0]) for addr in tcur.fetchall()]
        return set(address_list)

    except Exception as e:
        return None


def get_addr_txout(tx_indexes):
    try:
        tcur.execute('''SELECT DISTINCT addr FROM TxOut WHERE tx = '{}'; '''.format(tx_indexes))
        address_list = [str(addr[0]) for addr in tcur.fetchall()]
        return set(address_list)
    except Exception as e:
        return None


def get_max():
    icur.execute('''SELECT MAX(id) FROM TxID ''')
    return icur.fetchone()[0]

    
def get_addr_many(start, end):
    icur.execute(f'''SELECT id, -1 FROM TxID WHERE id BETWEEN {start} AND {end} ORDER BY id ASC;''')
    print(len(list(icur.fetchall())))
    return list(icur.fetchall())
    
