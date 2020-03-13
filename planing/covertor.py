# -*- coding: utf-8 -*-
import pandas as pd

data_xls = pd.read_excel('attractions2.xlsx', 'Sheet1', index_col=None)
data_xls.to_csv('attractions2.csv', encoding='utf-8', index=False)

