from llm import *
from util.request import get_yesterday_arxiv_papers
from util.construct_email import *
from tqdm import tqdm
import json
import os
from datetime import datetime
import time
import random
import smtplib
from email.header import Header
from email.utils import parseaddr, formataddr
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class ArxivDaily:
    def __init__(
        self,
        categories: list[str],
        max_entries: int,
        max_paper_num: int,
        provider: str,
        model: str,
        base_url: None,
        api_key: None,
        description: str,
        num_workers: int,
        temperature: float,
        save_dir: None,
        language: str = "zh",
    ):
        self.model_name = model
        self.base_url = base_url
        self.api_key = api_key
        self.max_paper_num = max_paper_num
        self.save_dir = save_dir
        self.num_workers = num_workers
        self.temperature = temperature
        self.language = language
        self.papers = {}
        for category in categories:
            self.papers[category] = get_yesterday_arxiv_papers(category, max_entries)
            print(
                "{} papers on arXiv for {} are fetched.".format(
                    len(self.papers[category]), category
                )
            )
            # avoid being blocked
            sleep_time = random.randint(5, 15)
            time.sleep(sleep_time)

        provider = provider.lower()
        if provider == "ollama":
            self.model = Ollama(model)
        elif provider == "openai" or provider == "siliconflow":
            self.model = GPT(model, base_url, api_key)
        else:
            assert False, "Model not supported."
        print(
            "Model initialized successfully. Using {} provided by {}.".format(
                model, provider
            )
        )

        self.description = description
        self.lock = threading.Lock()  # 添加线程锁

    def get_language_instruction(self):
        """根据语言返回相应的指令"""
        language_instructions = {
            "zh": "使用中文回答。",
            "en": "Please answer in English.",
            "ja": "日本語で回答してください。",
            "ko": "한국어로 답변해 주세요.",
            "fr": "Veuillez répondre en français.",
            "de": "Bitte antworten Sie auf Deutsch.",
            "es": "Por favor, responda en español.",
            "ru": "Пожалуйста, ответьте на русском языке."
        }
        return language_instructions.get(self.language, "使用中文回答。")

    def get_response(self, title, abstract):
        language_instruction = self.get_language_instruction()
        prompt = f"""
            你是一个有帮助的 AI 研究助手，可以帮助我构建每日论文推荐系统。
            以下是我最近研究领域的描述：
            {self.description}
        """
        prompt += f"""
            以下是我从昨天的 arXiv 爬取的论文，我为你提供了标题和摘要：
            标题: {title}
            摘要: {abstract}
        """
        prompt += f"""
            1. 总结这篇论文的主要内容。
            2. 请评估这篇论文与我研究领域的相关性，并给出 0-10 的评分。其中 0 表示完全不相关，10 表示高度相关。
            
            请按以下 JSON 格式给出你的回答：
            {{
                "summary": <你的总结>,
                "relevance": <你的评分>
            }}
            {language_instruction}
            直接返回上述 JSON 格式，无需任何额外解释。
        """

        response = self.model.inference(prompt, temperature=self.temperature)
        return response

    def process_paper(self, paper, max_retries=5):
        retry_count = 0

        while retry_count < max_retries:
            try:
                title = paper["title"]
                abstract = paper["abstract"]
                response = self.get_response(title, abstract)
                response = response.strip("```").strip("json")
                response = json.loads(response)
                relevance_score = float(response["relevance"])
                summary = response["summary"]
                with self.lock:
                    return {
                        "title": title,
                        "arXiv_id": paper["arXiv_id"],
                        "abstract": abstract,
                        "summary": summary,
                        "relevance_score": relevance_score,
                        "pdf_url": paper["pdf_url"],
                    }
            except json.JSONDecodeError as e:
                retry_count += 1
                print(f"JSON解析错误 {paper['arXiv_id']}: {e}")
                print(f"原始响应: {response}")
                if retry_count == max_retries:
                    print(f"已达到最大重试次数 {max_retries}，放弃处理该论文")
                    return None
                time.sleep(2)  # 增加重试间隔
            except Exception as e:
                retry_count += 1
                print(f"处理论文 {paper['arXiv_id']} 时发生错误: {e}")
                print(f"正在进行第 {retry_count} 次重试...")
                if retry_count == max_retries:
                    print(f"已达到最大重试次数 {max_retries}，放弃处理该论文")
                    return None
                time.sleep(2)  # 增加重试间隔

    def get_recommendation(self):
        recommendations = {}
        for category, papers in self.papers.items():
            for paper in papers:
                recommendations[paper["arXiv_id"]] = paper

        print(
            f"Got {len(recommendations)} non-overlapping papers from yesterday's arXiv."
        )

        recommendations_ = []
        print("Performing LLM inference...")

        with ThreadPoolExecutor(self.num_workers) as executor:
            futures = []
            for arXiv_id, paper in recommendations.items():
                futures.append(executor.submit(self.process_paper, paper))
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Processing papers",
                unit="paper",
            ):
                result = future.result()
                if result:
                    recommendations_.append(result)

        recommendations_ = sorted(
            recommendations_, key=lambda x: x["relevance_score"], reverse=True
        )[: self.max_paper_num]

        # Save recommendation to markdown file
        current_time = datetime.now()
        save_path = os.path.join(
            self.save_dir, f"{current_time.strftime('%Y-%m-%d')}.md"
        )
        with open(save_path, "w") as f:
            f.write("# Daily arXiv Papers\n")
            f.write(f"## Date: {current_time.strftime('%Y-%m-%d')}\n")
            f.write(f"## Description: {self.description}\n")
            f.write("## Papers:\n")
            for i, paper in enumerate(recommendations_):
                f.write(f"### {i + 1}. {paper['title']}\n")
                f.write(f"#### Abstract:\n")
                f.write(f"{paper['abstract']}\n")
                f.write(f"#### Summary:\n")
                f.write(f"{paper['summary']}\n")
                f.write(f"#### Relevance Score: {paper['relevance_score']}\n")
                f.write(f"#### PDF URL: {paper['pdf_url']}\n")
                f.write("\n")

        return recommendations_

    def summarize(self, recommendations):
        overview = ""
        for i in range(len(recommendations)):
            overview += f"{i + 1}. {recommendations[i]['title']} - {recommendations[i]['summary']} \n"
        
        language_instruction = self.get_language_instruction()
        language_prompts = {
            "zh": """
            请按以下要求总结今天的论文:

            1. 总体概述
            - 简要总结今天论文的主要研究领域和热点方向
            - 分析研究趋势和关注重点

            2. 分主题详细分析
            - 将论文按研究主题分类
            - 每个主题下的论文按相关性从高到低排序
            - 对每篇论文按以下格式分析:
                1. 论文标题 (高度相关/相关/一般相关)

                摘要: 非常简要地总结论文的主要内容和创新点。

                相关性分析: 分析该论文与研究领域的关联度,以及对研究的价值。

            3. 总体趋势分析
            - 总结当前研究热点和发展趋势
            - 分析未来可能的研究方向

            请以HTML格式返回,使用中文,包含以下结构:
            <h2>总体概述</h2>
            <p>整体概述内容</p>

            <h2>主题：主题分类的名称</h2>
            <ol>
                <li>论文标题 (相关性)</li>
                <p>摘要: 论文内容总结</p>
                <p>相关性分析: 分析论文价值</p>
                ...
            </ol>

            <h2>总体趋势</h2>
            <ol>
                <li>趋势分析</li>
            </ol>

            <h2>未来研究方向</h2>
            <ol>
                <li>未来研究方向1</li>
                <li>未来研究方向2</li>
                ...
            </ol>

            直接返回HTML内容,无需其他说明。
            """,
            "en": """
            Please summarize today's papers according to the following requirements:

            1. Overall Overview
            - Briefly summarize the main research areas and hot topics of today's papers
            - Analyze research trends and focus areas

            2. Detailed Analysis by Topic
            - Categorize papers by research topic
            - Sort papers within each topic by relevance from high to low
            - Analyze each paper in the following format:
                1. Paper Title (Highly Relevant/Relevant/Generally Relevant)

                Abstract: Very briefly summarize the main content and innovations of the paper.

                Relevance Analysis: Analyze the relevance of this paper to the research field and its value to research.

            3. Overall Trend Analysis
            - Summarize current research hotspots and development trends
            - Analyze possible future research directions

            Please return in HTML format, in English, with the following structure:
            <h2>Overall Overview</h2>
            <p>Overall overview content</p>

            <h2>Topic: Topic Classification Name</h2>
            <ol>
                <li>Paper Title (Relevance)</li>
                <p>Abstract: Paper content summary</p>
                <p>Relevance Analysis: Analyze paper value</p>
                ...
            </ol>

            <h2>Overall Trends</h2>
            <ol>
                <li>Trend analysis</li>
            </ol>

            <h2>Future Research Directions</h2>
            <ol>
                <li>Future research direction 1</li>
                <li>Future research direction 2</li>
                ...
            </ol>

            Return HTML content directly, no additional explanation needed.
            """,
            "ja": """
            今日の論文を以下の要件に従って要約してください：

            1. 全体的な概要
            - 今日の論文の主要な研究分野とホットトピックを簡潔に要約
            - 研究トレンドと注目分野を分析

            2. トピック別詳細分析
            - 研究トピック別に論文を分類
            - 各トピック内の論文を関連性の高い順に並べ替え
            - 各論文を以下の形式で分析：
                1. 論文タイトル（高関連/関連/一般的関連）

                要約：論文の主要な内容と革新点を非常に簡潔に要約。

                関連性分析：この論文の研究分野との関連性と研究への価値を分析。

            3. 全体的なトレンド分析
            - 現在の研究ホットスポットと発展トレンドを要約
            - 将来の可能な研究方向を分析

            HTML形式で日本語で返してください。以下の構造を含めてください：
            <h2>全体的な概要</h2>
            <p>全体的な概要内容</p>

            <h2>トピック：トピック分類名</h2>
            <ol>
                <li>論文タイトル（関連性）</li>
                <p>要約：論文内容の要約</p>
                <p>関連性分析：論文の価値を分析</p>
                ...
            </ol>

            <h2>全体的なトレンド</h2>
            <ol>
                <li>トレンド分析</li>
            </ol>

            <h2>将来の研究方向</h2>
            <ol>
                <li>将来の研究方向1</li>
                <li>将来の研究方向2</li>
                ...
            </ol>

            HTMLコンテンツを直接返してください。追加の説明は不要です。
            """,
            "ko": """
            다음 논문들을 요약해 주세요:

            1. 전체 개요
            - 주요 연구 분야와 핵심 내용 요약

            2. 논문별 분석
            - 각 논문의 주요 내용과 혁신점
            - 연구 분야와의 관련성 분석

            3. 연구 트렌드
            - 현재 연구 동향과 향후 방향

            HTML 형식으로 한국어로 반환:
            <h2>전체 개요</h2>
            <p>개요 내용</p>

            <h2>논문 분석</h2>
            <ol>
                <li>논문 제목</li>
                <p>요약: 주요 내용</p>
                <p>관련성: 연구 가치</p>
            </ol>

            <h2>연구 트렌드</h2>
            <ol>
                <li>트렌드 분석</li>
            </ol>

            HTML 내용만 반환하세요.
            """
        }
        
        # 获取对应语言的提示词，如果没有则使用中文
        prompt_template = language_prompts.get(self.language, language_prompts["zh"])
        
        prompt = f"""
            你是一个有帮助的 AI 研究助手，可以帮助我构建每日论文推荐系统。
            以下是我最近研究领域的描述：
            {self.description}
        """
        prompt += f"""
            以下是我从昨天的 arXiv 爬取的论文，我为你提供了标题和摘要：
            {overview}
        """
        prompt += prompt_template

        response = (
            self.model.inference(prompt, temperature=self.temperature)
            .strip("```")
            .strip("html")
            .strip()
        )
        print(response)
        response = get_summary_html(response)
        return response

    def render_email(self, recommendations):
        parts = []
        if len(recommendations) == 0:
            return framework.replace("__CONTENT__", get_empty_html())
        for i, p in enumerate(tqdm(recommendations, desc="Rendering Emails")):
            rate = get_stars(p["relevance_score"])
            parts.append(
                get_block_html(
                    str(i + 1) + ". " + p["title"],
                    rate,
                    p["arXiv_id"],
                    p["summary"],
                    p["pdf_url"],
                )
            )
        summary = self.summarize(recommendations)
        # Add the summary to the start of the email
        content = summary
        content += "<br>" + "</br><br>".join(parts) + "</br>"
        return framework.replace("__CONTENT__", content)

    def send_email(
        self,
        sender: str,
        receiver: str,
        password: str,
        smtp_server: str,
        smtp_port: int,
        title: str,
    ):
        recommendations = self.get_recommendation()
        html = self.render_email(recommendations)

        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, "utf-8").encode(), addr))

        msg = MIMEText(html, "html", "utf-8")
        msg["From"] = _format_addr(f"{title} <%s>" % sender)

        # 处理多个接收者
        receivers = [addr.strip() for addr in receiver.split(",")]
        print(receivers)
        msg["To"] = ",".join([_format_addr(f"You <%s>" % addr) for addr in receivers])

        today = datetime.now().strftime("%Y/%m/%d")
        msg["Subject"] = Header(f"{title} {today}", "utf-8").encode()

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        except Exception as e:
            logger.warning(f"Failed to use TLS. {e}")
            logger.warning(f"Try to use SSL.")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)

        server.login(sender, password)
        server.sendmail(sender, receivers, msg.as_string())
        server.quit()


if __name__ == "__main__":
    categories = ["cs.CV"]
    max_entries = 100
    max_paper_num = 50
    provider = "ollama"
    model = "deepseek-r1:7b"
    description = """
        I am working on the research area of computer vision and natural language processing. 
        Specifically, I am interested in the following fieds:
        1. Object detection
        2. AIGC (AI Generated Content)
        3. Multimodal Large Language Models

        I'm not interested in the following fields:
        1. 3D Vision
        2. Robotics
        3. Low-level Vision
    """

    arxiv_daily = ArxivDaily(
        categories, max_entries, max_paper_num, provider, model, None, None, description
    )
    recommendations = arxiv_daily.get_recommendation()
    print(recommendations)
