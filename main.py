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
from time import strftime, gmtime
from libs.get_random import get_best_first_rank as get_rank

def prs_day_alg(work_sction_id, year_working_period):
    work_sction_id = 1
    year_working_period = 139806
    
    PersianYear  = int(year_working_period / 100)
    PersianMonth = int(year_working_period % 100)
    # ----------------------- get data -------------------------------------------#
    conn_str = '''DRIVER={SQL Server Native Client 11.0};
                 SERVER=172.16.47.154;
                 DATABASE=Didgah_Timekeeper_DM;
                 Integrated_Security=false;
                 Trusted_Connection=yes;
                 UID=sa;
                 PWD=1qaz!QAZ
              '''
    query_gene_last = '''SELECT DISTINCT   
                                [Rank]
                               ,[Cost]      
                               ,[WorkSectionId]
                               ,[YearWorkingPeriod]
                               ,[EndTime]
                               ,DATEDIFF(SECOND,EndTime,GETDATE())life_cycle	 
                               ,[UsedParentCount]
                         FROM [PersonnelShiftDateAssignments]                         
                         WHERE WorkSectionId = {0} AND YearWorkingPeriod = {1}                                
                       '''.format(work_sction_id,year_working_period)                        
    parent_rank = get_rank(conn_str, query_gene_last)
    by_parent = True 
    query_gene_last ='''SELECT S.[PersonnelBaseId]                 
                              ,S.[YearWorkingPeriod]
                              ,S.[Day]      
                          	  ,ShiftId as ShiftCode 
                        FROM 
                        	[PersonnelShiftDateAssignments] S
                        WHERE                           	
                            WorkSectionId = {0}                      
                            AND S.YearWorkingPeriod = {1}   
                            AND S.RANK = {2}
                     '''.format(work_sction_id,
                                year_working_period,
                                parent_rank)
                        
    query_gene_new = '''SELECT 
                             PersonnelBaseId     					 
    						,YearWorkingPeriod
                            ,PersianDayOfMonth as Day
                            ,1 ShiftCode
                        FROM 
                            Personnel P JOIN
                            Dim_Date D ON D.PersianYear = {0} 
                            AND PersianMonth={1} and WorkSectionId = {2}
                      '''.format(PersianYear, PersianMonth, work_sction_id)
                      
    
    query_personnel = '''SELECT  [PersonnelBaseId]
    							,[WorkSectionId]
    							,[YearWorkingPeriod]
    							,[RequirementWorkMins_esti]
    							,[RequirementWorkMins_real]
    							,[TypeId] prs_typ_id
    							,[EfficiencyRolePoint]
                                ,[DiffNorm]
                        FROM [Personnel]
                        WHERE WorkSectionId = {0} AND YearWorkingPeriod = {1}
                      '''.format(work_sction_id,year_working_period)
                      
    query_shift = '''SELECT [id] as ShiftCode
    					 ,[Title]
    					 ,[Length]
    					 ,[StartTime]
    					 ,[EndTime]
    					 ,[Type] ShiftTypeID
                    FROM [Shifts]
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
                        WHERE 
    						YEAR = {0} AND Month = {1}
                            AND WorkSectionId = {2}
                        ORDER BY 
                        	WorkSectionId,D.Date
                        	,PersonnelTypeReqID,ShiftTypeID                        
                      '''.format(PersianYear, PersianMonth, work_sction_id)      
    query_prs_req = '''SELECT  [PersonnelBaseId]
                              ,[YearWorkingPeriod]
                              ,[WorkSectionId]
                              ,[Day]
                              ,[ShiftTypeID]
                              ,[Value]
                      FROM [PersonnelRequest]
                      WHERE [WorkSectionId] = {0}
                            and [YearWorkingPeriod] = {1}
                      ORDER BY[PersonnelBaseId]
                              ,[YearWorkingPeriod]
                              ,[Day]
                              ,[ShiftTypeID]
                    '''.format(work_sction_id,year_working_period)
                         
    db = data(conn_str =  conn_str,
              query_gene_last = query_gene_last,
              query_gene_new = query_gene_new,
              query_personnel=query_personnel,
              query_shift=query_shift,
              query_shift_req=query_shift_req,
              query_prs_req=query_prs_req
             )
    sql_conn = db.get_sql_conn()
    chromosom_df = pd.DataFrame(db.get_chromosom(work_sction_id, 
                                                 year_working_period))
    personnel_df = pd.DataFrame(db.get_personnel())
    shift_df = pd.DataFrame(db.get_shift())
    day_req_df = pd.DataFrame(db.get_day_req())
    prs_req_df = pd.DataFrame(db.get_prs_req())
    is_new = db.is_new()
    # ----------------------- gene pivoted ---------------------------------------#
    chromosom_df = chromosom_df.merge(personnel_df, 
                                      left_on='PersonnelBaseId', 
                                      right_on='PersonnelBaseId', 
                                      how='inner')
    chromosom_df = pd.pivot_table(chromosom_df, values='ShiftCode', 
                                  index=['PersonnelBaseId',
                                          'prs_typ_id',
                                          'EfficiencyRolePoint',
                                          'RequirementWorkMins_esti'                                                                           
                                        ],
                                  columns=['Day'], aggfunc=np.sum)
    # ----------------------- set personnel_df -----------------------------------#
    personnel_df = personnel_df.set_index('PersonnelBaseId')
    personnel_df['DiffNorm'] = 0
    # ----------------------- set shift_df ---------------------------------------#
    shift_df = shift_df.set_index('ShiftCode')
    # ----------------------- set day_req_df -------------------------------------#
    day_req_df = day_req_df.set_index(['Day','prs_typ_id','ShiftTypeID'])
    day_req_df['day_diff_typ'] = 0
    day_count =len(day_req_df.groupby(axis=0, level=0, as_index=True).count())
    # -----------------------Randomize gene---------------------------------------#
    if (is_new):      
        shift_list = np.flip(shift_df.index.values.tolist())   
        for prs in chromosom_df.index :       
            chromosom_df.loc[prs] = np.random.choice(shift_list,
                                                     p=[1/14,1/14,1/14,
                                                        1/14,2/14,3/14,5/14],
                                                     size=len(chromosom_df.columns)
                                                     )    
    # ---------------------- calcute typid_req_day--------------------------------#
    req_day = day_req_df.reset_index()
    typid_req_day = req_day.groupby(['Day','prs_typ_id','ShiftTypeID']).agg(
                    ReqMinCount = pd.NamedAgg(column='ReqMinCount', 
                                              aggfunc='sum'),
                    ReqMaxCount = pd.NamedAgg(column='ReqMaxCount', 
                                              aggfunc='sum')
                    )
    typid_req_day['ReqMean'] = (typid_req_day['ReqMaxCount']+ 
                                typid_req_day['ReqMinCount'])/2   
    # ---------------------- Calcute diff require and resource--------------------# 
                        #---------------sum_typid_req---------------#
    sum_typid_req = typid_req_day.reset_index()          
    sum_typid_req = sum_typid_req.groupby('prs_typ_id').agg(
                req_min  = pd.NamedAgg(column='ReqMinCount', 
                                              aggfunc='sum'), 
                req_max = pd.NamedAgg(column='ReqMaxCount', 
                                              aggfunc='sum'),
                req_mean= pd.NamedAgg(column='ReqMean', 
                                              aggfunc='sum'),            
            )
    sum_typid_req = sum_typid_req[:]*480
                         #--------------sum_typid_prs----------------#
    sum_typid_prs = personnel_df.groupby('prs_typ_id').agg(
                all_rec  = pd.NamedAgg(column='RequirementWorkMins_esti', 
                                              aggfunc='sum'), 
                count_prs = pd.NamedAgg(column='RequirementWorkMins_esti', 
                                              aggfunc='count'),
            )
                         #--------------sum_typid_prs----------------#
    diff_req_rec = sum_typid_req.join(sum_typid_prs,how='inner')                   
    diff_req_rec['diff_min'] = (diff_req_rec['req_min'] - 
                                diff_req_rec['all_rec'] )/diff_req_rec['count_prs'] 
    diff_req_rec['diff_max'] = (diff_req_rec['req_max'] - 
                                diff_req_rec['all_rec'] )/diff_req_rec['count_prs'] 
    diff_req_rec['diff_mean'] = (diff_req_rec['req_mean'] - 
                                diff_req_rec['all_rec'] )/diff_req_rec['count_prs']
    #diff_req_rec = diff_req_rec.reset_index()
    #------------------------ Consttraint day_const function for day -------------# 
    def calc_day_const (individual,meta_data):  
        df = individual           
        df = df[df['Length']>0].groupby(['Day',
                                         'prs_typ_id',
                                         'ShiftTypeID']).agg(
                            prs_count = pd.NamedAgg(column='Length', 
                                              aggfunc='count'), 
                            prs_points = pd.NamedAgg(column='EfficiencyRolePoint', 
                                              aggfunc='sum'),
                            )
        df = df.merge(meta_data, left_on=['Day','prs_typ_id','ShiftTypeID'], 
                      right_on=['Day','prs_typ_id','ShiftTypeID'], how='right') 
        df.fillna(0,inplace=True)
        df['diff_max'] = abs(df['prs_count'] - df['ReqMaxCount'])
        df['diff_min'] = abs(df['prs_count'] - df['ReqMinCount'])  
        df['diff'] = df[['diff_max','diff_min']].apply(np.min, axis=1)
        df['diff_norm'] = df['diff']/df['ReqMaxCount']
    #    cost = np.mean(df['diff_norm'])
        df['diff_norm'] = df['diff_norm']**2
        cost = np.sum(df['diff_norm']) / len(df)
    #    cost = np.max(df['diff_norm']) / len(df)
    #    print('cost: ' + str(cost))
        return cost
    
    #------------------------ Consttraint prs_const function for day -------------# 
    def calc_prs_const (individual, meta_data):
        df = individual    
        df = df.groupby(['PersonnelBaseId',
                          'prs_typ_id',
                          'EfficiencyRolePoint',
                          'RequirementWorkMins_esti',                      
                         ]).sum().drop(columns=['ShiftCode', 'StartTime', 
                                                'EndTime', 'ShiftTypeID'])    
        df = df.reset_index()
        meta_data = meta_data.reset_index()
        df = df.merge(meta_data, left_on='prs_typ_id', right_on='prs_typ_id'
                      ,how='inner')
        
        df['diff'] = abs(df['RequirementWorkMins_esti'] + 
                         df['diff_min'] - df['Length'])         
        df['diff_norm'] = df['diff']/df['RequirementWorkMins_esti']
    #    cost = np.mean(df['diff_norm'])    
        df['diff_norm'] = df['diff_norm']**2
        cost = np.sum(df['diff_norm']) / len(df)
    #    print('cost: ' + str(cost))
        return cost 
    #------------------------ Objective prs_req function for prs req -------------# 
    def calc_prs_req_cost (individual,meta_data):  
        df = individual     
        df['Assigned'] = 1
        df_req = meta_data.merge(df,  
                                 left_on =['PersonnelBaseId','Day','ShiftTypeID'],
                                 right_on=['PersonnelBaseId','Day','ShiftTypeID'],
                                 how='left'
                                )
        df_req = df_req.fillna(-1)
        
        df_req['cost'] = df_req['Assigned']*df_req['Value']
    
        return 0
    
    # ----------------------- fitness all ----------------------------------------#
    def fitness (individual, meta_data):
        sht = shift_df.reset_index()
        sht_2 = sht[sht['ShiftCode']>10]
        sht_2['Length'] = sht_2['Length'] // 2
        sht_2['ShiftTypeID'] = sht_2['ShiftTypeID'] // 10
        sht_2.index = [7,8,9]
        sht['Length'] = sht['Length'] // 2
        sht['ShiftTypeID'] = sht['ShiftTypeID'] % 10
        sht = sht.append(sht_2)
        #sht[sht['ShiftCode']>10]
        df = pd.melt(individual.reset_index(), 
                     id_vars=['PersonnelBaseId',
                              'prs_typ_id',
                              'EfficiencyRolePoint',
                              'RequirementWorkMins_esti',
                              
                             ],
                     var_name='Day', 
                     value_name='ShiftCode')
        df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
        day_const = 0.8*calc_day_const(df, typid_req_day)
        prs_const = 0.2*calc_prs_const(df, diff_req_rec)
        prs_req_cost = calc_prs_req_cost(df, prs_req_df)
        cost = day_const + prs_const
        return cost
    # -----------------------Define GA--------------------------------------------#        
    ga = GA_dataframes.GeneticAlgorithm( seed_data=chromosom_df,
                              meta_data=shift_df,
                              population_size=50,
                              generations=200,
                              crossover_probability=0.8,
                              mutation_probability=0.2,
                              elitism=True,
                              by_parent=by_parent,
                              maximise_fitness=False)
     
     # ----------------------- run ga --------------------------------------------# 
    ga.fitness_function = fitness         # set the GA's fitness function
    start_time = gmtime()
    ga.run()                                    # run the GA
    end_time = gmtime()
    time_consum_hour   = end_time[3] - start_time[3]
    time_consum_minute = end_time[4] - start_time[4]
    time_consum_second = end_time[5] - start_time[5]
    print('time_consum : ' + str(time_consum_hour) + ':'+ 
                             str(time_consum_minute) + ':'+ 
                             str(time_consum_second)
                            )
    sol_fitness, sol_df = ga.best_individual()
    sol_tbl = sol_df.stack()
    sol_tbl = sol_tbl.reset_index()
    
    sol_tbl['Rank'] = 1
    sol_tbl['Cost'] = sol_fitness
    sol_tbl['EndTime'] =  strftime('%Y-%m-%d %H:%M:%S')
    sol_tbl['UsedParentCount'] =  0
    sol_tbl['WorkSectionId'] = work_sction_id
    sol_tbl['YearWorkingPeriod'] = year_working_period
    sol_tbl = sol_tbl.drop(columns=['prs_typ_id', 
                                    'EfficiencyRolePoint', 
                                    'RequirementWorkMins_esti'])
    sol_tbl = sol_tbl.values.tolist()
    # ----------------------- inserting ------------------------------------------# 
    #db.delete_last_sol(work_sction_id,year_working_period)
    db.insert_sol(sol_tbl, personnel_df, 
                  sol_fitness,work_sction_id,year_working_period,
                  parent_rank)
    #-------------------- output show --------------------------------------------#
    #########################################################
    sht = shift_df.reset_index()
    sht_2 = sht[sht['ShiftCode']>10]
    sht_2['Length'] = sht_2['Length'] // 2
    sht_2['ShiftTypeID'] = sht_2['ShiftTypeID'] // 10
    sht_2.index = [7,8,9]
    sht['Length'] = sht['Length'] // 2
    sht['ShiftTypeID'] = sht['ShiftTypeID'] % 10
    sht = sht.append(sht_2)
    df = pd.melt(sol_df.reset_index(), 
                 id_vars=['PersonnelBaseId',
                          'prs_typ_id',
                          'EfficiencyRolePoint',
                          'RequirementWorkMins_esti',
                         
                         ],
                 var_name='Day', 
                 value_name='ShiftCode')
    df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
    #######################################################
    cons_prs = df.groupby(['PersonnelBaseId',
                          'prs_typ_id',
                          'EfficiencyRolePoint',
                          'RequirementWorkMins_esti',
                          
                         ]).sum().drop(columns=['ShiftCode', 'StartTime', 
                                                'EndTime', 'ShiftTypeID'])
    cons_prs = cons_prs.reset_index(level=3)
    cons_prs['diff'] = (cons_prs['RequirementWorkMins_esti'] - cons_prs['Length'])
    #########################################################3
    
    cons_day = df[df['Length']>0].groupby(['Day',
                                           'prs_typ_id',
                                           'ShiftTypeID']).agg(
                                  prs_count = pd.NamedAgg(column='Length', 
                                              aggfunc='count'), 
                                  prs_points = pd.NamedAgg(column='EfficiencyRolePoint', 
                                              aggfunc='sum'),
                                )
                                  
    cons_day = cons_day.merge(typid_req_day, 
                              left_on=['Day','prs_typ_id','ShiftTypeID'], 
                              right_on=['Day','prs_typ_id','ShiftTypeID'], 
                              how='right') 
    cons_day.fillna(0,inplace=True)            
    cons_day['diff_max'] = abs(cons_day['prs_count'] - cons_day['ReqMaxCount'])
    cons_day['diff_min'] = abs(cons_day['prs_count'] - cons_day['ReqMinCount'])  
    cons_day['diff'] = cons_day[['diff_max','diff_min']].apply(np.min, axis=1) 
    cons_day.sort_index(axis=0, level=[0,1,2], ascending=True, inplace=True)
    
if __name__ == "__main__":
    work_sction_id = 1 #int(sys.argv[1])
    year_working_period = 139806#int(sys.argv[2])
    prs_day_alg(work_sction_id=work_sction_id,
                year_working_period=year_working_period)