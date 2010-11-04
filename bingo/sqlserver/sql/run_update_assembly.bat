@each off

call bingo_saved_params.bat

set bingo_sqlcmd_arguments=-vbingo=%bingoname% -vbingo_pass=%bingopass% -b -vdatabase=%database% -vdll_directory="%libdir%" -vbingo_assembly_path="%CD%\assembly\bingo-sqlserver" -e

if not "%dbaname%" == "" set bingo_sqlcmd_arguments=%bingo_sqlcmd_arguments% -U %dbaname% 
if not "%dbapass%" == "" set bingo_sqlcmd_arguments=%bingo_sqlcmd_arguments% -P %dbapass%
if not "%server%" == "" set bingo_sqlcmd_arguments=%bingo_sqlcmd_arguments% -S %server%

sqlcmd -i bingo_update_assembly.sql %bingo_sqlcmd_arguments%

copy "%CD%\assembly\lib32\bingo-core-c.dll" "%libdir%\lib32\"
copy "%CD%\assembly\lib64\bingo-core-c.dll" "%libdir%\lib64\"
