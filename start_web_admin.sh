#!/bin/bash
echo "🚀 Запуск веб-интерфейса администратора..."
echo "📦 Установка зависимостей..."
python3 -m pip install flask
echo ""
echo "▶️  Запуск сервера..."
python3 web_admin.py &
sleep 3
echo ""
echo "🌐 Открываю браузер..."
open http://localhost:5001