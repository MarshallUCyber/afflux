@echo off
echo.
echo [32mInstalling dependancies...[0m
winget install -e --id Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools;includeRecommended"
cd .\windows_executable\
pip install pybindgen
tar xzvf fastchunking-0.0.3.tar.gz
cd .\fastchunking-0.0.3\
python setup.py build
python setup.py install
cd ..
echo [32mInstalling Snappy...[0m
pip install python_snappy-0.6.1-cp311-cp311-win_amd64.whl
echo [32mFinishing dependancies...[0m
cd ..
pip install -r requirments_windows.txt
echo [32mInstalling PyAFF4...[0m
cd .\pyaff4\
python setup.py install
echo [32mInstalling PyMobildeDevice3...[0m
cd ..\pymobiledevice3
python setup.py install
cd ..
echo [32mDone.[0m