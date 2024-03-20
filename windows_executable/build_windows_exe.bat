@echo off
echo.
echo [32mBuilding afflux.exe...[0m
echo.
set PYTHONOPTIMIZE=2 && pyinstaller --clean --distpath . afflux.spec
echo.
echo [32mDone.[0m
echo.