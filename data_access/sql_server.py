# -*- coding: utf-8 -*-

import pandas as pd
import pyodbc

class data(object): 
    def __init__(self, 
                 conn_str, 
                 query_gene_last,
                 query_gene_new,
                 query_personnel,
                 query_shift,
                 query_shift_req
                 ):
        # -------------------- Connection String -----------------------------#
        self.conn_str = conn_str
        self.sql_conn = pyodbc.connect(self.conn_str)
        # ------------------ Query for gene pivoted --------------------------#
        self.query_gene_last = query_gene_last
        self.query_gene_new = query_gene_new
        # ----------------- Query for personnel info -------------------------#
        self.query_personnel = query_personnel        
        # -------------------Query for shift info-----------------------------#
        self.query_shift = query_shift  
        # -------------------Query for shift_req info-------------------------#
        self.query_shift_req = query_shift_req        
        #---------------------------------------------------------------------#         
        self.cursor = self.sql_conn.cursor() 
        
        self.new = 0
               
    def get_sql_conn(self):
        sql_conn = self.sql_conn
        return sql_conn
        
    def get_chromosom(self):
        chromosom_df = pd.read_sql(self.query_gene_last, self.sql_conn)
        if(chromosom_df.empty):              
            self.new = 1
            chromosom_df = pd.read_sql(self.query_gene_new, self.sql_conn)
        return chromosom_df
    
    def get_personnel(self):
        personnel_df = pd.read_sql(self.query_personnel,self.sql_conn)    
        return personnel_df
    
    def get_shift(self):
        shift_df = pd.read_sql(self.query_shift,self.sql_conn)
        return shift_df
    
    def get_day_req(self):
        day_req_df = pd.read_sql(self.query_shift_req,self.sql_conn)
        return day_req_df
        
    def delete_last_sol(self,work_sction_id,year_working_period):
        cursor = self.cursor
        query_delete = '''delete from PersonnelShiftDateAssignments 
                          where WorkSectionId ={0} and YearWorkingPeriod = {1}
                        '''.format(work_sction_id,year_working_period)
        cursor.execute(query_delete)
        self.sql_conn.commit()                     
    def is_new(self):
        return self.new
    def insert_sol(self, sol_tbl, personnel_df, sol_fitness,
                   work_sction_id,year_working_period): 
        cursor = self.cursor  
        query_last = '''select * from PersonnelShiftDateAssignments 
                          where WorkSectionId ={0} and YearWorkingPeriod = {1}
                        '''.format(work_sction_id,year_working_period)
        last_df = pd.read_sql(query_last,self.sql_conn)
        last_cost = last_df['Cost'].min()        
        if(last_cost > sol_fitness):
            query_delete = '''delete from PersonnelShiftDateAssignments 
                              where WorkSectionId ={0} and YearWorkingPeriod = {1}
                            '''.format(work_sction_id,year_working_period)
            cursor.execute(query_delete)
        for i in range(len(sol_tbl)):
            cursor.execute('''insert into PersonnelShiftDateAssignments  
                               values (?, ?, ?, ?, ?, ?, ?, ?)'''
                               ,(sol_tbl[i])
                               )                
# =============================================================================
#         for prs in personnel_df.index:
#             cursor.execute('''update [Personnel]
#                               set [DiffNorm] = ?
#                               where [PersonnelBaseId] = ? and
#                                     [WorkSectionId] = ? and
#                                     [YearWorkingPeriod] = ?
#                            ''',
#                            (float(personnel_df.loc[prs,'DiffNorm']),
#                             prs,
#                             int(personnel_df.loc[prs,'WorkSectionId']),
#                             int(personnel_df.loc[prs,'YearWorkingPeriod'])
#                             )
#                            )
#          
# =============================================================================
        self.sql_conn.commit()