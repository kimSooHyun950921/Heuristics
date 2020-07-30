import pickle
import time
import pandas as pd
import numpy as np
import test_cluster_db_query as cdq

def grouping_csv():
    df = pd.read_csv('./TESTDB/TEST2.csv',header=None)
    df = df.drop_duplicates()
    grp = df.groupby([0])
    return grp
    

def cluster_from_grp(grp):
    count = 0
    all_list = []
    stime = time.time()
    for name, group in grp:
        all_list.append((str(name), count))
        for k in group[1].to_list():
            all_list.append((str(k), count))
        if count % 1000000 == 0:
            etime = time.time()
            print(f"GROUP: {count} END, Time: {etime-stime}, {all_list[-1]}")
        count += 1  
    return all_list

def main():
    '''print("read csv, and start grouping!")
    stime = time.time()
    grp = grouping_csv()
    etime = time.time()
    load_csv_time = etime - stime
    print("grouping END: ", etime - stime)
    
    print("cluster from group")
    stime = time.time()
    all_list = cluster_from_grp(grp)
    etime = time.time()
    cluster_time = etime - stime
    print("clustering END:", etime - stime)
    print("pickle write start")
    with open('./TESTDB/data.pickle', 'wb') as f:
        pickle.dump(all_list, f, pickle.HIGHEST_PROTOCOL)
    '''
    print("pickle load start")
    with open('./TESTDB/data.pickle', 'rb') as f:
        data = pickle.load(f)
    
    print("update cluster ")
    stime = time.time()
    cdq.begin_transactions()
    cdq.update_cluster_many(data)
    cdq.commit_transactions()
    etime = time.time()
    db_write_time = etime - stime
    print("update cluster END:", etime - stime)
    
    print(f"TOTAL TIME: {load_csv_time + cluster_time + db_write_time}")
    
if __name__ ==  "__main__":
    main()
    
