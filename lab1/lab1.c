#include <stdio.h>
#include <wchar.h>
#include <locale.h>
#include <stdlib.h>

#define MAX_STRINGS 700 

typedef struct {
    wchar_t* content;
    int count;
} StringRecord;

int main() {
    setlocale(LC_ALL, "zh_CN.UTF-8");

    // 初始化字典存储
    StringRecord* len1[MAX_STRINGS] = {0};
    StringRecord* len2[MAX_STRINGS] = {0};
    StringRecord* len3[MAX_STRINGS] = {0};
    StringRecord* len4[MAX_STRINGS] = {0};
    wchar_t* disabled_len1[MAX_STRINGS] = {0};
    wchar_t* disabled_len2[MAX_STRINGS] = {0};
    wchar_t* disabled_len3[MAX_STRINGS] = {0};
    wchar_t* disabled_len4[MAX_STRINGS] = {0};
    int count1 = 0, count2 = 0, count3 = 0, count4 = 0;
    int disabled_count1 = 0, disabled_count2 = 0, disabled_count3 = 0, disabled_count4 = 0;

   // 在加载主字典之前先加载禁用词典
FILE* disable_fp = _wfopen(L"C:\\Users\\Tang Yi\\Downloads\\cn_stopwords.txt", L"r,ccs=UTF-8");
if (disable_fp) {
    wchar_t disable_line[1024];
    while (fgetws(disable_line, sizeof(disable_line)/sizeof(wchar_t), disable_fp)) {
        size_t len = wcslen(disable_line);
        if (len > 0 && disable_line[len-1] == L'\n') {
            disable_line[len-1] = L'\0';
            len--;
        }

        if (len == 0 || len > 4) continue;

        wchar_t* word = (wchar_t*)malloc((len+1)*sizeof(wchar_t));
        if (!word) continue;

        wcscpy(word, disable_line);

        switch(len) {
            case 1: disabled_len1[disabled_count1++] = word; break;
            case 2: disabled_len2[disabled_count2++] = word; break;
            case 3: disabled_len3[disabled_count3++] = word; break;
            case 4: disabled_len4[disabled_count4++] = word; break;
        }
    }
    fclose(disable_fp);
} else {
    wprintf(L"警告：禁用词典加载失败\n");
}
    // 加载字典文件
    FILE* fp = _wfopen(L"C:\\Users\\Tang Yi\\Downloads\\corpus.dict.txt", L"r,ccs=UTF-8");
    if (!fp) {
        wprintf(L"字典文件打开失败\n");
        return 1;
    }

    wchar_t line[1024];
    while (fgetws(line, sizeof(line)/sizeof(wchar_t), fp)) {
        size_t len = wcslen(line);
        if (len > 0 && line[len-1] == L'\n') {
            line[len-1] = L'\0';
            len--;
        }

        if (len == 0) continue;

        // 检查是否在禁用词典中
    int is_disabled = 0;
    wchar_t** disable_dict = NULL;
    int disable_count = 0;
    
    switch(len) {
        case 1: disable_dict = disabled_len1; disable_count = disabled_count1; break;
        case 2: disable_dict = disabled_len2; disable_count = disabled_count2; break;
        case 3: disable_dict = disabled_len3; disable_count = disabled_count3; break;
        case 4: disable_dict = disabled_len4; disable_count = disabled_count4; break;
        default: break;
    }
    
    if (disable_dict) {
        for (int i = 0; i < disable_count; i++) {
            if (wcscmp(disable_dict[i], line) == 0) {
                is_disabled = 1;
                break;
            }
        }
    }
    
    if (is_disabled) continue;

    StringRecord* record = (StringRecord*)malloc(sizeof(StringRecord));
    if (!record) {
        wprintf(L"内存分配失败\n");
        break;
    }

    record->content = (wchar_t*)malloc((len+1)*sizeof(wchar_t));
    if (!record->content) {
        free(record);
        break;
    }

    wcscpy(record->content, line);
    record->count = 0;

    switch(len) {
        case 1: len1[count1++] = record; break;
        case 2: len2[count2++] = record; break;
        case 3: len3[count3++] = record; break;
        case 4: len4[count4++] = record; break;
        default:
            free(record->content);
            free(record);
    }
}
fclose(fp);
    // 处理句子文件
    const wchar_t* sentence_path = L"C:\\Users\\Tang Yi\\Downloads\\corpus.sentence.txt";
    fp = _wfopen(sentence_path, L"r,ccs=UTF-8");
    if (!fp) {
        wprintf(L"无法打开句子文件: %ls\n", sentence_path);
        return 1;
    }

    wchar_t sentence[4096]; // 行缓冲区
    while (fgetws(sentence, sizeof(sentence)/sizeof(wchar_t), fp)) {
        // 预处理行内容
        size_t len = wcslen(sentence);
        if (len > 0 && sentence[len-1] == L'\n') {
            sentence[len-1] = L'\0';
            len--;
        }
        size_t new_len = 0;
    for (size_t i = 0; i < len; i++) {
        // 判断中文字符范围（基本汉字+扩展A区）
        if ((sentence[i] >= 0x4E00 && sentence[i] <= 0x9FFF) || 
            (sentence[i] >= 0x3400 && sentence[i] <= 0x4DBF)) {
            sentence[new_len++] = sentence[i];
        }
    }
    sentence[new_len] = L'\0';  // 终止字符串
    len = new_len;

        int index = 0;
        while (index < len) {
            int matched = 0;
            
            // 从4到1尝试匹配
            for (int window = 4; window >= 1; window--) {
                if (index + window > len) continue;

                // 创建临时窗口字符串
                wchar_t window_str[5] = {0};
                wcsncpy(window_str, sentence + index, window);

                // 选择对应字典
                StringRecord** current_dict = NULL;
                int* dict_count = NULL;
                switch(window) {
                    case 4: current_dict = len4; dict_count = &count4; break;
                    case 3: current_dict = len3; dict_count = &count3; break;
                    case 2: current_dict = len2; dict_count = &count2; break;
                    case 1: current_dict = len1; dict_count = &count1; break;
                }

                // 遍历字典匹配
                for (int i = 0; i < *dict_count; i++) {
                    if (wcscmp(current_dict[i]->content, window_str) == 0) {
                        current_dict[i]->count++;
                        index += window;
                        matched = 1;
                        break;
                    }
                }
                if (matched) break;
            }

            // 未匹配则前进1字符
            if (!matched) index++;
        }
    }
    fclose(fp);
        StringRecord* all_words[MAX_STRINGS * 4] = {0};
        int total_words = 0;
        
        // 合并所有词汇（按长度倒序保证同次数时优先显示长词）
        for (int i = 0; i < count4; i++) all_words[total_words++] = len4[i];
        for (int i = 0; i < count3; i++) all_words[total_words++] = len3[i];
        for (int i = 0; i < count2; i++) all_words[total_words++] = len2[i];
        for (int i = 0; i < count1; i++) all_words[total_words++] = len1[i];
        
        // 排序比较函数
        int compare_words(const void* a, const void* b){
            StringRecord* wa = *(StringRecord**)a;
            StringRecord* wb = *(StringRecord**)b;
            
            // 先按次数降序，次数相同按词长降序，都相同按字典序
            if (wb->count != wa->count) 
                return wb->count - wa->count;
            
            int len_diff = wcslen(wb->content) - wcslen(wa->content);
            if (len_diff != 0)
                return len_diff;
                
            return wcscmp(wa->content, wb->content);
        }
        
        // 执行排序
        qsort(all_words, total_words, sizeof(StringRecord*), compare_words);
        
        // 输出前十结果
int total_count = 0;
for (int i = 0; i < total_words; i++) {
    total_count += all_words[i]->count;
}
printf("{\n");
int show_count = total_words > 10 ? 10 : total_words;
for (int i = 0; i < show_count; i++) {
    StringRecord* word = all_words[i];
    float percentage = (word->count * 100.0f) / total_count;
    wprintf(L"     \"%ls\":%.2f%%\n", 
          word->content, 
          percentage);
}
printf("}");
    // 释放字典内存
    for (int i = 0; i < count4; i++) {
        free(len4[i]->content);
        free(len4[i]);
    }
    for (int i = 0; i < count3; i++) {
        free(len3[i]->content);
        free(len3[i]);
    }
    for (int i = 0; i < count2; i++) {
        free(len2[i]->content);
        free(len2[i]);
    }
    for (int i = 0; i < count1; i++) {
        free(len1[i]->content);
        free(len1[i]);
    }
    for (int i = 0; i < disabled_count4; i++) free(disabled_len4[i]);
    for (int i = 0; i < disabled_count3; i++) free(disabled_len3[i]);
    for (int i = 0; i < disabled_count2; i++) free(disabled_len2[i]);
    for (int i = 0; i < disabled_count1; i++) free(disabled_len1[i]);
    return 0;
}