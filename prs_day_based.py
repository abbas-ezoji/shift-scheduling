'''
            <<<<Shift Recommandeation by Genetic Algorithm>>>>            
    - Create initial gene by pivot table
    - Fetch Personnel, Shift and WorkSection Requirements Info
'''
import sys

import numpy as np
import pandas as pd
from data_access.sql_server import data 
from libs import GA_dataframes 
import datetime
from time import gmtime, strftime

work_sction_id = 1
year_working_period = 139803
# ----------------------- get data -------------------------------------------#
conn_str = '''DRIVER={SQL Server Native Client 11.0};
             SERVER=172.16.47.154;
             DATABASE=Didgah_Timekeeper_DM;
             Integrated_Security=false;
             Trusted_Connection=yes;
             UID=sa;
             PWD=1qaz!QAZ
          '''
query_gene_last =('SELECT S.[PersonnelBaseId]'+                  
                  '        ,S.[YearWorkingPeriod]'+
                  '        ,S.[Day]      '+
                  '  	  ,ShiftId as ShiftCode ' +
                  '  FROM [PersonnelShiftDateAssignments] S'+
                  '  	   JOIN Personnel P ' +
                  '  on P.PersonnelBaseId = S.PersonnelBaseId'+
                  '  WHERE '+
                  '  	EndTime in  '+
                  '  	(SELECT MAX(EndTime) FROM  '+
                  '  	 [PersonnelShiftDateAssignments] s  '+
                  '  	 JOIN Personnel P ON P.PersonnelBaseId  '+
                  '  	 = S.PersonnelBaseId '+
                  '  	 GROUP BY WorkSectionId '+
                  '  	 ,P.YearWorkingPeriod) '+
                  ' AND P.WorkSectionId = '+    
                    str(work_sction_id) +
                    'AND S.YearWorkingPeriod ='+
                    str(year_working_period)
                )
                    
query_gene_new = '''SELECT 
                         PersonnelBaseId     					 
						,YearWorkingPeriod
                        ,PersianDayOfMonth as Day
                        ,NULL ShiftCode
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
query_shift = '''SELECT [id] as ShiftCode
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
          query_gene_last = query_gene_last,
          query_gene_new = query_gene_new,
          query_personnel=query_personnel,
          query_shift=query_shift,
          query_shift_req=query_shift_req
         )
sql_conn = db.get_sql_conn()
chromosom_df = pd.DataFrame(db.get_chromosom())
personnel_df = pd.DataFrame(db.get_personnel())
shift_df = pd.DataFrame(db.get_shift())
day_req_df = pd.DataFrame(db.get_day_req())
is_new = db.is_new()
# ----------------------- gene pivoted ---------------------------------------#
chromosom_df = chromosom_df.merge(personnel_df, 
                                  left_on='PersonnelBaseId', 
                                  right_on='PersonnelBaseId', 
                                  how='inner')
chromosom_df = chromosom_df.rename(columns={"YearWorkingPeriod_x": "YearWorkingPeriod"})
chromosom_df = pd.pivot_table(chromosom_df, values='ShiftCode', 
                              index=['PersonnelBaseId',
                                      'TypeId',
                                      'EfficiencyRolePoint',
                                      'RequirementWorkMins_esti',
                                      'YearWorkingPeriod'
                                    ],
                              columns=['Day'], aggfunc=np.sum)

#tttt = chromosom_df
# ----------------------- set personnel_df -----------------------------------#
personnel_df = personnel_df.set_index('PersonnelBaseId')
personnel_df['DiffNorm'] = 0
# ----------------------- set shift_df ---------------------------------------#
shift_df = shift_df.set_index('ShiftCode')
# ----------------------- set day_req_df -------------------------------------#
day_req_df = day_req_df.set_index(['Day','PersonnelTypeReqID'])
day_req_df['day_diff_typ'] = 0
# -----------------------Randomize gene---------------------------------------#
if (is_new):
    shift_list = np.flip(shift_df.index.values.tolist())
    for prs in chromosom_df.index :       
        chromosom_df.loc[prs] = np.random.choice(shift_list,
                                                 p=[0.40,0.20,0.20,0.20],
                                                 size=len(chromosom_df.columns))
# ---------------------- sum_typid_req ---------------------------------------#
work_mins = 420
req_day = day_req_df.reset_index()
sum_typid_req = req_day.groupby('PersonnelTypeReqID').agg(
                rec_by_type = pd.NamedAgg(column='PersonnelTypeReqCount', 
                                          aggfunc='sum')                 
                )
