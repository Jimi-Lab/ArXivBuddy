from flask import Flask, request, jsonify, render_template
import subprocess
import os

app = Flask(__name__)

# 默认参数
DEFAULT_MODEL = {
    'provider': 'OpenAI',
    'model': 'deepseek-chat',
    'base_url': 'https://api.deepseek.com/v1',
    'api_key': 'sk-f1be1129eb4147d68728855b1dad9e46',
}
DEFAULT_SENDER = '2026193271@qq.com'
DEFAULT_SENDER_PASSWORD = 'wcudxlkavibhdgee'
DEFAULT_SMTP_SERVER = 'smtp.qq.com'
DEFAULT_SMTP_PORT = 465

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/', methods=['GET'])
def index():
    return render_template('web.html')

@app.route('/run_arxiv_daily', methods=['POST'])
def run_arxiv_daily():
    data = request.json
    receiver = data.get('receiver')
    categories = data.get('categories')
    description = data.get('description')
    language = data.get('language', 'zh')  # 默认中文
    model = data.get('model', {})
    zotero_id = data.get('zotero_id')
    zotero_key = data.get('zotero_key')

    # 校验必填项
    if not receiver or not categories or not description:
        return jsonify({'success': False, 'msg': '请填写所有必填项'}), 400

    # 写入 description.txt
    desc_path = os.path.join(WORKSPACE, 'description.txt')
    
    # 读取现有的 description.txt 内容
    try:
        with open(desc_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except FileNotFoundError:
        # 如果文件不存在，创建默认结构
        existing_content = "用户自定义提示词：\n\n\n\n\nZotero文献库分析：\n\n"
    
    # 查找"用户自定义提示词："的位置
    prompt_marker = "用户自定义提示词："
    if prompt_marker in existing_content:
        # 找到标记位置，替换后面的内容
        marker_pos = existing_content.find(prompt_marker)
        marker_end = marker_pos + len(prompt_marker)
        
        # 查找下一个主要标题的位置（如"Zotero文献库分析："）
        next_section_pos = existing_content.find("Zotero文献库分析：", marker_end)
        
        if next_section_pos != -1:
            # 保留"用户自定义提示词："和后面的Zotero分析部分
            new_content = existing_content[:marker_end] + "\n\n" + description + "\n\n" + existing_content[next_section_pos:]
        else:
            # 没有找到下一个标题，直接替换标记后的内容
            new_content = existing_content[:marker_end] + "\n\n" + description + "\n\n"
    else:
        # 没有找到标记，在文件开头添加
        new_content = f"{prompt_marker}\n\n{description}\n\n\nZotero文献库分析：\n\n"
    
    # 写入更新后的内容
    with open(desc_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # 组装模型参数
    provider = model.get('provider') or DEFAULT_MODEL['provider']
    model_name = model.get('model') or DEFAULT_MODEL['model']
    base_url = model.get('base_url') or DEFAULT_MODEL['base_url']
    api_key = model.get('api_key') or DEFAULT_MODEL['api_key']

    # 构造命令
    cmd = [
        'python', os.path.join(WORKSPACE, 'main.py'),
        '--categories', *categories,
        '--provider', provider,
        '--model', model_name,
        '--base_url', base_url,
        '--api_key', api_key,
        '--smtp_server', DEFAULT_SMTP_SERVER,
        '--smtp_port', str(DEFAULT_SMTP_PORT),
        '--sender', DEFAULT_SENDER,
        '--receiver', receiver,
        '--sender_password', DEFAULT_SENDER_PASSWORD,
        '--title', 'Daily arXiv',
        '--description', desc_path,
        '--save',
        '--language', language,
        '--max_paper_num', '20',  # 减少最大论文数量
        '--max_entries', '50',    # 减少每个类别的最大条目数
        '--num_workers', '2',     # 减少worker数量
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 增加到600秒
        if result.returncode == 0:
            return jsonify({'success': True, 'msg': '邮件发送成功！'})
        else:
            error_msg = result.stderr or result.stdout or '执行失败'
            print(f"Command failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return jsonify({'success': False, 'msg': error_msg})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'msg': '处理超时，请稍后重试或减少论文数量'})
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # 打印完整堆栈
        return jsonify({'success': False, 'msg': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 