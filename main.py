import pandas as pd
import pyodbc

sql_conn = pyodbc.connect('''DRIVER={SQL Server Native Client 11.0};
                             SERVER=10.2.5.17\MSSQLSERVER2017;
                             DATABASE=AdventureWorks2017;
                             Integrated_Security=false;
                             Trusted_Connection=yes;
                             UID=sa;
                             PWD=1qaz!QAZ
                          ''') 
query = '''SELECT [BusinessEntityID],[FirstName],[LastName],
                 [PostalCode],[City] FROM [Sales].[vSalesPerson]
        '''
df = pd.read_sql(query, sql_conn)

df.head(3)

cursor = sql_conn.cursor()

print(df.info)

cursor.close()
sql_conn.close()    