cd /path/to/customized-arxiv-daily
python main.py --categories cs.CV cs.AI cs.CL cs.CR cs.LG \
    --provider SiliconFlow --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B \
    --base_url https://api.siliconflow.cn/v1 --api_key * \
    --smtp_server smtp.qq.com --smtp_port 465 \
    --sender * --receiver * \
    --sender_password * \
    --save