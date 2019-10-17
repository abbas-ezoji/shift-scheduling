# -*- coding: utf-8 -*-
"""
    pyeasyga module

"""

import random
import copy
from operator import attrgetter
import numpy as np

from six.moves import range


class GeneticAlgorithm(object):
    """Genetic Algorithm class.

    This is the main class that controls the functionality of the Genetic
    Algorithm.

    A simple example of usage:

    >>> # Select only two items from the list and maximise profit
    >>> from pyeasyga.pyeasyga import GeneticAlgorithm
    >>> input_data = [('pear', 50), ('apple', 35), ('banana', 40)]
    >>> easyga = GeneticAlgorithm(input_data)
    >>> def fitness (member, data):
    >>>     return sum([profit for (selected, (fruit, profit)) in
    >>>                 zip(member, data) if selected and
    >>>                 member.count(1) == 2])
    >>> easyga.fitness_function = fitness
    >>> easyga.run()
    >>> print easyga.best_individual()

    """

    def __init__(self,
                 seed_data,
                 meta_data,
                 population_size=50,
                 generations=100,
                 crossover_probability=0.8,
                 mutation_probability=0.2,
                 elitism=True,
                 maximise_fitness=True):
        """Instantiate the Genetic Algorithm.

        :param seed_data: input data to the Genetic Algorithm
        :type seed_data: list of objects
        :param int population_size: size of population
        :param int generations: number of generations to evolve
        :param float crossover_probability: probability of crossover operation
        :param float mutation_probability: probability of mutation operation

        """

        self.seed_data = seed_data
        self.meta_data = meta_data
        self.population_size = population_size
        self.generations = generations
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.elitism = elitism
        self.maximise_fitness = maximise_fitness

        self.current_generation = []

        def create_individual(data,meta_data):  
            individual = data[:]
            for col in individual.columns :       
                individual[col] = np.random.choice(meta_data.index.values.tolist(),
                                                   size=len(individual))
            return individual

        def crossover(parent_1, parent_2):                       
            child_1, child_2 = parent_1, parent_2
            row, col = parent_1.shape
            for r in range(row):
                crossover_index = (random.randrange(1, col - 1))
                colt = crossover_index
                child_1.iloc[r] = np.append(parent_1.iloc[r, :colt],parent_2.iloc[r, colt:])    
                child_2.iloc[r] = np.append(parent_1.iloc[r , colt:],parent_2.iloc[r, :colt])            
            return child_1, child_2

        def mutate(individual):
            parent = individual
            row , col = parent.shape
            for r in range(row):
                mutate_index1 = random.randrange(1, col)
                mutate_index2 = random.randrange(1, col)                
                parent.iloc[r][mutate_index1], parent.iloc[r][mutate_index2] = parent.iloc[r][mutate_index2], parent.iloc[r][mutate_index1]
        

        def random_selection(population):
            """Select and return a random member of the population."""
            return random.choice(population)

        def tournament_selection(population):
            """Select a random number of individuals from the population and
            return the fittest member of them all.
            """
            if self.tournament_size == 0:
                self.tournament_size = 2
            members = random.sample(population, self.tournament_size)
            members.sort(
                key=attrgetter('fitness'), reverse=self.maximise_fitness)
            return members[0]

        self.fitness_function = None
        self.tournament_selection = tournament_selection
        self.tournament_size = self.population_size // 10
        self.random_selection = random_selection
        self.create_individual = create_individual
        self.crossover_function = crossover
        self.mutate_function = mutate
        self.selection_function = self.tournament_selection

    def create_initial_population(self):
        """Create members of the first population randomly.
        """
        initial_population = []
        for _ in range(self.population_size):
            genes = self.create_individual(self.seed_data,self.meta_data)            
            individual = Chromosome(genes)
            initial_population.append(individual)
        self.current_generation = initial_population

    def calculate_population_fitness(self):
        """Calculate the fitness of every member of the given population using
        the supplied fitness_function.
        """
        for individual in self.current_generation:
            individual.fitness = self.fitness_function(
                individual.genes, self.meta_data)

    def rank_population(self):
        """Sort the population by fitness according to the order defined by
        maximise_fitness.
        """
        self.current_generation.sort(
            key=attrgetter('fitness'), reverse=self.maximise_fitness)
        print('best cost: ' + str(self.current_generation[0].fitness))

    def create_new_population(self):
        """Create a new population using the genetic operators (selection,
        crossover, and mutation) supplied.
        """
        new_population = []
        elite = copy.deepcopy(self.current_generation[0])
        selection = self.selection_function

        while len(new_population) < self.population_size:
            parent_1 = copy.deepcopy(selection(self.current_generation))
            parent_2 = copy.deepcopy(selection(self.current_generation))

            child_1, child_2 = parent_1, parent_2
            child_1.fitness, child_2.fitness = 0, 0

            can_crossover = random.random() < self.crossover_probability
            can_mutate = random.random() < self.mutation_probability

            if can_crossover:
                child_1.genes, child_2.genes = self.crossover_function(
                    parent_1.genes, parent_2.genes)

            if can_mutate:
                self.mutate_function(child_1.genes)
                self.mutate_function(child_2.genes)

            new_population.append(child_1)
            if len(new_population) < self.population_size:
                new_population.append(child_2)

        if self.elitism:
            new_population[0] = elite

        self.current_generation = new_population

    def create_first_generation(self):
        """Create the first population, calculate the population's fitness and
        rank the population by fitness according to the order specified.
        """
        self.create_initial_population()
        self.calculate_population_fitness()
        self.rank_population()

    def create_next_generation(self):
        """Create subsequent populations, calculate the population fitness and
        rank the population by fitness in the order specified.
        """
        self.create_new_population()
        self.calculate_population_fitness()
        self.rank_population()

    def run(self):
        """Run (solve) the Genetic Algorithm."""
        print('start: '+ strftime("%Y-%m-%d %H:%M:%S:%SS", gmtime()))
        self.create_first_generation()

        for g in range(1, self.generations):
            print('---------- Start ---------------')            
            print('generation-' +str(g) + ' -> start: '+ strftime("%Y-%m-%d %H:%M:%S:%SS", gmtime()))
            self.create_next_generation()            
            print('----------- End ----------------')

    def best_individual(self):
        """Return the individual with the best fitness in the current
        generation.
        """
        best = self.current_generation[0]        
        return (best.fitness, best.genes)

    def last_generation(self):
        """Return members of the last generation as a generator function."""
        return ((member.fitness, member.genes) for member
                in self.current_generation)


class Chromosome(object):
    """ Chromosome class that encapsulates an individual's fitness and solution
    representation.
    """
    def __init__(self, genes):
        """Initialise the Chromosome."""
        self.genes = genes
        self.fitness = 0

    def __repr__(self):
        """Return initialised Chromosome representation in human readable form.
        """
        return repr((self.fitness, self.genes))