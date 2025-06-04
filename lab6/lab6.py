import os
import jieba
from collections import defaultdict, Counter
import heapq


def load_stopwords(stopwords_path):
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        stopwords = set(line.strip() for line in f if line.strip())
    return stopwords


def tokenize(text, stopwords):
    words = jieba.cut(text)
    return [word for word in words if word.strip() and word not in stopwords]


# 构建完整倒排索引（保留每个词项的所有文档）
def build_full_index(article_dir, stopwords):
    inverted_index = defaultdict(list)
    doc_id_to_filename = {}

    doc_id = 1
    for filename in os.listdir(article_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(article_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            tokens = tokenize(text, stopwords)
            term_count = Counter(tokens)

            for term, count in term_count.items():
                tf = count / len(tokens)  # 简单归一化
                inverted_index[term].append((doc_id, tf))

            doc_id_to_filename[doc_id] = filename
            doc_id += 1

    full_winner_lists = {}
    for term, docs in inverted_index.items():

        # ✅ 使用堆排序选出 TF 最高的前 r 个文档
        heap = []
        for doc_id, score in docs:
            if len(heap) < r:
                heapq.heappush(heap, (score, doc_id))
            else:
                heapq.heappushpop(heap, (score, doc_id))

        # 堆中保存的是最小的 r 个，我们按降序返回
        sorted_docs = sorted(heap, key=lambda x: -x[0])

        full_winner_lists[term] = sorted_docs

    return full_winner_lists, doc_id_to_filename


# 查询处理函数（支持传入当前 r 值，并返回得分）
def query_top_k_terms_with_r(k, terms, full_winner_lists, r):
    lists = []
    valid_terms = []

    for term in terms:
        if term in full_winner_lists:
            lists.append(full_winner_lists[term][:r])
            valid_terms.append(term)

    if not valid_terms:
        return []

    # 求交集
    doc_sets = [set(doc_id for doc_id, _ in lst) for lst in lists]
    common_docs = set.intersection(*doc_sets)

    if not common_docs:
        return []

    # 计算得分
    combined_scores = defaultdict(float)
    for term_idx, term in enumerate(valid_terms):
        docs = lists[term_idx]
        for doc_id, score in docs:
            if doc_id in common_docs:
                combined_scores[doc_id] += score

    # 过滤掉得分为 0 的文档
    filtered_scores = [(doc_id, score) for doc_id, score in combined_scores.items() if score > 0]

    # 使用最大堆选出 Top-K
    heap = [(-score, doc_id) for doc_id, score in filtered_scores]
    heapq.heapify(heap)

    top_k = []
    for _ in range(min(k, len(heap))):
        neg_score, doc_id = heapq.heappop(heap)
        top_k.append((doc_id, -neg_score))  # (doc_id, score)

    return top_k


# 主程序入口
def main():
    article_dir = r"D:\code\natural_language_processing\lab6\article"
    stopwords_path = r"D:\code\natural_language_processing\lab6\cn_stopwords.txt"

    print("正在加载停用词...")
    stopwords = load_stopwords(stopwords_path)

    try:
        k = int(input("请输入整数 k："))
        if k <= 0:
            raise ValueError
    except ValueError:
        print("输入错误：k 必须为正整数")
        return

    # 获取文档总数
    article_files = [f for f in os.listdir(article_dir) if f.endswith(".txt")]
    N = len(article_files)
    print(f"总共找到 {N} 篇文档")

    try:
        m = int(input("请输入将要输入的词项数量 m："))
        if m <= 0:
            raise ValueError
    except ValueError:
        print("输入错误：m 必须为正整数")
        return

    threshold = int(k * 0.6)
    print(f"要求至少返回 {threshold} 个文档")

    # Step 1: 构建一次完整倒排索引 + 文档 ID 映射
    print("正在构建完整倒排索引...")
    full_winner_lists, doc_id_to_filename = build_full_index(article_dir, stopwords)

    # Step 2: 输入词项
    terms = []
    for i in range(m):
        term = input(f"请输入第 {i+1} 个查询词：").strip()
        if not term:
            print("警告：空词将被跳过")
            continue
        terms.append(term)

    if not terms:
        print("至少需要一个查询词")
        return

    # Step A: 检查每个词项是否存在于倒排索引中
    not_found_terms = [term for term in terms if term not in full_winner_lists]
    if not_found_terms:
        print(f"错误：以下词项在语料库中未出现：{', '.join(not_found_terms)}")
        print("无法进行查询，请重新输入有效词项")
        return

    # Step 3: 分阶段尝试不同 r 值进行查询
    r_candidates = [
        max(1, N // 4),
        max(1, N // 2),
        max(1, (3 * N) // 4),
        N
    ]

    results = []  # 存储 (doc_id, score)

    for r in r_candidates:
        print(f"\n正在尝试查询（r = {r}）...")

        current_results = query_top_k_terms_with_r(k, terms, full_winner_lists, r=r)

        if len(current_results) >= threshold:
            results = current_results
            print(f"满足要求，使用 r = {r}")
            break
        else:
            print(f"结果不足 {threshold} 个，尝试下一个 r 值")

    if not results:
        print(f"所有尝试均未达到要求，输出最大 r = {N} 的结果")
        results = current_results

    if not results:
        print("没有任何文档匹配所有关键词")
    else:
        print("\n匹配文档及得分如下：")
        scored_output = [f"id={doc_id}({int(score * 100)})" for doc_id, score in results]
        print("Top-K 文档：", ", ".join(scored_output))

        matched_files = []
        seen_files = set()
        for doc_id, _ in results:
            filename = doc_id_to_filename.get(doc_id)
            if filename and filename not in seen_files:
                matched_files.append(filename)
                seen_files.add(filename)

        print("\n匹配的文件名如下：")
        for file in matched_files:
            print(file)


if __name__ == '__main__':
    main()