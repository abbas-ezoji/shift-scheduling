import numpy as np
import pandas as pd
import pyodbc
from libs import GA_dataframes as ga
from sklearn.preprocessing import scale, normalize, minmax_scale

'''
            <<<<Shift Recommandeation by Genetic Algorithm>>>>            
    - Create initial gene by pivot table
    - Fetch Personnel, Shift and WorkSection Requirements Info
'''
# -----------------------Connection String------------------------------------#
sql_conn = pyodbc.connect('''DRIVER={SQL Server Native Client 11.0};
                             SERVER=172.16.47.154\MSSQLSERVER2017;
                             DATABASE=Didgah_Timekeeper_DM;
                             Integrated_Security=false;
                             Trusted_Connection=yes;
                             UID=sa;
                             PWD=1qaz!QAZ
                          ''')

# -----------------------Query for gene pivoted-------------------------------#
query_gene = '''SELECT 
            	   PersonnelBaseId            	   
            	  ,PersianDayOfMonth
            	  ,NULL SHIFTID
               FROM 
    	          Personnel P JOIN
                  Dim_Date D ON D.PersianYear = 1398 AND PersianMonth=3
            '''
chromosom_df = pd.read_sql(query_gene, sql_conn)
chromosom_df.head(3)
chromosom_df = pd.pivot_table(chromosom_df, values='SHIFTID', 
                              index=['PersonnelBaseId'],
                              columns=['PersianDayOfMonth'], aggfunc=np.sum)
# -----------------------Query for personnel info-----------------------------#
query_personnel = '''SELECT [PersonnelBaseId]
                           ,[WorkSectionId]
                           ,[YearWorkingPeriod]
                           ,[RequirementWorkMins_esti]
                           ,[RequirementWorkMins_real]
                           ,[TypeId]
                           ,[EfficiencyRolePoint]
                      FROM [Personnel]
                   '''
personnel_df = pd.read_sql(query_personnel,sql_conn)
personnel_df = personnel_df.set_index('PersonnelBaseId')

# -----------------------Query for shift info-----------------------------#
query_shift = '''SELECT [Code]
                          ,[Title]
                          ,[Lenght]
                          ,[StartTime]
                          ,[EndTime]
                          ,[Type]
                      FROM [Didgah_Timekeeper_DM].[dbo].[Shifts]
                   '''
shfit_df = pd.read_sql(query_shift,sql_conn)
shfit_df = shfit_df.set_index('Code')

# -----------------------Randomize gene---------------------------------------#
for col in chromosom_df.columns :       
    chromosom_df[col] = chromosom_df.apply(
                        lambda row : int(np.random.choice(shfit_df.index.values, 1))
                        ,axis=1)
# -----------------------Randomize gene---------------------------------------# 
ga = ga.GeneticAlgorithm(chromosom_df,
                         population_size=2,
                         generations=10,
                         crossover_probability=0.8,
                         mutation_probability=0.2,
                         elitism=True,
                         maximise_fitness=False)

def fitness (individual, data):
    w = np.random.randint(0,100)
    return w

ga.fitness_function = fitness               # set the GA's fitness function
ga.run()                                    # run the GA
sol_fitness, sol_df = ga.best_individual()
                    
# ----------------Query for insert shift assignment info----------------------#
cursor = sql_conn.cursor()
year_workingperiod = 1398 * 100 + 3
prs_count,day_count = chromosom_df.shape                      
cursor.execute('''truncate table PersonnelShiftDateAssignments''')

prs_count = 0
for prs in personnel_df.index:
    prs_count = prs_count + 1
    for day in range(day_count): 
        cursor.execute('''insert into PersonnelShiftDateAssignments 
                       values (?, ?, ?, ?, ?)'''
                       ,(prs,int(sol_df.loc[prs][[day+1]])
                       ,year_workingperiod * 100 + day+1,0,0)
                       )

sql_conn.commit()                     

