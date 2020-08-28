import pandas as pd
import test_db_query as dq 

def read_answer(vasp_file):
    answer_sheet = pd.read_csv(vasp_file, names=['Address','Balance','Transaction','NaN'])
    answer_sheet = answer_sheet['Address'].to_list()
    
    return answer_sheet

def read_data(data_file):
    data_sheet = pd.read_csv(data_file)
    data_sheet = data_sheet['address'].to_list()
    return data_sheet

def mapping_data(data_sheet):
    for data in data_sheet:
        txhash = dq.get_txhash_from_txid(int(data))
        yield txhash

def main(vasp, data):
    ''' 정답지 읽어들이기
        데이터 읽어들이기 
        매핑하기
        정답비교
        정답지에도 있고 데이터에도 있는것: True Positive
        정답지에는 있는데 데이터에는 없는것 True Negative
        데이터에는 있는데 정답지에는 없는것: False Posivie
    ''' 
    tp = 0
    fp = 0
    tn = 0
    
    answer_sheet = read_answer(vasp)
    data_sheet = read_data(data)
    count = 0
    print("START")
    for txhash in mapping_data(data_sheet):
        if str(txhash) in answer_sheet:
            tp += 1
            answer_sheet.remove(txhash)
        else:
            fp += 1
        if count % 10000 == 0:
            print(tp, fp)
        count += 1
            
    tn = len(answer_sheet)        
    print(data, ": TP:", tp,"TN:",tn,"FP:",fp)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='multi-input vasp accuracy.')
    parser.add_argument('--vasp','-v', type=str,
                        help='insert answer vasp file')
    parser.add_argument('--data','-d',type=str,
                        help='insert multi-input result file')

    args = parser.parse_args()
    main(args.vasp, args.data)
