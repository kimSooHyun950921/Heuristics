import sys
sys.path.append('/home/dnlab/Jupyter-Bitcoin/Heuristics/ExperimentSpeed/')
import pandas as pd
from test_cluster_db_query import ClusterDB
import test_db_query as dq
import csv
import time
cdq = ClusterDB('/home/dnlab/DataSSD/dbv3cluster.db')

df = pd.read_csv('/home/dnlab/DataHDD/tag_v2.csv')
df = df[df['len'] > 500]

clt_list = []
count = 0
for addr_group in df['group'].to_list():

    s_time = time.time()
    addr_list = cdq.find_addr_from_cluster_num(addr_group)
    cluster_list = list(cdq.get_tag_from_addr(addr_list))
    
    #if len(addr_list) > 10000:
    count += 1
    cls_list .append( ",".join(cluster_list))
    if count % 10 == 0:
        print(count, cat_list[-1], time.time()-s_time)


cat_list = []
count = 0
for addr_group in df['group'].to_list():

    s_time = time.time()
    addr_list = cdq.find_addr_from_cluster_num(addr_group)
    cluster_list = list(cdq.get_Category_from_addr(addr_list))
    
    #if len(addr_list) > 10000:
    count += 1
    cat_list .append( ",".join(cluster_list))
    if count % 10 == 0:
        print(count, cat_list[-1], time.time()-s_time)


df['ClusterName'] = df['group'].map(lambda x: get_addr_from_tag(x))
df['Category'] = df['group'].map(lambda x: get_addr_from_tag(x))
df['Year'] = 2020

