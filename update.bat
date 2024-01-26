@echo off

chcp 65001

set /p Data="(U - Update) / (C - Create hash file) Enter U or C: "

python ".\handlers\updateUtility.py" %Data%

pause