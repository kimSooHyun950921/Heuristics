import sys
sys.path.append('/home/dnlab/Jupyter-Bitcoin/Heuristics/ExperimentSpeed/')
import pandas as pd
import test_cluster_db_query as cdq
import test_db_query as dq
import csv
import time

#root_addr_df = pd.read_csv('/home/dnlab/DataHDD/tagdata/tag_59man.csv')[['ClusterName', 'Category', 'address','id']]
#root_addr_df['addr'] = root_addr_df['Address'].map(lambda x: dq.get_addrid_from_addr(x))
#root_addr_df = root_addr_df.dropna(axis=0)
#root_addr_df.id = root_addr_df.id.astype('int32')

print("UPLOAD MEMORY ")
mi_df= pd.read_csv('/home/dnlab/DataHDD/otc.csv')
data_condition =mi_df['number'] != -1
mi_df = mi_df[data_condition]
mi_df= mi_df.rename(columns={"address": "addr"})
mi_group = mi_df.groupby('number')


cluster_list = []
count = 0
print("START TAGGING")
stime = time.time()
with open('/home/dnlab/DataHDD/otc_cluster.csv', 'w', newline='') as csvfile:
    #fieldnames = ['group', 'Category','num_in_tx','num_out_tx', \
    #              'in_value', 'out_value', 'balance', \
    #              'smallest_addr', 'ClusterName', 'len']
    fieldnames = ['group', 'smallest_addr', 'len']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for cluster_number, addr_group in mi_group:
        #addr_dict = {'group':cluster_number, 'Category':None, 'num_in_tx':0, \
        #             'num_out_tx':0, 'in_value':0, 'out_value':0, 'balance':0,\
        #             'smallest_addr':addr_group.reset_index().iloc[0]['addr'],\
        #             'ClusterName':None,'len': len(addr_group)}
        if len(addr_group) <= 10:
            continue
        addr_dict = {'group':cluster_number, 'smallest_addr':addr_group['addr'].iloc[0], 'len': len(addr_group)}
        #addr_list = addr_group['addr'].to_list()
        #if len(addr_list) > 10000:
        #    print("query start", len(addr_list))
            
        #addr_dict['num_in_tx'] = dq.count_all_tx_in(addr_list)
        #addr_dict['num_out_tx'] = dq.count_all_tx_out(addr_list)
        #addr_dict['in_value'] = dq.sum_all_invalue(addr_list)
        #addr_dict['out_value'] = dq.sum_all_outvalue(addr_list)
        #addr_dict['balance'] = addr_dict['out_value'] - addr_dict['in_value']
        
        #if len(addr_list) > 10000:
        #    print("join_start:", len(addr_list))
        #join_df = pd.merge(addr_group, root_addr_df,how = 'inner', on=['addr'])

        #category = set(join_df['Category'].to_list())
        #addr_dict['Category'] = ','.join(list(category))

        #cluster_name = set(join_df['ClusterName'].to_list())
        #addr_dict['ClusterName'] = ','.join(list(cluster_name)) 

        writer.writerow(addr_dict)
        if count % 1000000 == 0:
            print(count, time.time() - stime)
        count += 1

