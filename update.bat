@echo off

chcp 65001

set /p x="(U - Update) / (C - Create hash file) Enter U or C: "

python ".\handlers\updateUtility.py" %x%

pause