@echo off

chcp 65001

set /p Data="(U - Update) / (C - Create hash file) Enter U or C: "

python "D:\Проекты\Программы\Python\Sharmanka-2.0\handlers\updateUtility.py" %Data%

pause