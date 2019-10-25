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
query_gene_new = (query_gene_new + ' AND p.WorkSectionId = ' 
                                + str(work_sction_id))

query_personnel = '''SELECT  [PersonnelBaseId]
							,[WorkSectionId]
							,[YearWorkingPeriod]
							,[RequirementWorkMins_esti]
							,[RequirementWorkMins_real]
							,[TypeId] prs_typ_id
							,[EfficiencyRolePoint]
                            ,[DiffNorm]
                    FROM [Personnel]
                  '''
query_personnel = (query_personnel + ' WHERE WorkSectionId = ' 
                                   + str(work_sction_id))
                  
query_shift = '''SELECT [id] as ShiftCode
					 ,[Title]
					 ,[Length]
					 ,[StartTime]
					 ,[EndTime]
					 ,[Type] ShiftTypeID
             FROM [Didgah_Timekeeper_DM].[dbo].[Shifts]
			 '''   
query_shift_req = '''SELECT [PersianDayOfMonth] AS Day
                          ,[PersonnelTypeReqID] as prs_typ_id
                          ,[ShiftTypeID]
                          ,[ReqMinCount]
                          ,[ReqMaxCount]
                          ,[day_diff_typ]
                    FROM 
                    	[WorkSectionRequirements] R
                    	JOIN Dim_Date D ON D.PersianYear=R.Year
                    	AND D.PersianMonth = R.Month
                    	AND D.SpecialDay = R.DayType
                    ORDER BY 
                    	WorkSectionId,D.Date
                    	,PersonnelTypeReqID,ShiftTypeID                        
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
                                      'prs_typ_id',
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
day_req_df = day_req_df.set_index(['Day','prs_typ_id','ShiftTypeID'])
day_req_df['day_diff_typ'] = 0
# -----------------------Randomize gene---------------------------------------#
if (is_new):    
    shift_list = np.flip(shift_df.index.values.tolist())   
    for prs in chromosom_df.index :       
        chromosom_df.loc[prs] = np.random.choice(shift_list,
                                                 p=[0.05,0.15,0.35,0.45],
                                                 size=len(chromosom_df.columns))
        
# ---------------------- sum_typid_req ---------------------------------------#

req_day = day_req_df.reset_index()
sum_typid_req = req_day.groupby(['Day','prs_typ_id','ShiftTypeID']).agg(
                ReqMinCount = pd.NamedAgg(column='ReqMinCount', 
                                          aggfunc='sum'),
                ReqMaxCount = pd.NamedAgg(column='ReqMaxCount', 
                                          aggfunc='sum')
                )
sum_typid_req['ReqMean'] = (sum_typid_req['ReqMaxCount'] + 
                            sum_typid_req['ReqMinCount'])/2
#------------------------fitness_day_const function for day-------------------# 
def calc_day_const (individual,sum_typid_req):   
    df = individual           
    df = df[df['Length']>0].groupby(['Day',
                                     'prs_typ_id',
                                     'ShiftTypeID']).agg(
                        prs_count = pd.NamedAgg(column='Length', 
                                          aggfunc='count'), 
                        prs_points = pd.NamedAgg(column='EfficiencyRolePoint', 
                                          aggfunc='sum'),
                        )
    df = df.merge(sum_typid_req, left_on=['Day','prs_typ_id','ShiftTypeID'], 
                  right_on=['Day','prs_typ_id','ShiftTypeID'], how='inner')    
    df['diff_max'] = abs(df['prs_count'] - df['ReqMaxCount'])
    df['diff_min'] = abs(df['prs_count'] - df['ReqMinCount'])  
    df['diff'] = df[['diff_max','diff_min']].apply(np.min, axis=1)                
#    all_point = df.sum()['prs_points']
#    df['diff'] = df['diff'] * (df['prs_points']/all_point)    
#    min_diff = df['diff'].min()
#    max_diff = df['diff'].max()
#    df['diff_norm'] = (df['diff'] - min_diff) / (max_diff - min_diff)
    df['diff_norm'] = df['diff']/df['diff_max']
    cost = np.mean(df['diff_norm']) 
#    print('cost: ' + str(cost))
    return cost

#------------------------fitness_prs_const function---------------------------# 
def calc_prs_const (individual, meta_data):
    df = individual    
    df = df.groupby(['PersonnelBaseId',
                      'prs_typ_id',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                      'YearWorkingPeriod'
                     ]).sum().drop(columns=['ShiftCode', 'StartTime', 
                                            'EndTime', 'ShiftTypeID'])
    df = df.reset_index(level=[2,3])
    df['diff'] = abs(df['RequirementWorkMins_esti'] + 5000 - df['Length'])     
#    all_point = df.sum()['EfficiencyRolePoint']
#    df['diff'] = df['diff'] * (df['EfficiencyRolePoint']/all_point)
#    min_diff = df['diff'].min()
#    max_diff = df['diff'].max()
#    df['diff_norm'] = (df['diff'] - min_diff) / (max_diff - min_diff)
    df['diff_norm'] = df['diff']/5000
    cost = np.mean(df['diff_norm'])      
#    print('cost: ' + str(cost))◘
    return cost 
# ----------------------- fitness all ----------------------------------------#
def fitness (individual, meta_data):
    sht = shift_df.reset_index()
    df = pd.melt(individual.reset_index(), 
                 id_vars=['PersonnelBaseId',
                          'prs_typ_id',
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
                          generations=50,
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
sol_tbl = sol_tbl.drop(columns=['prs_typ_id', 
                                'EfficiencyRolePoint', 
                                'RequirementWorkMins_esti'])
sol_tbl = sol_tbl.values.tolist()
print(sol_tbl[1])
#########################################################
sht = shift_df.reset_index()
df = pd.melt(sol_df.reset_index(), 
             id_vars=['PersonnelBaseId',
                      'prs_typ_id',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                      'YearWorkingPeriod'
                     ],
             var_name='Day', 
             value_name='ShiftCode')
df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
#######################################################
prs_cons = df.groupby(['PersonnelBaseId',
                      'prs_typ_id',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                      'YearWorkingPeriod'
                     ]).sum().drop(columns=['ShiftCode', 'StartTime', 
                                            'EndTime', 'ShiftTypeID'])
prs_cons = prs_cons.reset_index(level=3)
prs_cons['diff'] = (prs_cons['RequirementWorkMins_esti'] - prs_cons['Length'])
#########################################################3

day_cons = df[df['Length']>0].groupby(['Day',
                                       'prs_typ_id',
                                       'ShiftTypeID']).agg(
                              prs_count = pd.NamedAgg(column='Length', 
                                          aggfunc='count'), 
                              prs_points = pd.NamedAgg(column='EfficiencyRolePoint', 
                                          aggfunc='sum'),
                            )
day_cons = day_cons.merge(sum_typid_req, 
                          left_on=['Day','prs_typ_id','ShiftTypeID'], 
                          right_on=['Day','prs_typ_id','ShiftTypeID'], 
                          how='inner')             
day_cons['diff_max'] = abs(day_cons['prs_count'] - day_cons['ReqMaxCount'])
day_cons['diff_min'] = abs(day_cons['prs_count'] - day_cons['ReqMinCount'])  
day_cons['diff'] = day_cons[['diff_max','diff_min']].apply(np.min, axis=1) 
# ----------------------- inserting ---------------------------------------# 
db.insert_sol(sol_tbl, personnel_df, sol_fitness)

