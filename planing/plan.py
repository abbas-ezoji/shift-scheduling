import pandas as pd
import numpy as np
from ga_numpy import GeneticAlgorithm as ga
import numpy_indexed as npi
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine

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
    
df_kelar = df[df['city']=='کلاردشت']

dist_df = pd.read_csv('m.csv')

dist_mat = pd.pivot_table(dist_df,                           
                          index=['orgin'],
                          columns=['dist'], 
                          values='len', 
                          aggfunc=np.sum)

vst_time_from = df_kelar['vis_time_from'] 
vst_time_to = df_kelar['vis_time_to']
points = df_kelar['id']
rq_time = df_kelar['rq_time']

meta_data = [points, rq_time]

pln_gene1 = np.array([points, 
                      rq_time, 
                      ], dtype=int).T
pln_gene2 = np.array([np.flip(points), 
                      np.flip(rq_time), 
                     ], dtype=int).T						  
							  
def lenght_cost(individual, meta_data):
    plan = individual
    l = len(plan)
    start_tiem = 480
    end_time = 1260
    all_dist = 0
    all_duration = np.sum(plan[:,1])
    pln_pnt = plan[:,0]
    for i,orig in enumerate(pln_pnt):    
        if i<l-1:
            all_dist += dist_mat.loc[orig , pln_pnt[i+1]]
    plan_lenght = all_dist +all_duration        
    return np.abs((start_tiem + plan_lenght) - end_time) / 1440.0
	
def count_cost(individual, meta_data):
    plan = individual
    len_pln = len(plan)
    len_points = len(meta_data[0])
    
    return (len_points-len_pln) / len_points

def fitness(individual, meta_data):
    alpha = 0.5
    beta = 0.5
    _, individual = npi.group_by(individual[:,0]).max(individual)
    len_cost = lenght_cost(individual, meta_data)
    cnt_cost = count_cost(individual, meta_data)
    print(len_cost, cnt_cost)
    cost = (alpha*len_cost) + (beta*cnt_cost)
    
    return cost


ga = ga(seed_data=pln_gene1,
        meta_data=meta_data,
        population_size=60,
        generations=1000,
        crossover_probability=0.8,
        mutation_probability=0.2,
        elitism=True,
        by_parent=False,
        maximise_fitness=False)	
ga.fitness_function = fitness

ga.run()   

sol_fitness, sol_df = ga.best_individual()

plan = sol_df
start_time = 480

l = len(plan)
all_dist = 0
all_duration = np.sum(plan[:,1])
pln_pnt = plan[:,0]
for i,orig in enumerate(pln_pnt):    
    if i<l-1:
        all_dist += dist_mat.loc[orig , pln_pnt[i+1]]
plan_lenght = all_dist +all_duration  
plan_lenght + start_time