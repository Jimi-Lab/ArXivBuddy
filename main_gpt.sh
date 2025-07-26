cd /
python main.py --categories cs.AI cs.CE cs.CR \
    --provider OpenAI --model deepseek-chat \
    --base_url https://api.deepseek.com/v1 --api_key sk-f1be1129eb4147d68728855b1dad9e46 \
    --smtp_server smtp.qq.com --smtp_port 465 \
    --sender 2026193271@qq.com --receiver jimi_gogogo@163.com \
    --sender_password wcudxlkavibhdgee \
    --num_workers 16 \
    --temperature 0.7 \
    --title "Daily arXiv" \
    --description "description.txt" \
    --save
