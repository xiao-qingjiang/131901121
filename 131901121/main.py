# -*- coding:utf-8 -*-

import pypinyin
import zhconv
import sys

from pychai import Schema

n = 4
res_queue = []
origin_word = {}  # 用来存测试文件的
hash_keyword = {}
result = []
str_han_zi_word = []


def output_doc(filename):
    with open(filename, 'a', encoding='utf-8') as file_object:
        file_object.write("Total: " + str(len(result)) + '\n')
        for i in result:
            file_object.write(i)


class DFAFilter:

    def __init__(self):
        self.keyword_chains = {}
        self.delimit = '\x00'

    def add_keyword(self, chars, level):
        last_level = {}
        last_char = ""
        for i in range(len(chars)):
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]

                last_level[last_char] = {self.delimit: 0}
                break

    def add(self, keyword):  # 将作为参数的敏感词传入敏感词库keyword_chains

        self.add_keyword(keyword, origin_word)  # 将最原始的敏感词加入到origin_word，方便后续输出
        """需要根据是否是中文，中文的话就要考虑拼音、汉字与部首的组合，把各种组合都存进敏感词库，英文字母全部转化为小写存入敏感词库"""

        if '\u4e00' <= keyword[0] <= '\u9fff':  # 如果敏感词是汉字
            str_han_zi_word.append(keyword)
            len_keyword = len(keyword)
            res_queue.clear()  # 每个新的敏感词操作都要清空res_queue，否则后面的会一直添加到前面敏感词的后面
            type_nums(0, [], len_keyword)  # 通过这个操作可以更新全局变量res_queue，这个通过数字存储了敏感词所有表现形式的所有组合
            for i in range(len(res_queue)):  # 遍历所有可能的组合，并加入敏感词库
                keyword_copy = ""
                for j in range(len(res_queue[i])):
                    if res_queue[i][j] == 0:  # 说明这个位置将用拼音表示
                        keyword_copy += pypinyin.lazy_pinyin(keyword[j])[0]
                    elif res_queue[i][j] == 1:  # 说明这个位置将用简体字表示
                        keyword_copy += zhconv.convert(keyword[j], 'zh-hans')
                    elif res_queue[i][j] == 2:  # 说明这个位置将用繁体字形式表示
                        keyword_copy += zhconv.convert(keyword[j], 'zh-tw')
                    else:                       # 说明这个位置将用首字母表示
                        keyword_copy += pypinyin.lazy_pinyin(keyword[j])[0][0]
                self.add_keyword(keyword_copy, self.keyword_chains)  # 将每一种敏感词的组合表现形式都加入到敏感词库中
                hash_keyword[keyword_copy] = keyword
        else:
            keyword = keyword.lower()
            level = self.keyword_chains
            chars = keyword
            hash_keyword[chars] = chars
            self.add_keyword(chars, level)

    def parse(self, path):  # 解析路径，读入文件，并去除每个词前后的空格,最终根据
        with open(path, encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())  # 将敏感词库中的敏感词逐个添加到self.keyword_chains里

    def filter(self, message):  # 过滤出敏感词，同时按要求输出
        start = 0
        for lines in range(len(message)):
            message[lines] = message[lines].lower()
            level = self.keyword_chains
            record = ""
            flag = 0
            i = -1
            while i < len(message[lines]) - 1:
                i += 1
                char = message[lines][i]
                if char.isalpha():  # 如果是字母，则转为小写
                    char = char.lower()
                    if (char in level) and (flag == 0):
                        start = i
                        record = ""
                        while start < len(message[lines]):
                            char = message[lines][start]
                            if not char.isalpha() and not ('\u4e00' <= char <= '\u9fff'):
                                start += 1
                                continue
                            else:
                                if char not in level:
                                    i = start - 1
                                    flag = 1
                                    break
                                record += char
                                if self.delimit not in level[char]:
                                    level = level[char]

                                elif self.delimit in level[char]:
                                    if record in hash_keyword:
                                        result.append(
                                            "Line" + str(lines + 1) + ": <" + hash_keyword[record] + "> " +
                                            message[lines][i:start + 1] + "\n")
                                    level = self.keyword_chains
                                    break
                            start += 1
                        continue
                    if '\u4e00' <= char <= '\u9fff':  # 如果是汉字，则转为简体
                        char = zhconv.convert(char, 'hans')
                        pinyin = pypinyin.lazy_pinyin(char)[0]
                        if pinyin[0] in level:
                            flag = 1
                            for j in range(len(pinyin)):
                                tmp_char = pinyin[j]
                                if tmp_char not in level:
                                    flag = 0
                                    level = self.keyword_chains
                                    break
                                if self.delimit not in level:
                                    level = level[tmp_char]
                            else:
                                record += char
                                if self.delimit in level:
                                    level = self.keyword_chains
                                    temp_str = ""
                                    for temp in record:
                                        if '\u4e00' <= temp <= '\u9fff':
                                            temp_str += temp
                                    if ''.join(pypinyin.lazy_pinyin(temp_str)) in hash_keyword:
                                        result.append(
                                            "Line" + str(lines + 1) + ": <" + hash_keyword[
                                                ''.join(pypinyin.lazy_pinyin(temp_str))] + "> " + record + "\n")
                                    record = ""
                        else:
                            level = self.keyword_chains
                            flag = 0
                            record = ""
                            continue
                elif len(record) > 0:
                    record += char


def read_file(file_path):  # 读出文件内容，以字符串的形式存在data
    with open(file_path, 'r', encoding='utf-8') as file:
        original_word = file.readlines()
    return original_word


def chai_zi(keywords, dfa_instance):
    wubi98 = Schema('wubi98')
    wubi98.run()
    for word in keywords:
        res = ""
        for i in word:
            if not ('\u4e00' <= i <= '\u9fff'):
                continue
            if not (i in wubi98.tree):
                continue
            tree = wubi98.tree[i]
            first = tree.first
            second = tree.second
            while first.structure == 'h':
                if first.first is None:
                    break
                first = first.first
            while second.structure == 'h':
                if second.second is None:
                    break
                second = second.second
            res_word = ""
            res_word += first.name[0]
            res_word += second.name
            res += res_word
        dfa_instance.add_keyword(res, dfa_instance.keyword_chains)
        hash_keyword[res] = word


# ------------------------------------用dfs求解敏感词表示形式可能的所有组合------------------------------------
def type_nums(depth, queue, lens):  # 三个参数分别为当前搜索深度，传入队列以及敏感词长度
    # dfs求解可能的种类
    queue_copy = queue.copy()
    if depth == lens:
        res_queue.append(queue_copy)
        return

    depth = depth + 1
    for i in range(n):
        queue_copy.append(i)
        type_nums(depth, queue_copy, lens)
        queue_copy.pop()
    return


if __name__ == "__main__":
    if len(sys.argv) > 1:
        words_txt = sys.argv[1]
        org_txt = sys.argv[2]
        ans_txt = sys.argv[3]
    else:
        words_txt = "words.txt"
        org_txt = "org.txt"
        ans_txt = "ans.txt"
    gfw = DFAFilter()

    # -------------------------------读入测试文件-------------------------------

    org = read_file(org_txt)  # 读入测试文件
    # -------------------------------添加敏感词到一个字典中-------------------------------
    gfw.parse(words_txt)  # 解析敏感词文件，将敏感词文件里的敏感词读出并存到gfw.keyword_chains
    chai_zi(str_han_zi_word, gfw)

    # -------------------------------测试敏感词的核心算法-------------------------------
    gfw.filter(org)
    output_doc(ans_txt)
    # -------------------------------将检测结果写入指定文件-------------------------------
