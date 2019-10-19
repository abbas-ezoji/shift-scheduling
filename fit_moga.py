def fitness (individual, meta_data, fit_count):
    sht = shift_df.reset_index()
    df = pd.melt(individual.reset_index(), 
                 id_vars=['PersonnelBaseId',
                          'TypeId',
                          'EfficiencyRolePoint',
                          'RequirementWorkMins_esti'
                         ],
                 var_name='Day', 
                 value_name='ShiftCode')
    df = df.merge(sht, left_on='ShiftCode', right_on='ShiftCode', how='inner')
    if (fit_count==1):
        cost = calc_day_const(df, sum_typid_req)
    elif (fit_count==2):
        cost = calc_prs_const(df, sum_typid_req)
    else:
        day_const = 0.8*calc_day_const(df, sum_typid_req)
        prs_const = 0.2*calc_prs_const(df, sum_typid_req)
        cost = day_const + prs_const
        
    return cost