sum_typid_req['rec_by_type'] = sum_typid_req['rec_by_type']*work_mins
sum_typid_req['TypeId'] = [1,2,3]
#------------------------fitness_day_const function for day-------------------# 
def calc_day_const (df_day,sum_typid_req):              
    df = df_day.where(df_day['Length']>0).groupby(['TypeId']).sum()
    df = df.merge(sum_typid_req, left_on='TypeId', right_on='TypeId', how='inner')
    df['diff'] = df['Length'] - df['rec_by_type']
    df['diff'] = abs((df['diff']/df['rec_by_type'])-1)
    all_point = df.sum()['EfficiencyRolePoint']
    df['diff'] = df['diff'] * (df['EfficiencyRolePoint']/all_point)    
    min_diff = df['diff'].min()
    max_diff = df['diff'].max()
    df['diff_norm'] = (df['diff'] - min_diff) / (max_diff - min_diff)
    cost = np.sum(df['diff_norm']) 
#    print('cost: ' + str(cost))
    return cost

#------------------------fitness_prs_const function---------------------------# 
def calc_prs_const (individual, meta_data):
    df = individual
    df = df.groupby(['PersonnelBaseId',
                      'TypeId',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                      'YearWorkingPeriod'
                     ]).sum().drop(columns=['ShiftCode', 'StartTime', 'EndTime', 'Type'])
    df = df.reset_index(level=3)
    df['diff'] = abs(df['RequirementWorkMins_esti'] - df['Length'])
    min_diff = df['diff'].min()
    max_diff = df['diff'].max()
    df['diff_norm'] = (df['diff'] - min_diff) / (max_diff - min_diff)
    cost = np.sum(df['diff_norm'])      
#    print('cost: ' + str(cost))
    return cost 
# ----------------------- fitness all ----------------------------------------#
def fitness (individual, meta_data):
    sht = shift_df.reset_index()
    df = pd.melt(individual.reset_index(), 
                 id_vars=['PersonnelBaseId',
                          'TypeId',
                          'EfficiencyRolePoint',
                          'RequirementWorkMins_esti',
                          'YearWorkingPeriod'
                         ],
                 var_name='Day', 
                 value_name='ShiftCode')
    df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
    day_const = 0.8*calc_day_const(df, sum_typid_req)
    prs_const = 0.2*calc_prs_const(df, sum_typid_req)
    cost = day_const + prs_const
    return cost
# -----------------------Define GA--------------------------------------------# 
ga = GA_dataframes.GeneticAlgorithm( seed_data=chromosom_df,
                          meta_data=shift_df,
                          population_size=50,
                          generations=5,
                          crossover_probability=0.8,
                          mutation_probability=0.2,
                          elitism=True,
                          maximise_fitness=False)
 
 # -----------------------run ga----------------------------------------------# 
ga.fitness_function = fitness         # set the GA's fitness function
start_time = datetime.datetime.now()
ga.run()                                    # run the GA
start_time = datetime.datetime.now()
sol_fitness, sol_df = ga.best_individual()
sol_tbl = sol_df.stack()
sol_tbl = sol_tbl.reset_index()

sol_tbl['Rank'] = 1
sol_tbl['Cost'] = sol_fitness
sol_tbl['EndTime'] =  strftime('%Y-%m-%d %H:%M:%S')
sol_tbl = sol_tbl.drop(columns=['TypeId', 'EfficiencyRolePoint', 'RequirementWorkMins_esti'])
sol_tbl = sol_tbl.values.tolist()
print(sol_tbl[1])
#########################################################
sht = shift_df.reset_index()
df = pd.melt(sol_df.reset_index(), 
             id_vars=['PersonnelBaseId',
                      'TypeId',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                      'YearWorkingPeriod'
                     ],
             var_name='Day', 
             value_name='ShiftCode')
df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
#######################################################
prs_cons = df.groupby(['PersonnelBaseId',
                      'TypeId',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                      'YearWorkingPeriod'
                     ]).sum().drop(columns=['ShiftCode', 'StartTime', 'EndTime', 'Type'])
prs_cons = prs_cons.reset_index(level=3)
prs_cons['diff'] = abs(prs_cons['RequirementWorkMins_esti'] - prs_cons['Length'])
#########################################################3

day_cons = df.where(df['Length']>0).groupby(['TypeId']).sum()
day_cons = day_cons.merge(sum_typid_req, left_on='TypeId', right_on='TypeId', how='inner')
day_cons['diff'] = day_cons['Length'] - day_cons['rec_by_type']
# ----------------------- db inserting ---------------------------------------# 
db.insert_sol(sol_tbl, personnel_df, sol_fitness)

