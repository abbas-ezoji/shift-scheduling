'''
            <<<<Shift Recommandeation by Genetic Algorithm>>>>            
    - Create initial gene by pivot table
    - Fetch Personnel, Shift and WorkSection Requirements Info
'''
import numpy as np
import pandas as pd
from data_access.sql_server import data 
from libs import GA_dataframes as ga

# ----------------------- get data -------------------------------------------#
conn_str = '''DRIVER={SQL Server Native Client 11.0};
             SERVER=172.16.47.154\MSSQLSERVER2017;
             DATABASE=Didgah_Timekeeper_DM;
             Integrated_Security=false;
             Trusted_Connection=yes;
             UID=sa;
             PWD=1qaz!QAZ
          '''
query_gene = '''SELECT 
                    PersonnelBaseId            	   
                    ,PersianDayOfMonth
                    ,NULL SHIFTID
                FROM 
                    Personnel P JOIN
                    Dim_Date D ON D.PersianYear = 1398 AND PersianMonth=3
              '''
query_personnel = '''SELECT  [PersonnelBaseId]
							,[WorkSectionId]
							,[YearWorkingPeriod]
							,[RequirementWorkMins_esti]
							,[RequirementWorkMins_real]
							,[TypeId]
							,[EfficiencyRolePoint]
                    FROM [Personnel]
                  '''
query_shift = '''SELECT [Code]
					 ,[Title]
					 ,[Length]
					 ,[StartTime]
					 ,[EndTime]
					 ,[Type]
             FROM [Didgah_Timekeeper_DM].[dbo].[Shifts]
			 '''                 
db = data(conn_str =  conn_str,
          query_gene = query_gene,
          query_personnel=query_personnel,
          query_shift=query_shift
         )
sql_conn = db.get_sql_conn()
chromosom_df = pd.DataFrame(db.get_chromosom())
personnel_df = pd.DataFrame(db.get_personnel())
shift_df = pd.DataFrame(db.get_shift())
# ----------------------- gene pivoted ---------------------------------------#
chromosom_df = pd.pivot_table(chromosom_df, values='SHIFTID', 
                              index=['PersonnelBaseId'],
                              columns=['PersianDayOfMonth'], aggfunc=np.sum)
# ----------------------- set personnel_df -----------------------------------#
personnel_df = personnel_df.set_index('PersonnelBaseId')

# ----------------------- set shift_df ---------------------------------------#
shift_df = shift_df.set_index('Code')

# -----------------------Randomize gene---------------------------------------#
for prs in chromosom_df.index :       
    chromosom_df.loc[prs] = np.random.choice(shift_df.index.values.tolist(),
                                             size=len(chromosom_df.columns))
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

        shift_lenght_diff.append(abs(
                                    (shift_lenght/shift_prs.iloc[prs_count,3]) 
                                    - 1) 
                                    * shift_prs.iloc[prs_count,6]
                                    )
        shift_prs.set_value(prs_count,'RequirementWorkMins_real',shift_lenght)
        shift_prs.set_value(prs_count,'diff',
            abs(shift_lenght - shift_prs.iloc[prs_count,3])
                               )        
#        print(shift_lenght - shift_prs.iloc[prs_count,3])
        prs_count += 1 
        
    cost = np.max(shift_lenght_diff)
#    print('cost: ' + str(cost))
    return cost  
# -----------------------prs output function----------------------------------# 
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
                          population_size=50,
                          generations=50,
                          crossover_probability=0.8,
                          mutation_probability=0.2,
                          elitism=True,
                          maximise_fitness=False)
 
 # -----------------------run ga----------------------------------------------# 
 
ga.fitness_function = fitness               # set the GA's fitness function
ga.run()                                    # run the GA
sol_fitness, sol_df = ga.best_individual()
sol_fitness, prs_diff_df = get_personnel_diff_len(sol_df,shift_df)
# ----------------------- db inserting ------------------------------------------# 
db.truncate()
db.insert_sol(sol_df, personnel_df, sol_fitness)

