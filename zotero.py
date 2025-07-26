from pyzotero import zotero
import os
from llm import GPT, Ollama


# Zotero文献库分析主函数
def analyze_zotero_library(library_id, api_key, provider, model, base_url=None, llm_api_key=None, description_path="description.txt"):
    """
    深度分析用户Zotero文献库，自动总结研究方向和兴趣领域，并写入description.txt。
    参数：
        library_id: Zotero用户ID
        api_key: Zotero API密钥
        provider: LLM提供方（如OpenAI、Ollama等）
        model: LLM模型名
        base_url: LLM API base_url（如有）
        llm_api_key: LLM API密钥（如有）
        description_path: description.txt路径
    """
    # 参数验证
    if not library_id or not api_key:
        raise ValueError("library_id和api_key不能为空")
    
    # 确保参数是字符串类型
    library_id = str(library_id).strip()
    api_key = str(api_key).strip()
    
    # 1. 连接Zotero，获取全部文献
    zot = zotero.Zotero(library_id, 'user', api_key)
    # 获取所有文献（会议论文、期刊论文、预印本）
    items = zot.everything(zot.items(itemType='conferencePaper || journalArticle || preprint'))
    # 过滤有摘要的文献
    items = [item for item in items if item['data'].get('abstractNote')]
    # 按导入时间排序（新到旧），取最近导入的100篇论文
    items.sort(key=lambda x: x['data'].get('dateAdded', ''), reverse=True)
    sample_items = items[:100]  # 取时间离现在最近的100篇论文
    paper_infos = []
    for item in sample_items:
        title = item['data'].get('title', '')
        abstract = item['data'].get('abstractNote', '')
        tags = ','.join([t['tag'] for t in item['data'].get('tags', [])])
        year = item['data'].get('date', '')
        paper_infos.append(f"标题: {title}\n年份: {year}\n标签: {tags}\n摘要: {abstract}")
    papers_text = '\n---\n'.join(paper_infos)

    # 3. 构建大模型分析prompt
    prompt = f"""
请根据以下Zotero文献库内容，分析该用户的主要研究方向、感兴趣领域、代表性主题、常用方法等，并用中文总结：\n\n{papers_text}\n\n请用条理清晰的段落进行总结。
"""

    # 4. 调用大模型分析
    if provider.lower() == 'openai' or provider.lower() == 'siliconflow':
        llm = GPT(model, base_url, llm_api_key)
        analysis = llm.inference(prompt, temperature=0.3)
    elif provider.lower() == 'ollama':
        llm = Ollama(model)
        analysis = llm.inference(prompt)
    else:
        raise ValueError(f"暂不支持的provider: {provider}")

    # 5. 写入description.txt
    # 读取原文件内容
    if not os.path.exists(description_path):
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write("用户自定义提示词：\n\n\n\n\nZotero文献库分析：\n\n")
    with open(description_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # 找到“Zotero文献库分析：”行
    new_lines = []
    found = False
    for line in lines:
        new_lines.append(line)
        if line.strip().startswith("Zotero文献库分析："):
            found = True
            # 清空后续内容，插入分析
            new_lines.append(analysis.strip() + '\n')
            break
    if found:
        # 只保留到分析段落
        with open(description_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    else:
        # 没有找到则追加
        with open(description_path, 'a', encoding='utf-8') as f:
            f.write("Zotero文献库分析：\n" + analysis.strip() + '\n')
    print("Zotero文献库分析已写入description.txt！")






# # 主函数调用示例
# def main():
#     # 这里请替换为你的Zotero用户ID和API key，以及大模型参数
#     library_id = "16651687"
#     zotero_api_key = "fytaYsbjBOhzjfQoalDc1UEf"
#     provider = "OpenAI"  # 或 "Ollama"
#     model = "deepseek-chat"  # 例如 deepseek-chat, gpt-3.5-turbo, deepseek-r1:7b
#     base_url = "https://api.deepseek.com/v1"  # OpenAI/SiliconFlow等需提供
#     llm_api_key = "sk-f1be1129eb4147d68728855b1dad9e46"
    
#     # 检查参数是否已设置
#     if library_id == "你的Zotero用户ID" or zotero_api_key == "你的Zotero API key":
#         print("请先设置你的Zotero用户ID和API key！")
#         print("请修改main()函数中的以下参数：")
#         print("- library_id: 你的Zotero用户ID")
#         print("- zotero_api_key: 你的Zotero API key")
#         print("- llm_api_key: 你的大模型API key")
#         return
    
#     try:
#         analyze_zotero_library(library_id, zotero_api_key, provider, model, base_url, llm_api_key)
#     except Exception as e:
#         print(f"运行出错: {e}")
#         print("请检查你的Zotero用户ID、API key和网络连接是否正确。")

# if __name__ == "__main__":
#     main()
