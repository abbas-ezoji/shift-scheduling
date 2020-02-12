import pandas as pd
import numpy as np
import pyodbc

conn_str = '''DRIVER={SQL Server Native Client 11.0};
             SERVER=.;
             DATABASE=Didgah_Timekeeper_DM;
             Integrated_Security=false;
             Trusted_Connection=yes;
             UID=sa;
             PWD=1qaz!QAZ
          '''

sql_conn = pyodbc.connect(conn_str)
query = '''SELECT [PersonnelBaseId]
                  ,[YearWorkingPeriod]
                  ,[WorkSectionId]
                  ,[Day]
                  ,[ShiftTypeID]
                  ,[Value]
          FROM [PersonnelRequest]
          WHERE [WorkSectionId] = 1 and [YearWorkingPeriod] = 139806
          ORDER BY[PersonnelBaseId]
                  ,[YearWorkingPeriod]
                  ,[Day]
                  ,[ShiftTypeID]
        '''

query_gene_last ='''SELECT S.[PersonnelBaseId]                 
                          ,S.[YearWorkingPeriod]
                          ,S.[Day]      
                      	  ,ShiftId as ShiftCode 
                    FROM 
                    	[PersonnelShiftDateAssignments] S
                    WHERE                           	
                        WorkSectionId = 1                     
                        AND S.YearWorkingPeriod = 139806
                        AND S.RANK = 1
                 '''
query_shift = '''SELECT [id] as ShiftCode
					 ,[Title]
					 ,[Length]
					 ,[StartTime]
					 ,[EndTime]
					 ,[Type] ShiftTypeID
                FROM [Shifts]
			 '''   
query_personnel = '''SELECT  [PersonnelBaseId]
							,[WorkSectionId]
							,[YearWorkingPeriod]
							,[RequirementWorkMins_esti]
							,[RequirementWorkMins_real]
							,[TypeId] prs_typ_id
							,[EfficiencyRolePoint]
                            ,[DiffNorm]
                    FROM [Personnel]
                    WHERE WorkSectionId = 1 AND YearWorkingPeriod = 139806
                  '''             
             
prs_req = pd.read_sql(query,sql_conn)
chromosom_df = pd.read_sql(query_gene_last,sql_conn)
personnel_df = pd.read_sql(query_personnel, sql_conn)
shift_df = pd.read_sql(query_shift , sql_conn)

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


#--------------------------------------------------------------------
sht = shift_df.reset_index()
sht_2 = sht[sht['ShiftCode']>10]
sht_2['Length'] = sht_2['Length'] // 2
sht_2['ShiftTypeID'] = sht_2['ShiftTypeID'] // 10
sht_2.index = [7,8,9]
sht['Length'] = sht['Length'] // 2
sht['ShiftTypeID'] = sht['ShiftTypeID'] % 10
sht = sht.append(sht_2)
df = pd.melt(chromosom_df.reset_index(), 
             id_vars=['PersonnelBaseId',
                      'prs_typ_id',
                      'EfficiencyRolePoint',
                      'RequirementWorkMins_esti',
                     
                     ],
             var_name='Day', 
             value_name='ShiftCode')
df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
#-------------------------------------
df['Assigned'] = 1
df_req = prs_req.merge(df, 
                       left_on =['PersonnelBaseId','Day','ShiftTypeID'],
                       right_on=['PersonnelBaseId','Day','ShiftTypeID'],
                       how='left'
                      )
df_req = df_req.fillna(-1)

df_req['cost'] = df_req['Assigned']*df_req['Value']










 
