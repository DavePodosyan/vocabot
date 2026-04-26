# Vocabot

This Telegram bot sends vocabulary batches, fetches translations and definitions on-the-fly, and tracks learning progress!

## Setup Instructions

### 1. Set Up Your Environment
Open your terminal and navigate to the project directory:
```bash
cd /Users/dav/Development/vocabot
```

If you haven't created a Python virtual environment yet, do so now:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Your Bot
1. Open Telegram and search for **@BotFather**.
2. Send the command `/newbot` and follow the prompts to create your bot and get the **Token**.
3. Open the `.env` file in this directory and paste your token under `TELEGRAM_BOT_TOKEN`.

### 3. Run the Bot

**Option A: Local Polling (Easiest for quick testing)**
In your `.env` file, ensure you have:
```env
MODE=polling
```
Then run the bot:
```bash
python bot.py
```

**Option B: Webhooks (For Ngrok or Server Deployment)**
1. In your `.env` file, set:
```env
MODE=webhook
PORT=8443
WEBHOOK_URL=https://your-ngrok-url.ngrok.io
```
2. Start ngrok in a separate terminal:
```bash
ngrok http 8443
```
3. Copy the `https://...` URL that Ngrok gives you, paste it as `WEBHOOK_URL` in `.env`, and run:
```bash
python bot.py
```

### 4. Interact with the Bot
Go to Telegram and send your bot `/start`.
Then send `/nextbatch` to get 10 words (it will fetch definitions and Russian translations automatically).
Forward the words to Robert. Once he's ready, send `/review 1` to review the batch using the interactive buttons!

---

## 🚀 Ubuntu Server Deployment (Systemd)

Since you are already hosting Laravel apps on your Hetzner Ubuntu server, running this Python bot continuously in the background is extremely easy using `systemd`. 

**Note: You can just use `MODE=polling` on the server!** You do not need Ngrok or Webhooks for this to work perfectly on your server.

### Step 1: Clone and Setup
SSH into your server and put your bot files in `/home/deploy/vocabot` (or your home directory).
```bash
cd /home/deploy/vocabot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
*Don't forget to create your `.env` file there with your Token and Allowed ID!*

### Step 2: Create a Systemd Service
Create a new service file for the bot:
```bash
sudo nano /etc/systemd/system/vocabot.service
```

Paste the following configuration (adjust the paths if you put the folder somewhere else):
```ini
[Unit]
Description=Vocabot Telegram Bot
After=network.target

[Service]
# Change this to your actual server username (e.g., ubuntu, root, or dav)
User=deploy
WorkingDirectory=/home/deploy/vocabot
Environment="PATH=/home/deploy/vocabot/venv/bin"
ExecStart=/home/deploy/vocabot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Step 3: Enable and Start the Bot
Run these commands to tell the server to start the bot, and automatically restart it if the server ever reboots:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vocabot
sudo systemctl start vocabot
```

### Step 4: Check the Status
To see the bot's live logs and make sure it's running smoothly, use:
```bash
sudo systemctl status vocabot
# Or view real-time logs:
sudo journalctl -u vocabot -f
```
