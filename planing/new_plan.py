# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from ga_numpy import GeneticAlgorithm as ga
import numpy_indexed as npi
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine


##############################
city = 24 #  'استانبول'
start_time = 480
end_time = 1260

coh_fultm = 0.8
coh_lntm  = 0.0
coh_cnt   = 0.2
coh_dffRqTime  = 0.0
##############################

USER = 'planuser'
PASSWORD = '1qaz!QAZ'
HOST = 'localhost'
PORT = '5432'
NAME = 'planing'
db_connection = "postgresql://{}:{}@{}:{}/{}".format(USER,
                                                         PASSWORD,
                                                         HOST,
                                                         PORT,
                                                         NAME
                                                        )
engine = create_engine(db_connection)
df = pd.read_sql_query('SELECT * FROM	plan_attractions',con=engine)
df = df.drop(['image'], axis=1)

df_city = df[df['city_id']==city]

dist_mat_query = ''' select 
                         origin_id as orgin
                        ,destination_id as dist
                        ,len_time as len
                     from 
                       plan_distance_mat
                     where
                       origin_id in 
                       (select id from plan_attractions
                        where city_id = {0})
                       '''.format(city)
             
dist_df = pd.read_sql_query(dist_mat_query
                          ,con=engine)

dist_mat = pd.pivot_table(dist_df,                           
                          index=['orgin'],
                          columns=['dist'], 
                          values='len', 
                          aggfunc=np.sum)

vst_time_from = df_city['vis_time_from'] 
vst_time_to = df_city['vis_time_to']
points = df_city['id']
rq_time = df_city['rq_time']

meta_data = np.array([points, rq_time], dtype=int)

pln_gene1 = np.array([points, 
                      rq_time, 
                      ], dtype=int).T
pln_gene2 = np.array([np.flip(points), 
                      np.flip(rq_time), 
                     ], dtype=int).T						  
							  
def cost_fulltime(individual, meta_data):
    plan = individual
    len_pln = len(plan)
    edge = len_pln - 1   
    all_dist = 0
    all_duration = np.sum(plan[:,1])
    pln_pnt = plan[:,0]
    for i,orig in enumerate(pln_pnt):    
        if i<edge:
            all_dist += dist_mat.loc[orig , pln_pnt[i+1]]
    plan_lenght = all_dist + all_duration  
    cost = np.abs((start_time + plan_lenght) - end_time) / 1440.0     
      
    return cost

def cost_lentime(individual, all_dist, all_duration ):         
    cost = all_dist / (all_duration + all_dist)
      
    return cost
	
def cost_count(individual, meta_data):
    plan = individual
    len_pln = len(plan)
    len_points = len(meta_data[0])
    cost = np.abs(len_points-len_pln) / len_points
    
    return cost

def cost_rqTime(individual, meta_data):
    plan = individual
   
    t = np.concatenate((plan, meta_data.T))
    _, t_max = npi.group_by(t[:,0]).max(t)
    _, t_min = npi.group_by(t[:,0]).min(t)
    t = (t_max - t_min)/t_max
    cost = np.sum(t[:,1]) / len(plan)   
    
    return cost

def fitness(individual, meta_data):    
    _, individual = npi.group_by(individual[:,0]).max(individual)
    
    len_pln = len(individual)
    edge = len_pln - 1   
    pln_pnt = individual[:,0]
    len_points = len(points)
    all_duration = np.sum(individual[:,1])
    all_dist = 0
    for i,orig in enumerate(pln_pnt):    
        if i<edge:
            all_dist += dist_mat.loc[orig , pln_pnt[i+1]]
    

    cost_fultm = cost_fulltime(individual, meta_data)
    cost_lntm  = cost_lentime(individual, all_dist, all_duration)
    cost_cnt   = cost_count(individual, meta_data)
    cost_diff_rqTime = cost_rqTime(individual, meta_data)
#    print(len_cost, cnt_cost, diff_rqTime_cost)
    cost =((coh_fultm*cost_fultm) + 
           (coh_lntm*cost_lntm) + 
           (coh_cnt*cost_cnt) + 
           (coh_dffRqTime*cost_diff_rqTime)
           )
#    print(cost)
    
    return cost

ga = ga(seed_data=pln_gene1,
        meta_data=meta_data,
        population_size=50,
        generations=100,
        crossover_probability=0.8,
        mutation_probability=0.2,
        elitism=True,
        by_parent=False,
        maximise_fitness=False)	
ga.fitness_function = fitness

ga.run()   

sol_fitness, sol_df = ga.best_individual()

def lenght(individual, meta_data):
    plan = individual
    len_pln = len(plan)
    edge = len_pln - 1   
    all_dist = 0
    all_duration = np.sum(plan[:,1])
    pln_pnt = plan[:,0]
    for i,orig in enumerate(pln_pnt):    
        if i<edge:
            all_dist += dist_mat.loc[orig , pln_pnt[i+1]]
    
    return all_duration + all_dist

len_pln = len(sol_df)
edge = len_pln - 1   
pln_pnt = sol_df[:,0]
len_points = len(points)
all_duration = np.sum(sol_df[:,1])
all_dist = lenght(sol_df, meta_data)
all_lenght = all_dist + all_duration
    
cost_fultm = cost_fulltime(sol_df, meta_data)
cost_lntm  = cost_lentime(sol_df, all_dist, all_duration)
cost_cnt   = cost_count(sol_df, meta_data)
cost_diff_rqTime = cost_rqTime(sol_df, meta_data)
diff_full_time = (start_time + all_lenght) - end_time





