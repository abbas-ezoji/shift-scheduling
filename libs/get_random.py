# -*- coding: utf-8 -*-
import random
import copy
import pyodbc
import pandas as pd

def get_rollet_wheel(prob_list, rank_list):
    cd_prob = copy.deepcopy(prob_list)
    p = random.random()
    for i in range(len(rank_list)):        
        cd_prob[i] =  sum(prob_list[:i+1]) if prob_list[i] else 0    
    
    r = -1    
    for i in range(len(cd_prob)):    
        if p < cd_prob[i]:
            r = rank_list[i]
            break
    return r

def get_best_first_rank(conn_str, query_gene_last):    
    sql_conn = pyodbc.connect(conn_str)        
    last_df = pd.read_sql(query_gene_last, sql_conn)
    
    min_diff = min(last_df['life_cycle'])
    last_df['life_cycle'] = last_df['life_cycle'] / min_diff
    
    last_df['point'] = ( last_df['life_cycle']
                          / 
                         (last_df['Rank'] * 
                          last_df['Cost'] * 
                          (last_df['UsedParentCount'] + 1 )                      
                         )
                        )
    sum_point = sum(last_df['point'])
    last_df['point'] = last_df['point'] / sum_point
    rank_list = last_df['Rank']
    prob_list = last_df['point']
    
    return get_rollet_wheel(prob_list,rank_list)


