# -*- coding: utf-8 -*-

import pandas as pd
import pyodbc

class data(object): 
    def __init__(self, conn_str, query_gene ,query_personnel ,query_shift):
        # -------------------- Connection String -----------------------------#
        self.conn_str = conn_str
        self.sql_conn = pyodbc.connect(self.conn_str)
        # ------------------ Query for gene pivoted --------------------------#
        self.query_gene = query_gene
        # ----------------- Query for personnel info -------------------------#
        self.query_personnel = query_personnel        
        # -------------------Query for shift info-----------------------------#
        self.query_shift = query_shift        
        #-------------------------------------------------------------------         
        self.cursor = self.sql_conn.cursor()                
               
    def get_sql_conn(self):
        sql_conn = self.sql_conn
        return sql_conn
        
    def get_chromosom(self):
        chromosom_df = pd.read_sql(self.query_gene, self.sql_conn)
        return chromosom_df
    
    def get_personnel(self):
        personnel_df = pd.read_sql(self.query_personnel,self.sql_conn)    
        return personnel_df
    
    def get_shift(self):
        shift_df = pd.read_sql(self.query_shift,self.sql_conn)
        return shift_df
        
    def truncate(self):
        cursor = self.cursor
        cursor.execute('''truncate table PersonnelShiftDateAssignments''')
        self.sql_conn.commit()                     
    
    def insert_sol(self, sol_df, personnel_df, sol_fitness): 
        cursor = self.cursor             
        year_workingperiod = 1398 * 100 + 3
        prs_count,day_count = sol_df.shape                      
        for prs in personnel_df.index:
            prs_count = prs_count + 1
            for day in range(day_count): 
                cursor.execute('''insert into PersonnelShiftDateAssignments 
                               values (?, ?, ?, ?, ?)'''
                               ,(prs,
                                 year_workingperiod * 100 + day+1,
                                 int(sol_df.loc[prs][[day+1]]),
                                 1,                                 
                                 sol_fitness)
                               )
        
        
         
        self.sql_conn.commit()                     
       
    


