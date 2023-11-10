# [MEDSLIK-II](http://www.medslik-ii.org/index.html) v2.00 (07/2018)

MEDSLIK-II software can be run on GNU/Linux Operative Systems.
> You can download MEDSLIK-II source code from the [website](http://www.medslik-ii.org/users/login.php), after registering.

## GET STARTED in 3 STEPS!
1. You need to install conda or miniconda with python3.x, following the instructions on conda [website](https://docs.conda.io/projects/miniconda/en/latest/). Then, create a new conda environment with pip.
```
conda create --name mdk2.00
conda activate mdk2.00
```
2. Extract the tarball contents and enter the main software folder. Install pip requirements
```
tar –zxvf MEDSLIK_II_v2.tar.gz MEDSLIK_II_v2
cd MEDSLIK_II_v2
pip install -r pip_requirements.txt
```
3. You can now run the test case for Medslik II (v2.00).
```
chmod +x run_testcase.sh
sudo ./run_testcase.sh
```

For more details about running MEDSLIK-II 2.00 and installing software requirements, please see the [documentation folder](https://github.com/Igoratake/Medslik-II/tree/medslik_II_2_00/doc/).

# Enjoy!
