@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 开始批量生成 AI 画廊系列...
echo ========================================

echo.
echo [1/4] 🖼️ 正在生成: 大理石雕像 (14张)
call venv\Scripts\activate && python tools\generate.py marble_statue

echo.
echo [2/4] 🖼️ 正在生成: 青铜雕像 (12张)
call venv\Scripts\activate && python tools\generate.py bronze_statue

echo.
echo [3/4] 🖼️ 正在生成: 金身佛像 (4张)
call venv\Scripts\activate && python tools\generate.py golden_buddha

echo.
echo [4/4] 🖼️ 正在生成: 翡翠神兽 (4张)
call venv\Scripts\activate && python tools\generate.py jade_deer

echo.
echo ========================================
echo ✅ 画廊系列全部生成完毕！
echo ========================================
pause