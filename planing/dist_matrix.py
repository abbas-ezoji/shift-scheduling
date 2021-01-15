import requests
import time
import pandas as pd
from sqlalchemy import create_engine

USER = 'planuser'
PASSWORD = '1qaz!QAZ'
HOST = 'localhost'
PORT = '5432'
NAME = 'planing'
db_connection_url = "postgresql://{}:{}@{}:{}/{}".format(USER,
                                                         PASSWORD,
                                                         HOST,
                                                         PORT,
                                                         NAME
                                                        )
engine = create_engine(db_connection_url)
df = pd.read_sql_query(''' SELECT 
                                 O.city AS CITY
                            	,O.ID AS ORIGIN
                            	,D.ID AS DIST
                            	,O.latt AS ORIG_LATT
                            	,O.long AS ORIG_LONG
                            	,D.latt AS DIST_LATT
                            	,D.long AS DIST_LONG
                            FROM
                            	plan_attractions O
                            	JOIN plan_attractions D ON O.city = D.city
                            WHERE O.city = 'استانبول'
                            ORDER BY O.city, O.ID, D.ID
                       '''
                          ,con=engine)
df['weight'] = 0
df['duration'] = 0
df['distance'] = 0

for ind in df.index:
          
     status = ''
     while status != 'Ok':
         origin = str(df.iloc[ind][3]) + ',' + str(df.loc[ind][4])
         dist   = str(df.loc[ind][5]) + ',' + str(df.loc[ind][6])
         url = 'http://router.project-osrm.org/route/v1/driving/{0};{1}?overview=false'\
                    .format(origin, dist)
                    
         r = requests.get(url)
         data = r.json() 
         try:
             status = data['code']
         except:
             status = ''
         if status != 'Ok':
             time.sleep(0.5)         
          
     t = data['routes'][0]
     t = t['legs'][0]
     
     df.at[ind,'weight'] = t['weight']
     df.at[ind,'duration'] = t['duration']
     df.at[ind,'distance'] = t['distance']
     print('index: ' + str(ind) + ' - ' + str(t['duration']))

df.to_csv('mat.csv') 
     