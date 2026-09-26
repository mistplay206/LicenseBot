#!/bin/bash

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}=======================================${NC}"
echo -e "${GREEN}   Telegram License Bot Auto Installer   ${NC}"
echo -e "${CYAN}=======================================${NC}"

# گرفتن اطلاعات از ادمین
read -p "1. Enter Bot Token (توکن ربات): " BOT_TOKEN
read -p "2. Enter Admin ID (آیدی عددی ادمین): " ADMIN_ID
read -p "3. Enter Channel ID (آیدی کانال با @): " CHANNEL_ID

echo -e "${YELLOW}\n>>> Updating system and installing dependencies...${NC}"
sudo apt-get update -y -q
sudo apt-get install python3 python3-pip python3-venv git sqlite3 -y -q

echo -e "${YELLOW}>>> Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q

echo -e "${YELLOW}>>> Creating .env file...${NC}"
echo "BOT_TOKEN=$BOT_TOKEN" > .env
echo "ADMIN_ID=$ADMIN_ID" >> .env
echo "CHANNEL_ID=$CHANNEL_ID" >> .env

CURRENT_DIR=$(pwd)

echo -e "${YELLOW}>>> Creating and starting background service...${NC}"
# ساخت سرویس برای روشن ماندن ۲۴ ساعته ربات
cat <<EOF > /etc/systemd/system/licensebot.service
[Unit]
Description=Telegram License Shop Bot
After=network.target

[Service]
User=root
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable licensebot.service
sudo systemctl restart licensebot.service

echo -e "${CYAN}=======================================${NC}"
echo -e "${GREEN}✅ Installation Completed Successfully!${NC}"
echo -e "Bot is now running in the background."
echo -e "Check status with: ${YELLOW}systemctl status licensebot.service${NC}"
echo -e "${CYAN}=======================================${NC}"