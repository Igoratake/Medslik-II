#!/bin/bash

# set where you have placed MEDSLIK_II folder
HOME_MEDSLIK=/users_home/opa/ia19223/Medslik-II/MEDSLIK_II_3.01

MEDSLIK=${HOME_MEDSLIK}/RUN

# generate update timelog file
start_time=$(date +%s.%N)
echo "`date +'%Y-%m-%d %H:%M:%S'` `date +%s` `hostname` start EXE" > ${MEDSLIK}/timelog.log

# launches model
source ${MEDSLIK}/medslik_II.sh

# update timelog file
end_date=$(date +%s.%N)
exec_time=$(echo "(${end_date}-${start_time})" | bc)
echo "`date +'%Y-%m-%d %H:%M:%S'` `date +%s` `hostname` end EXE - Execution time: ${exec_time} sec. " >> ${MEDSLIK}/timelog.log

