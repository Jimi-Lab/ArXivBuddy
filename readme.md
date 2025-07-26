# ArXivBuddy

## 一、项目简介

**ArXivBuddy** 是一个面向科研工作者和学术爱好者的 AI 驱动学术论文发现与推荐平台。它结合**<u>用户自定义提示词（Prompt）</u>**、**<u>Zotero 文献库</u>**分析和 <u>**arXiv 论文抓取**</u>，能够根据用户的研究兴趣和文献阅读历史，自动推荐<u>**每日**</u>最新的高相关性论文，并通过邮件推送给用户。项目支持多种主流 LLM（如 <u>OpenAI、Ollama 等</u>），可自定义研究兴趣（提示词）和推荐语言（中、英、日、韩等），适合个性化学术信息获取。

## 二、项目部署流程

### 1. 本地环境部署

1. 克隆仓库并进入目录：

```bash
git clone https://github.com/Jimi-Lab/ArXivBuddy
cd ArXivBuddy
```

2. 安装依赖：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. 运行程序

```bash
python /web/app.py
```

该命令将在本地 8080 端口开启服务。

4. 访问本地网站 127.0.0.1:8080/即可打开网页。

![](https://cdn.nlark.com/yuque/0/2025/png/34357387/1753556196396-3c908d89-70e8-4a38-b778-f2870c68e90a.png)



### 2. Docker 部署

1. 构建镜像：


2. 运行容器（默认启动 Web 服务，监听 8080 端口）：





## 三、作品详细描述

### 1. 核心功能

+ **arXiv 论文抓取**：自动获取指定类别的最新论文。
+ **Zotero 文献分析**：集成 Zotero API，分析用户文献库，提取研究兴趣、代表性主题、常用方法等，自动生成个性化推荐权重。
+ **大模型智能推荐**：支持多种 LLM（OpenAI、Ollama），结合用户自定义提示词和文献历史，智能筛选、摘要和排序论文。
+ **邮件推送**：自动生成美观的 HTML 邮件，按用户设定每日推送论文推荐。
+ **Web 端交互**：现代化前端，支持 arXiv 类别多选、Zotero 账号输入、模型参数自定义、语言切换等。
+ **历史记录**：推荐结果可保存至本地，便于追溯和分析。

### 2. 工作流程

1. 用户通过 Web 或命令行输入研究兴趣、arXiv 类别、Zotero 账号等。
2. 系统抓取最新 arXiv 论文，分析用户 Zotero 文献库，融合自定义提示词。
3. 调用 LLM 对论文进行摘要、相关性分析和排序。
4. 生成推荐摘要和详细分析，渲染为 HTML 邮件。
5. 通过 SMTP 自动发送邮件，或在 Web 端展示结果。
6. 推荐历史自动归档至 `arxiv_history/` 目录。

### 3. 推荐算法与个性化

+ 结合用户自定义提示词（如研究兴趣、关注方向）和 Zotero 文献库分析结果，动态分配权重。
+ 支持多模型推理，自动重试和容错。
+ 论文相关性排序融合了 LLM 语义理解和历史兴趣建模。

### 4. Zotero 集成

+ 支持输入 Zotero 用户 ID 和 API Key，自动抓取最近 100 篇有摘要的文献。
+ 通过 LLM 自动总结用户研究方向、兴趣领域、代表性主题和常用方法，写入 description.txt。
+ 支持 Web 端一键配置。

### 5. 邮件与前端

+ 邮件内容采用美观的 HTML 模板，支持多语言。
+ Web 前端基于 Bootstrap，交互友好，支持移动端适配。
+ 支持模型参数自定义、arXiv 类别多选、Zotero 账号输入等。

## 四、技术栈与架构

+ **后端**：Python 3.11，Flask（Web 服务），requests、BeautifulSoup（arXiv 抓取），pyzotero（Zotero API），tqdm、loguru、concurrent.futures（并发与日志）。
+ **大模型集成**：支持 OpenAI格式的API、Ollama本地部署的模型 等。
+ **邮件服务**：smtplib、email（邮件发送与格式化）。
+ **前端**：Bootstrap 5，FontAwesome，现代响应式设计，交互丰富。
+ **容器化**：支持Dockerfile 一键部署。
+ **历史归档**：推荐结果自动保存至 `arxiv_history/`。

---

如需详细使用说明、二次开发或遇到问题，欢迎查阅源码、提 issue 或联系作者。



本项目参考了：
https://github.com/JoeLeelyf/customize-arxiv-daily

https://github.com/TideDra/zotero-arxiv-daily

