@echo off
rem Launch the assignment-1 Gradio page for manual testing.
rem (Full web_demo.py cannot start on gradio 3.36.1: UI.py hw3 uses gr.ImageEditor.)
cd /d "%~dp0"
python "tests\ui_smoke_hw1.py" --serve
pause
