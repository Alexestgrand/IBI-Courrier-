@echo off
pip install pyinstaller customtkinter pillow reportlab bcrypt
python -m PyInstaller build.spec --noconfirm
copy README_INSTALLATION.txt dist\IBI_COURRIERS\
copy README_TECHNIQUE.txt dist\IBI_COURRIERS\
echo Build termine : dist\IBI_COURRIERS\IBI_COURRIERS.exe
