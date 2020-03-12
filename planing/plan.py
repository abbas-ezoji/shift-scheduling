import pandas as pd
import numpy as np
from ga_numpy import GeneticAlgorithm as ga



data = pd.read_excel('attractions.xlsx')
df = data
df['province'] = ''; df['city'] = ''; 

for i, s in zip(df.index,df['description']):    
    describ = df.iloc[[i]]['description']
    rq_time = str(df.iloc[[i]]['requiredTime'])
    
    describ = np.array(describ)    
    describ_arr = describ[0].strip().split('/')
    rq_time = rq_time.strip().split(' ')
    
    country = describ_arr[0] if len(describ_arr)>0 else ''
    province = describ_arr[1] if len(describ_arr)>1 else ''
    city = describ_arr[2] if len(describ_arr)>2 else ''
    df.ix[i,10] = rq_time[4]
    df.ix[i,14] = province
    df.ix[i,15] = city.split(' ')[0].replace('\n','')

    
df_kelar = df[df['city']=='کلاردشت']

dist_df = pd.read_csv('m.csv')

dist_mat = pd.pivot_table(dist_df,                           
                          index=['orgin'],
                          columns=['dist'], 
                          values='len', 
                          aggfunc=np.sum)

vst_time_from = df_kelar['visitingTimeFrom'] 
vst_time_to = df_kelar['visitingTimeTo']
meta_data = np.array([dist_mat.index, df_kelar['requiredTime']])

points = meta_data[0]
rq_time = meta_data[1]
pln_gene1 = np.array([points, 
                      rq_time, 
                      ], dtype=int).T
pln_gene2 = np.array([np.flip(points), 
                      np.flip(rq_time), 
                     ], dtype=int).T						  

ga = ga(seed_data=pln_gene1,
        meta_data=meta_data,
        population_size=60,
        generations=500,
        crossover_probability=0.8,
        mutation_probability=0.2,
        elitism=True,
        by_parent=False,
        maximise_fitness=False)
							  
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
    _, len_points = meta_data.shape
    
    return (len_points-len_pln) / len_points

def fitness(individual, meta_data):
    alpha = 0.5
    beta = 0.5
    len_cost = lenght_cost(individual, meta_data)
    cnt_cost = count_cost(individual, meta_data)
    print(len_cost, cnt_cost)
    cost = (alpha*len_cost) + (beta*cnt_cost)
    
    return cost
	
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