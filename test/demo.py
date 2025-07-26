import numpy as np
from sentence_transformers import SentenceTransformer
from paper import ArxivPaper
from datetime import datetime




default_id = ''
default_key = ''

def get_zotero_corpus(id:str,key:str) -> list[dict]:
    zot = zotero.Zotero(id, 'user', key)
    collections = zot.everything(zot.collections())
    collections = {c['key']:c for c in collections}
    # 获取所有会议论文、期刊论文、预印本，且摘要不为空
    corpus = zot.everything(zot.items(itemType='conferencePaper || journalArticle || preprint'))
    corpus = [c for c in corpus if c['data']['abstractNote'] != '']
    def get_collection_path(col_key:str) -> str:
        # 递归获取collection的完整路径
        if p := collections[col_key]['data']['parentCollection']:
            return get_collection_path(p) + '/' + collections[col_key]['data']['name']
        else:
            return collections[col_key]['data']['name']
    for c in corpus:
        paths = [get_collection_path(col) for col in c['data']['collections']]
        c['paths'] = paths
    return corpus





def dynamic_alpha(prompt: str) -> float:
    """
    根据 prompt 长度动态计算 alpha 权重
    """
    if not prompt:
        return 0.0
    length = len(prompt.split())
    if length > 25:
        return 0.7
    elif length > 10:
        return 0.5
    else:
        return 0.3

def rerank_paper(
    candidate: list[ArxivPaper],
    corpus: list[dict],
    prompt: str = None,
    model: str = 'avsolatorio/GIST-small-Embedding-v0'
) -> list[ArxivPaper]:
    """
    对候选论文进行重排序，融合用户 prompt 与 Zotero 库兴趣

    参数:
    - candidate: 候选论文列表
    - corpus: 用户 Zotero 库
    - prompt: 用户输入的大模型提示词，可选
    - model: SentenceTransformer 模型名
    """
    encoder = SentenceTransformer(model)

    # 对 Zotero 论文按时间倒序
    corpus = sorted(
        corpus,
        key=lambda x: datetime.strptime(x['data']['dateAdded'], '%Y-%m-%dT%H:%M:%SZ'),
        reverse=True
    )
    
    # 时间衰减权重
    time_decay_weight = 1 / (1 + np.log10(np.arange(len(corpus)) + 1))
    time_decay_weight = time_decay_weight / time_decay_weight.sum()

    # 编码 Zotero 摘要
    corpus_feature = encoder.encode([paper['data']['abstractNote'] for paper in corpus])
    # 编码候选论文
    candidate_feature = encoder.encode([paper.summary for paper in candidate])

    # 相似度（Zotero）
    sim_zotero = encoder.similarity(candidate_feature, corpus_feature)
    score_zotero = (sim_zotero * time_decay_weight).sum(axis=1)

    # 相似度（Prompt）或为零
    if prompt:
        prompt_feature = encoder.encode([prompt])[0]
        score_prompt = candidate_feature @ prompt_feature.T
        alpha = dynamic_alpha(prompt)
    else:
        score_prompt = np.zeros(len(candidate))
        alpha = 0.0

    # 综合打分
    final_scores = alpha * score_prompt + (1 - alpha) * score_zotero

    # 分配得分
    for s, c in zip(final_scores, candidate):
        c.score = s.item()

    # 排序
    candidate = sorted(candidate, key=lambda x: x.score, reverse=True)
    return candidate









