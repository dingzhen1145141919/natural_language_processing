import os
import jieba
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

input_dir = r'D:\\code\\natural_language_processing\\lab3\\dataset\\article'
output_file = r'D:\\code\\natural_language_processing\\lab3\\output.txt'

inverted_index = defaultdict(lambda: defaultdict(int))
inverted_index_sets = defaultdict(set)

def build_inverted_index():

    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                words = jieba.lcut(content)
                # 去除标点、数字、单字
                filtered_words = [word for word in words if len(word) > 1 and word.isalpha()]
                # 统计词频
                word_count = defaultdict(int)
                for word in filtered_words:
                    word_count[word] += 1
                # 更新倒排索引
                doc_id = int(filename[:-4])
                for word, count in word_count.items():
                    inverted_index[word][doc_id] = count
                    inverted_index_sets[word].add(doc_id)

def write_inverted_index_to_file():

    with open(output_file, 'w', encoding='utf-8') as file:
        for word, doc_counts in inverted_index.items():
            sorted_doc_counts = sorted(doc_counts.items(), key=lambda x: (-x[1], x[0]))
            file.write(f"{word}: {', '.join(f'({doc_id},{count})' for doc_id, count in sorted_doc_counts)}\n")

@lru_cache(maxsize=1000)
def cached_search_word(word):

    if word in inverted_index:
        doc_counts = inverted_index[word]
        sorted_doc_counts = sorted(doc_counts.items(), key=lambda x: (-x[1], x[0]))
        return sorted_doc_counts
    return None

def search_word(word):
    start_time = time.perf_counter()
    result = cached_search_word(word)
    if result:
        end_time = time.perf_counter()
        print(f"查询“{word}”花费时间: {end_time - start_time:.6f} 秒")
        for doc_id, count in result:
            print(f"文档{doc_id}共出现{count}次")
    else:
        end_time = time.perf_counter()
        print(f"查询“{word}”花费时间: {end_time - start_time:.6f} 秒")
        print("未找到该词")

def process_query(query):

    start_time = time.perf_counter()
    if '&' in query and '|' in query:
        return "输入错误", []

    if '&' in query:
        words = query.split('&')
        operator = '&'
    elif '|' in query:
        words = query.split('|')
        operator = '|'
    else:
        return search_word(query), []

    word_indices = {word: inverted_index_sets[word] for word in words if word in inverted_index_sets}

    if not word_indices:
        end_time = time.perf_counter()
        return f"查询“{query}”花费时间: {end_time - start_time:.6f} 秒", []

    if operator == '&':
        common_doc_ids = set.intersection(*word_indices.values())
        if not common_doc_ids:
            end_time = time.perf_counter()
            return f"查询“{query}”花费时间: {end_time - start_time:.6f} 秒", []
        doc_count = defaultdict(int)
        for doc_id in common_doc_ids:
            total_count = sum(inverted_index[word][doc_id] for word in words if doc_id in inverted_index[word])
            doc_count[doc_id] = total_count

    elif operator == '|':
        all_doc_ids = set.union(*word_indices.values())
        doc_count = defaultdict(int)
        for word in words:
            for doc_id in word_indices[word]:
                doc_count[doc_id] += inverted_index[word][doc_id]

    sorted_doc_counts = sorted(doc_count.items(), key=lambda x: (-x[1], x[0]))
    end_time = time.perf_counter()
    return f"查询“{query}”花费时间: {end_time - start_time:.6f} 秒", sorted_doc_counts

def search_multiple_words(query):
    start_time = time.perf_counter()
    queries = query.split(',')
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_query, queries))
    for result in results:
        print(result[0])
        if result[1]:
            for doc_id, count in result[1]:
                print(f"文档{doc_id}共出现{count}次")
    end_time = time.perf_counter()
    print(f"总查询时间: {end_time - start_time:.6f} 秒")

if __name__ == "__main__":
    try:
        build_inverted_index()
        print("倒排索引构建完成")
        write_inverted_index_to_file()
        print("结果已写入输出文件")
        
        while True:
            user_input = input("请输入要检索的词或字（输入 'exit' 退出）: ").strip()
            if user_input.lower() == 'exit':
                print("退出检索")
                break
            if not user_input:
                print("输入不能为空，请重新输入。")
                continue
            search_multiple_words(user_input)
    except Exception as e:
        print(f"发生错误: {e}")