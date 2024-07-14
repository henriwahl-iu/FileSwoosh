#!/usr/bin/env python3
# © 2024 Henri Wahl

from os import environ
from pathlib import Path
from shutil import rmtree
from subprocess import run
from zipfile import ZipFile, ZIP_DEFLATED

from app.config import PORT
from version import VERSION

# Remove build and dist directories for a clean build
for directory in ['build', 'dist']:
   rmtree(directory, ignore_errors=True)

NAME = 'FileSwoosh'
NAME_SETUP = f'{NAME}_Setup'

PYINSTALLER_ARGS = ['pyinstaller',
                    '--name', NAME,
                    '--windowed',
                    '--add-data', 'resources/:resources/',
                    '--icon', 'resources/images/logo.ico',
                    'main.py']

SIGNING = False
if 'WIN_SIGNING_CERT_BASE64' in environ \
        and 'WIN_SIGNING_PASSWORD' in environ:
    SIGNING = True

# build the app in folder
run(PYINSTALLER_ARGS)

# build the app as one file
run(PYINSTALLER_ARGS + ['--onefile'])

if SIGNING:
    # sign the exe file in folder
    run(args=f'powershell.exe deploy/code_signing.ps1 dist/{NAME}/{NAME}.exe')
    # sign the onefile exe file
    run(args=f'powershell.exe deploy/code_signing.ps1 dist/{NAME}.exe')

# Zip the folder
zip_name = f'dist/{NAME}.zip'
dist_path = Path('dist') / NAME
with ZipFile(zip_name, 'w', ZIP_DEFLATED) as zip_file:
    for file_path in dist_path.rglob('*'):
        zip_file.write(file_path, file_path.relative_to(dist_path))
print(f'Created zipfile: {zip_name}')

run(args=f'iscc /O.\\dist /Dversion={VERSION} /Dapp_name={NAME} /Doutput_base_filename={NAME_SETUP} /Dport={PORT} deploy\\FileSwoosh.iss', shell=True)

if SIGNING:
    # sign the installer
    run(args=f'powershell.exe deploy/code_signing.ps1 dist/{NAME_SETUP}.exe')