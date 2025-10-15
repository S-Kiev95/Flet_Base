@echo off
REM Script para iniciar la aplicación Flet
REM Guarda este archivo como: run.bat

echo ========================================
echo   Iniciando aplicacion Flet
echo ========================================
echo.

REM Activar el entorno virtual
echo [1/2] Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Verificar que se activo correctamente
if %errorlevel% neq 0 (
    echo.
    echo ERROR: No se pudo activar el entorno virtual
    echo Verifica que existe la carpeta .venv
    pause
    exit /b 1
)

echo [OK] Entorno virtual activado
echo.

REM Ejecutar la aplicación
echo [2/2] Ejecutando aplicacion...
echo.
python main.py

REM Si hay error, pausar para ver el mensaje
if %errorlevel% neq 0 (
    echo.
    echo ERROR: La aplicacion termino con errores
    pause
)

REM Desactivar entorno virtual al salir
deactivate