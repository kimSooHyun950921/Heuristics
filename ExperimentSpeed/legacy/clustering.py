import csv
import pickle
import time
import pandas as pd
import numpy as np
import unionfind as uf
import test_cluster_db_query as cdq


def read_csv(csv_file):
    df = pd.read_csv(csv_file, header=None)
    df = df.drop_duplicates()
    first = df[0].to_list()
    second = df[1].to_list()
    return list(zip(first, second))
        

def main(args):
    count = 0
    stime = time.time()
    csv_list = read_csv(args.csv_file)
    etime = time.time()
    print("DEBUG:", csv_list[0], etime-stime)

    print("START UNION FIND")
    stime = time.time()
    u = uf.UnionFind(int(cdq.get_max_address())+1)
    #u = uf.UnionFind(int(100000000))
    etime = time.time()
    print(f"MAKE ADDRESS END, TOTAL TIME:{etime - stime}")
    
    
    for first, second in csv_list:
        u.union(first, second)
        if count % 10000000 == 0:
            etime = time.time()
            print(f"COUNT {count} END, TOTAL TIME: {etime - stime}")
        count += 1
    etime = time.time()
    print(f"UNION FIND END TOTAL TIME:{etime - stime}") 
    
    del u.rank
    print("START CLUSTERING")
    stime = time.time()
    count = 0
    addr_list = list()
    for index, cluster in enumerate(u.par):
        addr_list.append((u.find(cluster), str(index)))
        if count % 10000 == 0:
            cdq.begin_transactions()
            cdq.update_cluster_many(addr_list)
            cdq.commit_transactions()
            etime = time.time()
            print(f"COUNT {count} END, TOTAL TIME: {etime - stime}, {addr_list[len(addr_list)-1]}")
            del addr_list
            addr_list = list()
        count += 1
    etime = time.time()
    del u.par
    
    print(f"CLUSTERING END:{etime - stime}")    
    #with open('./TESTDB/data.pickle', 'wb') as f:
    #    pickle.dump(addr_list, f)
    #print("pickle load start")
    #with open('./TESTDB/data.pickle', 'rb') as f:
    #    data = pickle.load(f)
    
    #print("update cluster ")
    #stime = time.time()
    #cdq.begin_transactions()
    #cdq.update_cluster_many(data)
    #cdq.commit_transactions()
    #etime = time.time()
    #print("update cluster END:", etime - stime)
    


if __name__ ==  "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--csv_file', '-c',
                        type=str,
                        default='./TESTDB/TESTall.csv',
                        help='an integer for the accumulator')
    args = parser.parse_args()
    main(args)
    