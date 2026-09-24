@echo off
cd /d C:\Users\hp\NEWS_TRACKER
call .venv\Scripts\activate.bat
python scripts\run_news_update.py >> logs\live_news_update.log 2>&1
