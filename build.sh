#!/bin/bash

echo "========================================"
echo "    Auto Build Python App to EXE"
echo "========================================"

APP_NAME="Area Calculator"
MAIN_FILE="src/app.py"
VENV_DIR=".venv1"
REQUIREMENTS="requirements.txt"
COPY_FILE="placeholder.png"

echo "Python найден:"
python3 --version

echo "Проверяем наличие requirements.txt..."
if [ ! -f "$REQUIREMENTS" ]; then
    echo "Ошибка: Файл $REQUIREMENTS не найден!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Проверяем наличие основного файла..."
if [ ! -f "$MAIN_FILE" ]; then
    echo "Ошибка: Файл $MAIN_FILE не найден!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Удаляем старое виртуальное окружение если существует..."
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
fi

echo "Создаем виртуальное окружение..."
python3 -m venv "$VENV_DIR"
if [ $? -ne 0 ]; then
    echo "Ошибка при создании venv!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Активируем venv и устанавливаем зависимости..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "Ошибка активации venv!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Обновляем pip..."
python3 -m pip install --upgrade pip

echo "Устанавливаем зависимости из $REQUIREMENTS..."
pip install -r "$REQUIREMENTS"
if [ $? -ne 0 ]; then
    echo "Ошибка установки зависимостей!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Устанавливаем pyinstaller..."
pip install pyinstaller
if [ $? -ne 0 ]; then
    echo "Ошибка установки pyinstaller!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Собираем приложение..."
pyinstaller --onefile --windowed --name "$APP_NAME" "$MAIN_FILE"
if [ $? -ne 0 ]; then
    echo "Ошибка сборки!"
    read -p "Нажмите Enter для продолжения..."
    exit 1
fi

echo "Копируем дополнительные файлы..."
cp "src/$COPY_FILE" "dist/$COPY_FILE"
echo "Файл $COPY_FILE скопирован в dist/"

echo "========================================"
echo "    Сборка завершена успешно!"
echo "    EXE файл: dist/$APP_NAME"
echo "========================================"

read -p "Нажмите Enter для продолжения..."