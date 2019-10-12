import pandas as pd
import numpy as np
from libs import GA_dataframes as ga

chromosom_df = pd.DataFrame(np.random.randint(15, size=(4, 30)),
                            index = ['A', 'B', 'C', 'D'],
                            columns = pd.date_range('1/1/2019', periods=30) )

individual = chromosom_df.sample(frac=1).reset_index(drop=False)
# =============================================================================
# ga = ga.GeneticAlgorithm(chromosom_df,
#                       population_size=200,
#                       generations=5,
#                       crossover_probability=0.8,
#                       mutation_probability=0.2,
#                       elitism=True,
#                       maximise_fitness=False)
# def fitness(individual, data):
#     sigma = 0.5
#     mu = 0.8
#     return sigma * np.random.randn(1) + mu
# 
# ga.fitness_function = fitness               # set the GA's fitness function
# ga.run()                                    # run the GA
# sol_fitness, sol_df = ga.best_individual()                # print the GA's best solution
# =============================================================================

