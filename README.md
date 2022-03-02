# prediction_bot
  This bot is automatic betting bot for pancakeswap prediction and dogebet.<br>
  By analyzing bnb prices across multiple marketplaces to predict bnb prices, this bot can win almost 70% ~ 80% of bets.
# Installation Env
  linux server, ubuntu
# How to use this bot
1. Import your wallet address/private key to config.json file
2. Set bet amount in config.json file
  - default_bet_amount: This value is the initial bet amount. The bot determines the bet amount based on this value.
  - low_bet_amount: This value is the amount to bet when the probability of winning is not very high.
  - medium_bet_amount: This value is the amount to bet when the probability of winning is medium.
  - high_bet_amount: This value is the amount to bet when the probability of winning is high.
# Installation
  -  sudo apt install python3-pip  or sudo apt-get install python3.6<br>
  -  pip3 install -r requirement.txt<br>
  -  python3 pro.py 
