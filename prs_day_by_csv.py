import numpy as np
import pandas as pd
from libs import GA_dataframes as ga

# -----------------------Query for gene pivoted-------------------------------#

chromosom_df = pd.read_csv('C:/MyFiles/Projects/DM/sample files/output.csv')
chromosom_df = pd.pivot_table(chromosom_df, values='SHIFTID', 
                              index=['PersonnelBaseId'],
                              columns=['PersianDayOfMonth'], aggfunc=np.sum)

# -----------------------Query for personnel info-----------------------------#
personnel_df = pd.read_csv('C:/MyFiles/Projects/DM/sample files/personnel.csv')
personnel_df = personnel_df.set_index('PersonnelBaseId')
# -----------------------Query for shift info---------------------------------#
shift_df = pd.read_csv('C:/MyFiles/Projects/DM/sample files/shifts.csv')
shift_df = shift_df.set_index('Code')
# -----------------------Randomize gene---------------------------------------#
for prs in chromosom_df.index :       
    chromosom_df.loc[prs] = np.random.choice(shift_df.index.values.tolist(),size=len(chromosom_df.columns))
chromosom_df = chromosom_df.astype(int)
#------------------------fitness function-------------------------------------# 
def fitness (individual, meta_data):
    prs_count,day_count = individual.shape    
    shift_prs = personnel_df.reset_index()
    shift_prs['diff'] = 0
    prs_count = 0
    shift_lenght_diff = []
    for prs in personnel_df.index: 
        shift_lenght = 0          
        for day in range(day_count):
#            print('shiftcode:'+str(individual.loc[prs,day+1]))
            shift_lenght += meta_data.loc[individual.loc[prs,day+1]][1]

        shift_lenght_diff.append(abs((shift_lenght/shift_prs.iloc[prs_count,3]) - 1))
        shift_prs.set_value(prs_count,'RequirementWorkMins_real',shift_lenght)
        shift_prs.set_value(prs_count,'diff',
            abs(shift_lenght - shift_prs.iloc[prs_count,3])
                               )        
#        print(shift_lenght - shift_prs.iloc[prs_count,3])
        prs_count += 1 
        
    cost = np.mean(shift_lenght_diff)
#    print('cost: ' + str(cost))
    return cost  
# -----------------------prs output function-------------------------------------# 
def get_personnel_diff_len (individual, meta_data):
    prs_count,day_count = individual.shape    
    shift_prs = personnel_df.reset_index()
    shift_prs['diff'] = 0
    prs_count = 0
    shift_lenght_diff = []
    for prs in personnel_df.index: 
        shift_lenght = 0          
        for day in range(day_count):
#            print('shiftcode:'+str(individual.loc[prs,day+1]))
            shift_lenght += meta_data.loc[individual.loc[prs,day+1]][1]

        shift_lenght_diff.append(shift_lenght-shift_prs.iloc[prs_count,3])
        shift_prs.set_value(prs_count,'RequirementWorkMins_real',shift_lenght)
        shift_prs.set_value(prs_count,'diff',
            abs(shift_lenght - shift_prs.iloc[prs_count,3])
                               )        
#        print(shift_lenght - shift_prs.iloc[prs_count,3])
        prs_count += 1 
        
    cost = np.mean(shift_lenght_diff)
#    print('cost: ' + str(cost))
    return cost,shift_prs
# -----------------------Define GA--------------------------------------------# 
 
ga = ga.GeneticAlgorithm( seed_data=chromosom_df,
                          meta_data=shift_df,
                          population_size=20,
                          generations=10,
                          crossover_probability=0.8,
                          mutation_probability=0.2,
                          elitism=True,
                          maximise_fitness=False)
 
 # -----------------------run ga-----------------------------------------------# 
 
ga.fitness_function = fitness               # set the GA's fitness function
ga.run()                                    # run the GA
sol_fitness, sol_df = ga.best_individual()
sol_fitness, prs_diff_df = get_personnel_diff_len(sol_df,shift_df)