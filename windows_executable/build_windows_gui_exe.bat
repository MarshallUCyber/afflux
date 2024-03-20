@echo off
echo.
echo [32mBuilding afflux_gui.exe...[0m
echo.
set PYTHONOPTIMIZE=2 && pyinstaller --clean --distpath . afflux_gui.spec
echo.
echo [32mDone.[0m
echo.