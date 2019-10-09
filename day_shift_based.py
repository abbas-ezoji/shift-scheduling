import numpy as np
import pandas as pd
import pyodbc
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
            	   Code SHIFTID
            	  ,PersianDayOfMonth
            	  ,NULL PersonnelBaseId
               FROM 
    	          Shifts S JOIN 
                  Dim_Date D ON D.PersianYear = 1398 AND PersianMonth=3
            '''
chromosom_df = pd.read_sql(query_gene, sql_conn)
chromosom_df.head(3)
chromosom_df = pd.pivot_table(chromosom_df, values='PersonnelBaseId'
                              , index=['PersianDayOfMonth'],
                              columns=['SHIFTID'], aggfunc=np.sum)

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

# -----------------------Randomize gene---------------------------------------#
prs_count = personnel_df.count(axis = 0)
for col in chromosom_df.columns :       
    chromosom_df[col] = chromosom_df.apply(lambda row : np.random.randint(0,prs_count)
                                            ,axis=1)
    
# -----------------------Query for personnel info-----------------------------#


# ----------------Query for insert shift assignment info----------------------#
cursor = sql_conn.cursor()
year_workingperiod = 1398 * 100 + 3
day_count,shift_count = chromosom_df.shape                     
cursor.execute('''truncate table PersonnelShiftDateAssignments''')

for shift in range(shift_count):    
    for day in range(day_count): 
        cursor.execute('''insert into PersonnelShiftDateAssignments 
                       values (?, ?, ?, ?, ?)'''
                       ,( personnel_df.loc[chromosom_df.loc[day+1][[shift+1]]][[1]] # personnelID
                         ,shift+1                     # 
                         ,year_workingperiod * 100 + day+1,0,0)
                       )       

sql_conn.commit()                     

