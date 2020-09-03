import sys
import time
import sqlite3
import numpy as np
import multiprocessing
from test_secret import rpc_user, rpc_password
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

class ClusterDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()
        #db_path = '/home/dnlab/Jupyter-Bitcoin/Heuristics/ExperimentSpeed/TESTDB/test40man-test.db'
        #db_path = '/home/dnlab/Jupyter-Bitcoin/Heuristics/ExperimentSpeed/TESTDB/test1.db'
        #self.conn = sqlite3.self.connect(db_path)
        #self.cur = self.conn.self.cursor()
         
    def create_cluster_table(self):
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Cluster (
                         address TEXT PRIMARY KEY,
                         number INTEGER NOT NULL);''')


    def create_debug_table(self):
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Debug (
                         address TEXT PRIMARY KEY,
                         number INTEGER NOT NULL);''')


    def insert_cluster(self, address, number):
        self.cur.execute('''INSERT OR IGNORE INTO Cluster (
                           address, number) VALUES (?, ?);
                    ''', (address, number))


    def insert_cluster_debug(self, address, number):
        self.cur.execute('''INSERT OR IGNORE INTO Debug (
                           address, number) VALUES (?, ?);
                    ''', (address, number))


    def insert_cluster_many(self, addr_list):
        self.cur.executemany('''INSERT OR IGNORE INTO Cluster VALUES (?, ?)''', addr_list)


    def insert_cluster_many_debug(self, addr_list):
        self.cur.executemany('''INSERT OR IGNORE INTO Cluster VALUES (?, ?)''', addr_list)


    def update_cluster_many(self, addr_list):
        index = 0
        try:
            while index < len(addr_list):
                sample_list = addr_list[index: index+10000]
                self.cur.executemany('''UPDATE Cluster SET number=? WHERE address=?
                                ''', sample_list)
                index += 10000
            return True
        except sqlite3.Error as error:
            print(error)
            return False

    
    def count_cluster_address(self, number):
        try:
            self.cur.execute(f'''select distinct count(address) from Cluster
                                where number = {number};''')
            return self.cur.fetchone()[0]
        except Exception as e:
            print("[ERROR]:",e)
            return None
            
            
    def update_cluster_many_debug(self, addr_list):
        index = 0
        try:
            while index < len(addr_list):
                sample_list = addr_list[index: index+10000]
                self.cur.executemany('''UPDATE Debug SET number=? WHERE address=?
                                ''', sample_list)
                index += 10000
            return True
        except sqlite3.Error as error:
            print(error)
            return False


    def find_addr_from_cluster_num(self, num):
        '''클러스터 번호가 num인 모든 주소를 가져옴
           '''
        self.cur.execute('''SELECT address FROM Cluster WHERE number = {}'''.format(num))
        addr_list = [addr[0] for addr in self.cur.fetchall()]
        return addr_list


    def begin_transactions(self):
        try:
            self.cur.execute('BEGIN TRANSACTION;')

        except sqlite3.OperationalError as e:
            print("Error Ocself.cur!", e)


    def commit_transactions(self):
        try:
            #self.conn.commit()
            self.cur.execute('COMMIT;')
            print('commit complete')
        except sqlite3.OperationalError as e:
            print("Error Ocself.cur!", e)


    def get_min_all_cluster(self, addrss):
        self.cur.execute(f'''SELECT MIN(number) FROM Cluster \
                             WHERE address IN ('{",".join(addrss)}')'''.replace('\'',''))
        return self.cur.fetchone()[0]


    def get_min_clustered(self, addrss):
        self.cur.execute(f'''SELECT MIN(number) FROM Cluster WHERE address IN ('{",".join(addrss)}') \
                             and number > -1'''.replace('\'',''))
        return self.cur.fetchone()[0]


    def get_max_clustered(self):
        self.cur.execute(f'''SELECT MAX(number) FROM Cluster''')
        return self.cur.fetchone()[0]


    def get_max_address(self):
        self.cur.execute(f'''SELECT count(address) FROM Cluster''')
        return self.cur.fetchone()[0]


    def get_cluster_number(self, addrss):
        try:
            self.cur.execute(f'''SELECT number FROM Cluster \
                                WHERE address IN ('{",".join(addrss)}')'''.replace('\'',''))
            cls_num = []
            for addr_tuple in self.cur.fetchall():
                cls_num.append(addr_tuple[0])
            return set(cls_num)
        except sqlite3.DatabaseError as e:
            print("[ERROR]: get_cluster_number", addrss, e)
            

    def get_all_cluster(self):
        try:
            self.cur.execute('''SELECT DISTINCT * FROM Cluster; ''')
            addr_dict = dict()
            for addr in self.cur.fetchall():
                addr_dict.update({addr[0]:addr[1]})
            return addr_dict
        except Exception as e:
            return None

    def get_tag_from_addr(self, addr_list):
        try:
            self.cur.execute(f'''SELECT DISTINCT ClusterName FROM Tag \
                                 WHERE id IN ('{",".join(addr_list)}')'''.replace('\'',''))
            
            addr_list = {ClusterName[0] for ClusterName in self.cur.fetchall()}
            return addr_list
        except Exception as e:
            print("[ERROR]: ", e)
            return None
        
        
    def get_Category_from_addr(self, addr_list):
        try:
            self.cur.execute(f'''SELECT DISTINCT Category FROM Tag \
                                 WHERE id IN ('{",".join(addr_list)}')'''.replace('\'',''))
            
            addr_list = {Category[0] for Category in self.cur.fetchall()}
            return addr_list
        except Exception as e:
            print("[ERROR]: ", e)
            return None
        
        
    def db_close(self):
        self.conn.close()
