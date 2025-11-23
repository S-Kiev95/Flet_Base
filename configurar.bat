@echo off
echo ==========================================
echo Configuracion de LaMilagrosa (Supabase)
echo ==========================================
echo.

REM Configuración de Supabase (cambiar estos valores)
set USUARIO=postgres
set PASSWORD=LaMilagrosa2025
set HOST=db.wkyydhqiuvbpgigufzzv.supabase.co
set PUERTO=5432
set DATABASE=postgres

set DB_URL=postgresql+psycopg2://%USUARIO%:%PASSWORD%@%HOST%:%PUERTO%/%DATABASE%

echo Configurando variable de entorno...
setx DATABASE_URL "%DB_URL%"

echo.
echo ==========================================
echo Configuracion completada!
echo Por favor REINICIE la aplicacion
echo ==========================================
pause