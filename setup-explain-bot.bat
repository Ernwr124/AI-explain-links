@echo off
chcp 65001 > nul
title Установка Explain Bot

echo.
echo #######################################################
echo #       Установка Explain Bot - начало               #
echo #######################################################
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo !!! ОШИБКА: Python не установлен или не добавлен в PATH
    echo Пожалуйста, установите Python 3.8+ с сайта python.org
    echo И убедитесь, что выбрали опцию "Add Python to PATH"
    pause
    exit /b 1
)

REM Проверка версии Python
for /f "tokens=2 delims= " %%A in ('python --version 2^>^&1') do set "python_version=%%A"
for /f "tokens=1,2 delims=." %%A in ("%python_version%") do (
    if %%A LSS 3 (
        echo.
        echo !!! ОШИБКА: Требуется Python 3.8 или выше (у вас версия %python_version%)
        pause
        exit /b 1
    )
    if %%A EQU 3 if %%B LSS 8 (
        echo.
        echo !!! ОШИБКА: Требуется Python 3.8 или выше (у вас версия %python_version%)
        pause
        exit /b 1
    )
)

echo.
echo === Установка Python библиотек ===

REM Функция для установки библиотек
:install_lib
set lib_name=%~1
set lib_import=%~2
if "%~2"=="" set lib_import=%lib_name%

echo Проверяем %lib_name%...
python -c "import %lib_import%" >nul 2>&1
if %errorlevel% equ 0 (
    echo %lib_name% уже установлен
    goto :EOF
)

echo Устанавливаем %lib_name%...
pip install %lib_name% --quiet
if %errorlevel% neq 0 (
    echo.
    echo !!! ОШИБКА при установке %lib_name%
    pause
    exit /b 1
)
echo %lib_name% успешно установлен
goto :EOF

REM Установка основных зависимостей
call :install_lib "python-telegram-bot" "telegram"
call :install_lib "requests" "requests"
call :install_lib "beautifulsoup4" "bs4"
call :install_lib "readability-lxml" "readability"
call :install_lib "ollama" "ollama"
call :install_lib "youtube-transcript-api" "youtube_transcript_api"
call :install_lib "google-api-python-client" "googleapiclient"

echo.
echo === Установка модели Ollama ===
ollama list | find "granite3.3:2b" >nul 2>&1
if %errorlevel% equ 0 (
    echo Модель granite3.3:2b уже установлена
) else (
    echo Устанавливаем модель granite3.3:2b...
    ollama pull granite3.3:2b
    if %errorlevel% neq 0 (
        echo.
        echo !!! ОШИБКА при установке модели
        echo Попробуйте вручную: ollama pull granite3.3:2b
        pause
    )
)

echo.
echo === Настройка окружения ===
if not exist config.py (
    echo Создаем файл конфигурации...
    echo TELEGRAM_TOKEN = "ваш_токен" > config.py
    echo YOUTUBE_API_KEY = "ваш_api_key" >> config.py
    echo MAX_TEXT_LENGTH = 4000 >> config.py
)

echo.
echo #######################################################
echo #       Установка завершена!                          #
echo #                                                    #
echo # 1. Отредактируйте config.py, добавив:              #
echo #    - TELEGRAM_TOKEN (получить @BotFather)          #
echo #    - YOUTUBE_API_KEY (console.cloud.google.com)    #
echo #                                                    #
echo # 2. Запустите бота командой:                        #
echo #    python explain-bot.py                           #
echo #                                                    #
echo # 3. Для работы с YouTube видео нужен API ключ       #
echo #######################################################
echo.

pause