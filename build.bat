@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    Auto Build Python App to EXE
echo ========================================

set "APP_NAME=Area Calculator"
set "MAIN_FILE=src/app.py"
set "VENV_DIR=.venv1"
set "REQUIREMENTS=requirements.txt"
set "COPY_FILE=placeholder.png"

echo Python найден: 
py.exe --version

echo Проверяем наличие requirements.txt...
if not exist "%REQUIREMENTS%" (
    echo Ошибка: Файл %REQUIREMENTS% не найден!
    pause
    exit /b 1
)

echo Проверяем наличие основного файла...
if not exist "%MAIN_FILE%" (
    echo Ошибка: Файл %MAIN_FILE% не найден!
    pause
    exit /b 1
)

echo Удаляем старое виртуальное окружение если существует...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"

echo Создаем виртуальное окружение...
py.exe -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Ошибка при создании venv!
    pause
    exit /b 1
)

echo Активируем venv и устанавливаем зависимости...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Ошибка активации venv!
    pause
    exit /b 1
)

echo Обновляем pip...
py.exe -m pip install --upgrade pip

echo Устанавливаем зависимости из %REQUIREMENTS%...
pip install -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo Ошибка установки зависимостей!
    pause
    exit /b 1
)

echo Устанавливаем pyinstaller...
pip install pyinstaller
if errorlevel 1 (
    echo Ошибка установки pyinstaller!
    pause
    exit /b 1
)

echo Собираем приложение...
pyinstaller --onefile --windowed --name "%APP_NAME%" "%MAIN_FILE%"
if errorlevel 1 (
    echo Ошибка сборки!
    pause
    exit /b 1
)

echo Копируем дополнительные файлы...

copy "src\%COPY_FILE%" "dist\%COPY_FILE%"
echo Файл %COPY_FILE% скопирован в dist/


echo ========================================
echo    Сборка завершена успешно!
echo    EXE файл: dist\%APP_NAME%.exe
echo ========================================

pause