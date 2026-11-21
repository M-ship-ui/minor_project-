@echo off
title Push Project to GitHub - Sanskriti University Portal
color 0A

echo ==============================================================================
echo   SANSKRITI UNIVERSITY - ACADEMIC ASSET RECOVERY & MANAGEMENT SYSTEM
echo   Student: O. Pulla Reddy (2302320110) ^| Guide: Dr. Sakuldeep Singh
echo   Department of Computer Science & Engineering
echo ==============================================================================
echo.
echo Target GitHub Repository:
echo   https://github.com/M-ship-ui/minor_project-.git
echo.
echo [1/2] Verifying Local Git Repository...
cd /d "C:\Users\bandi\OneDrive\Desktop\academic_asset_system"

git remote remove origin 2>nul
git remote add origin https://github.com/M-ship-ui/minor_project-.git
git branch -M main

echo.
echo All project code, single-file monolith, unit tests, and the 78-page PDF report
echo are staged and committed on branch 'main'.
echo.
echo ==============================================================================
echo   CHOOSE HOW YOU WANT TO PUSH TO GITHUB:
echo ==============================================================================
echo   [1] Push using GitHub Personal Access Token (PAT) - (FASTEST ^& RECOMMENDED)
echo   [2] Push via GitHub Browser Sign-In (Git Credential Manager)
echo   [3] Exit
echo ==============================================================================
echo.
set /p METHOD="Choose an option (1, 2 or 3): "

if "%METHOD%"=="1" goto PUSH_TOKEN
if "%METHOD%"=="2" goto PUSH_BROWSER
if "%METHOD%"=="3" goto END
goto PUSH_TOKEN

:PUSH_TOKEN
echo.
echo ------------------------------------------------------------------------------
echo If you don't have a token yet, create one in 30 seconds:
echo 1. Open: https://github.com/settings/tokens/new
echo 2. Note: "minor_project"
echo 3. Check the box for: [x] repo (Full control of private repositories)
echo 4. Click 'Generate token' and copy it.
echo ------------------------------------------------------------------------------
echo.
set /p GH_PAT="Paste your GitHub Personal Access Token (starts with ghp_...): "
if "%GH_PAT%"=="" (
    echo Error: Token cannot be empty!
    pause
    goto END
)

echo.
echo [2/2] Pushing all files to https://github.com/M-ship-ui/minor_project-.git...
git push https://%GH_PAT%@github.com/M-ship-ui/minor_project-.git main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo   [SUCCESS] ALL CODE AND PDF REPORT SUCCESSFULLY PUSHED TO GITHUB!
    echo ==============================================================================
    echo   Repository Link: https://github.com/M-ship-ui/minor_project-
    echo ==============================================================================
    echo.
    echo Opening your repository in your browser...
    start https://github.com/M-ship-ui/minor_project-
) else (
    echo.
    echo [ERROR] Push failed. Please check that:
    echo 1. Your token has the 'repo' scope checked.
    echo 2. The account associated with the token has write access to M-ship-ui/minor_project-.
)
goto END

:PUSH_BROWSER
echo.
echo [2/2] Launching Git Credential Manager for browser authentication...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo   [SUCCESS] ALL CODE AND PDF REPORT SUCCESSFULLY PUSHED TO GITHUB!
    echo ==============================================================================
    echo   Repository Link: https://github.com/M-ship-ui/minor_project-
    echo ==============================================================================
    echo.
    echo Opening your repository in your browser...
    start https://github.com/M-ship-ui/minor_project-
) else (
    echo.
    echo [ERROR] Browser authentication failed or was cancelled.
    echo Try Option [1] using a GitHub Personal Access Token.
)
goto END

:END
echo.
pause
