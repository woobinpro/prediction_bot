Installation env: linux server, ubuntu
How to use this bot:
1. Import your wallet address/private key to config.json file
2. Set bet amount in config.json file
  - default_bet_amount: This value is the initial bet amount. The bot determines the bet amount based on this value.
  - low_bet_amount: This value is the amount to bet when the probability of winning is not very high.
  - medium_bet_amount: This value is the amount to bet when the probability of winning is medium.
  - high_bet_amount: This value is the amount to bet when the probability of winning is high.
Installation:
  -  sudo apt install python3-pip  or sudo apt-get install python3.6
  -  pip3 install -r requirement.txt
  -  python3 pro.py 