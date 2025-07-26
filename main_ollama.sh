cd /path/to/customized-arxiv-daily
python main.py --categories cs.CV cs.AI cs.CL cs.CR cs.LG \
    --provider Ollama --model deepseek-r1:7b \
    --smtp_server smtp.qq.com --smtp_port 465 \
    --sender * --receiver * \
    --sender_password * \
    --save