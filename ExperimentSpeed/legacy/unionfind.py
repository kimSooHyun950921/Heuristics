import pandas as pd
import clustering

class UnionFind:
    
    def __init__(self, n):
        result = self.init(n)
        self.par = result[0]
        self.rank = result[1]
    
    
    def init(self, n):
        par = []
        rank = []
        for i in range(0, n+1):
            par.append(-1)
            rank.append( 0)
        return par, rank


    def find(self, x):
        if self.par[x] == -1:
            return x
        elif self.par[x] == x:
            return x
        else:
            return self.find(self.par[x])

        
    def union(self, a, b):
        a = self.find(a)
        b = self.find(b)
        if a != -1 and b != -1 and a == b:
            return 

        if self.rank[a] < self.rank[b]:
            self.par[a] = self.find(b)
        else:
            self.par[b] = self.find(a)
            
            if self.rank[a] == self.rank[b]:
                self.rank[a] += 1
                if self.par[a] == -1:
                    self.par[a] = a

                
if __name__ == "__main__":
    import random 
    import time
    union_list = clustering.read_csv('./TESTDB/TESTman.csv')
    #[(1,2), (8,3), (7,4),(5,9),(0,0),(6,8),(7,5),(8,7),(3,9),(9,4)]
    validation_list = []
    stime = time.time()
    u = UnionFind(100000)
    for first, second in union_list:
    #for i in range(0, 10):
        #first =  random.randrange(0,10)
        #second = random.randrange(0,10)
        print(f"UNION {first} AND {second}")
        u.union(first, second)      
        validation_list.append((first, second))
        
    etime = time.time()
    result_list = dict()
    for index, value in enumerate(u.par):
        result_list[u.find(value)] = result_list.get(u.find(value),{u.find(value)}).union({index})
    print(result_list)
    
    for first, second in validation_list:
        if u.find(first) == u.find(second):
            continue
        else:
            print("False", first, second)
            break
    
    print("totaltime:", etime-stime)