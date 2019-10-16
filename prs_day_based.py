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
             SERVER=172.16.47.154;
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
                            ,[DiffNorm]
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
query_shift_req = '''SELECT d.PersianDayOfMonth as [Day]
                          ,[PersonnelTypeReqID]
                          ,[PersonnelTypeReqCount]
                          ,[day_diff_typ]
                      FROM [Didgah_Timekeeper_DM].[dbo].[WorkSectionRequirements] t
                      join Dim_Date d on d.Date = t.Date
                    order by PersianDayOfMonth                        
                  '''              
db = data(conn_str =  conn_str,
          query_gene = query_gene,
          query_personnel=query_personnel,
          query_shift=query_shift,
          query_shift_req=query_shift_req
         )
sql_conn = db.get_sql_conn()
chromosom_df = pd.DataFrame(db.get_chromosom())
personnel_df = pd.DataFrame(db.get_personnel())
shift_df = pd.DataFrame(db.get_shift())
day_req_df = pd.DataFrame(db.get_day_req())
# ----------------------- gene pivoted ---------------------------------------#
chromosom_df = pd.pivot_table(chromosom_df, values='SHIFTID', 
                              index=['PersonnelBaseId'],
                              columns=['PersianDayOfMonth'], aggfunc=np.sum)
# ----------------------- set personnel_df -----------------------------------#
personnel_df = personnel_df.set_index('PersonnelBaseId')

# ----------------------- set shift_df ---------------------------------------#
shift_df = shift_df.set_index('Code')
# ----------------------- set day_req_df -------------------------------------#
day_req_df = day_req_df.set_index(['Day','PersonnelTypeReqID'])
day_req_df['day_diff_typ'] = 0
# -----------------------Randomize gene---------------------------------------#
for prs in chromosom_df.index :       
    chromosom_df.loc[prs] = np.random.choice(shift_df.index.values.tolist(),
                                             size=len(chromosom_df.columns))

#------------------------fitness_day_const function for day-------------------# 
def fitness_day_const (individual, meta_data):
    prs_count,day_count = individual.shape        
    day_req_df['day_diff_typ'] = 0  
    max_typid = personnel_df['TypeId'].max()
    for day in range(day_count):        
        for prs in personnel_df.index:
            shift_lenght = meta_data.loc[individual.loc[prs,day+1]][1]
            type_id = personnel_df.loc[prs,'TypeId']
            day_req_df.at[(day+1,type_id),'day_diff_typ']+= int(shift_lenght>0)                 
    
    day_req_df.at[:,'day_diff_typ'] = abs(day_req_df.loc[:,'day_diff_typ']/
                 day_req_df.loc[:,'PersonnelTypeReqCount']-1)
                                             
#    cost = np.max(shift_lenght_diff)   # tchebichef role
    cost = np.sum(day_req_df.at[:,'day_diff_typ']) # 
#    print('cost: ' + str(cost))
    return cost 
#------------------------fitness_prs_const function for prs ------------------# 
def fitness_prs_const (individual, meta_data):
    prs_count,day_count = individual.shape    
    shift_prs = personnel_df.reset_index()
    shift_prs['DiffNorm'] = 0
    prs_count = 0
    shift_lenght_diff = []
    for prs in personnel_df.index: 
        shift_lenght = 0          
        for day in range(day_count):
            shift_lenght += meta_data.loc[individual.loc[prs,day+1]][1]

        shift_lenght_diff.append(abs(shift_lenght/shift_prs.iloc[prs_count,3]-1) 
                                    * shift_prs.iloc[prs_count,6]
                                    )
        personnel_df.at[prs,'RequirementWorkMins_real'] = shift_lenght
        personnel_df.at[prs,'DiffNorm'] = abs(shift_lenght - 
                                               shift_prs.iloc[prs_count,3])
        prs_count += 1 
        
#    cost = np.max(shift_lenght_diff)   # tchebichef role
    cost = np.mean(shift_lenght_diff) # 
#    print('cost: ' + str(cost))
    return cost 
# ----------------------- fitness all ----------------------------------------#
def fitness (individual, meta_data):
    day_const = fitness_day_const(individual, meta_data)
    prs_const = fitness_prs_const(individual, meta_data)
    cost = day_const + prs_const
    return cost
# -----------------------Define GA--------------------------------------------# 
ga = ga.GeneticAlgorithm( seed_data=chromosom_df,
                          meta_data=shift_df,
                          population_size=50,
                          generations=100,
                          crossover_probability=0.8,
                          mutation_probability=0.2,
                          elitism=True,
                          maximise_fitness=False)
 
 # -----------------------run ga----------------------------------------------# 
ga.fitness_function = fitness         # set the GA's fitness function
ga.run()                                    # run the GA
sol_fitness, sol_df = ga.best_individual()

# ----------------------- db inserting ---------------------------------------# 
db.truncate()
db.insert_sol(sol_df, personnel_df, sol_fitness)

