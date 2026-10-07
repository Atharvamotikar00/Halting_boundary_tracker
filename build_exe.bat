@echo off
echo Installing dependencies...
python -m pip install -r requirements.txt
echo Building executable...
python -m PyInstaller --onefile --windowed --name HaltingBoundaryTracker main.py
echo.
echo Done. Your program is at dist\HaltingBoundaryTracker.exe
pause
