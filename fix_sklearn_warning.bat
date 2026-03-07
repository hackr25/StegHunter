@echo off
:: Fix sklearn parallel processing warning
set SKLEARN_NO_OPENMP=1
set NUMEXPR_MAX_THREADS=1
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
python steg_hunter_gui.py
pause
