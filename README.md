# Almighty_gpt_bot
GPT telegram bot that you can use to solve any problems from learning languages to coding.

[link to GitHub](https://github.com/NikkyBricky/Almighty_gpt_bot)
# Description

This is a bot based on gpt. It can answer any questions (in ethical scope).
Features of the bot are:
1. It understands voice messages
2. It uses grammar checking API to make the text from your message more readable (optional, needs api_key)
3. You can manage the answers configuration of the gpt to make interaction with the bot as convenient as possible 

This bot uses gpt model "yandexgpt" 

# Usage:
If you want to make your bot with the functions like here, I suggest you to:
 1. Clone this repository
 2. Create .env file with BOT_TOKEN, IAM_TOKEN, FOLDER_ID, ADMIN_ID (your telegram_id) and GRAMMAR_API_KEY (optional) variables
 3. Install packages from requirements.txt 
 4. If you want to move bot to the server, you may not use IAM_TOKEN, but func get_creds() from file make_gpt_token.py to get token automatically  
 5. You can also use infra directory from the project to make it work non-stop on your server 

If you just want to see it work:
 1. Go to https://t.me/best_solutions_bot (bot is launched on cloud)
 2. Choose parameters 
 3. Ask Your questions 

Enjoy!
