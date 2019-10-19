import random
from multiprocessing import Pool
import prs_day_based



if __name__ == '__main__':
    pool = Pool()
    to_factor = [ random.randint(100000, 50000000) for i in range(20)]
    results = pool.map(prs_day_based, to_factor)
    for value, factors in zip(to_factor, results):
        print("The factors of {} are {}".format(value, factors))