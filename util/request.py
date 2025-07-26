"""
Use requests and BeautifulSoup to get yesterday's arXiv papers.
"""

import requests
from bs4 import BeautifulSoup


def get_yesterday_arxiv_papers(category: str = "cs.CV", max_results: int = 100):
    url = f"https://arxiv.org/list/{category}/new?skip=0&show={max_results}"

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        entries = soup.find_all("dl", id="articles")[0].find_all(["dt", "dd"])
    except Exception as e:
        return []

    papers = []
    for i in range(0, len(entries), 2):
        title_tag = entries[i + 1].find("div", class_="list-title")
        title = (
            title_tag.text.strip().replace("Title:", "").strip()
            if title_tag
            else "No title available"
        )

        abs_url = "https://arxiv.org" + entries[i].find("a", title="Abstract")["href"]

        pdf_url = entries[i].find("a", title="Download PDF")["href"]
        pdf_url = "https://arxiv.org" + pdf_url

        abstract_tag = entries[i + 1].find("p", class_="mathjax")
        abstract = (
            abstract_tag.text.strip() if abstract_tag else "No abstract available"
        )

        comments_tag = entries[i + 1].find("div", class_="list-comments")
        comments = (
            comments_tag.text.strip() if comments_tag else "No comments available"
        )

        paper_info = {
            "title": title,
            "arXiv_id": pdf_url.split("/")[-1],
            "abstract": abstract,
            "comments": comments,
            "pdf_url": pdf_url,
            "abstract_url": abs_url,
        }

        papers.append(paper_info)

    return papers


if __name__ == "__main__":
    papers = get_yesterday_arxiv_papers()
    print(len(papers))
