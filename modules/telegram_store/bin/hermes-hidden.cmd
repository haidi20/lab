@echo off
setlocal
set "NODE_EXE=E:\apps\nodejs\node.exe"
set "HERMES_JS=C:\Users\nhaid\AppData\Roaming\npm\node_modules\hermes-agent\bin\hermes.js"
"%NODE_EXE%" "%HERMES_JS%" %*
