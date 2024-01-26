import os
import sys
import hashlib
import requests
import subprocess

FULL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMMANDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'commands')
HANDLERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'handlers')
UPDATETOOL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')

CONSOLE_ARGV = sys.argv[1]

def createHashFile():
    hashList = []

    for _, source in enumerate([COMMANDS_DIR, HANDLERS_DIR, UPDATETOOL_DIR]):
        os.chdir(source)
        for _, source in enumerate(os.listdir(path='.')):
            try:
                if source != 'updateUtility.py':
                    hashList.append(hashlib.md5(open(f"{source}", 'rb').read()).hexdigest())
            except: continue

    with open(f"{FULL_DIR}\\hashFile.txt", "w") as file:
        for hash in hashList:
            file.writelines(f"{hash}\n")

    os.chdir(FULL_DIR)
    print(f"[UPDATE] Successefully created hash file!")

def compareHash():
    InternalHash = []
    ExternalHash = []

    with open(f"hashFile.txt", "r") as file:
        InternalHash.extend(file.read().splitlines())
    ExternalHash.extend(requests.get('https://github.com/UnluckyRu/Sharmanka-2.0/blob/development/hashFile.txt').json()['payload']['blob']['rawLines'])

    print(f"[UPDATE] Compare is finished! (2/3)")

    if sorted(InternalHash) == sorted(ExternalHash): 
        print(f"[UPDATE] Update not needed! (3/3)")
        return False
    else:
        return True

def updatingBot():
    try:
        createHashFile()
    except FileNotFoundError:
        subprocess.run([rf"{FULL_DIR}\tools\UpdateTool.bat"])
        print("[UPDATE] Recovery and update successfull complete! (3/3)")
        return
    
    if compareHash():
        subprocess.run([rf"{FULL_DIR}\tools\UpdateTool.bat"])
        print("[UPDATE] Update successfull complete! (3/3)")

if CONSOLE_ARGV == 'U':
    updatingBot()
if CONSOLE_ARGV == 'C':
    createHashFile()
