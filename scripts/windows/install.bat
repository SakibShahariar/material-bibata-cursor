@echo off
REM Material Bibata Cursor — Windows Installer
REM Usage: install.bat [theme_name]
REM   No arg: installs all themes
REM   With arg: installs single theme (e.g. install.bat Ice-Blue)

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
set "INSTALL_DIR=%LOCALAPPDATA%\Icons"
set "CURSOR_DIR=%INSTALL_DIR%\Bibata-Material"

echo ============================================
echo  Material Bibata Cursor — Windows Installer
echo ============================================
echo.

REM --- Check prerequisites ---
if not exist "%CURSOR_DIR%" (
    echo Error: No compiled cursors found at %CURSOR_DIR%
    echo Run ^'^ python3 scripts/build_windows.py ^'^ first.
    echo.
    pause
    exit /b 1
)

echo Installing cursors to %INSTALL_DIR% ...
echo.

set "count=0"
set "fail=0"

for /d %%T in ("%CURSOR_DIR%\*") do (
    set "name=%%~nxT"
    echo Processing !name! ...

    if "%1"=="" (
        REM --- Install all themes ---
        if exist "%%T\*.cur" (
            xcopy "%%T\*.cur" "%INSTALL_DIR%\%%~nxT\" /Y /Q >nul
            if !errorlevel! equ 0 (
                echo   ✓ Copied !name! cursors
                set /a count+=1
            ) else (
                echo   ✗ Failed to copy !name!
                set /a fail+=1
            )
        ) else (
            echo   ✗ No .cur files in !name!
            set /a fail+=1
        )
    ) else (
        REM --- Install single theme ---
        if /i "!name!"=="Bibata-Material-%1" (
            if exist "%%T\*.cur" (
                xcopy "%%T\*.cur" "%INSTALL_DIR%\%%~nxT\" /Y /Q >nul
                if !errorlevel! equ 0 (
                    echo   ✓ Copied !name!
                    set /a count+=1
                ) else (
                    echo   ✗ Failed to copy !name!
                    set /a fail+=1
                )
            ) else (
                echo   ✗ No .cur files in !name!
                set /a fail+=1
            )
        )
    )
)

echo.
echo ============================================
echo  Installed !count! theme(s), !fail! failed
echo ============================================
echo.

REM --- Apply cursor theme via registry ---
if "%1"=="" (
    echo To apply a cursor theme, open Windows Settings:
    echo   Settings → Personalization → Colors →
    echo   "Edit your settings" → "Cursor size"
    echo.
    echo Or run this command for a specific theme:
    echo   install.bat ^<theme_name^>
) else (
    echo Theme %1 installed. Apply it via:
    echo   gsettings set org.gnome.desktop.interface cursor-theme ^
    echo     "Bibata-Material-%1"
)
echo.
echo You may need to log out and back in for changes to take effect.
echo.
pause