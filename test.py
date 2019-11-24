from time import gmtime, strftime, sleep

start_time = gmtime()
sleep(3)
end_time = gmtime()
t = (end_time[5] - start_time[5])