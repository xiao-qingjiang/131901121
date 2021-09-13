# -*- coding:utf-8 -*-

import time

import pypinyin
import zhconv
from xmnlp.checker import unicode

n = 3
res_queue = []
origin_word = {}  # 用来存测试文件的
hash_keyword = {}
result = []


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
                    else:  # 说明这个位置将用繁体字形式表示
                        keyword_copy += zhconv.convert(keyword[j], 'zh-tw')
                self.add_keyword(keyword_copy, self.keyword_chains)  # 将每一种敏感词的组合表现形式都加入到敏感词库中
                hash_keyword[keyword_copy] = keyword
        else:
            keyword = keyword.lower()
            level = self.keyword_chains
            chars = keyword
            hash_keyword[chars] = chars
            self.add_keyword(chars, level)

        # if i == len(chars) - 1:
        #     level[self.delimit] = 0

    def parse(self, path):  # 解析路径，读入文件，并去除每个词前后的空格,最终根据
        with open(path, encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())  # 将敏感词库中的敏感词逐个添加到self.keyword_chains里

    def filter(self, message):  # 过滤出敏感词，同时按要求输出

        for lines in range(len(message)):
            message[lines] = message[lines].lower()
            level = self.keyword_chains

            for i in range(len(message[lines])):
                char = message[lines][i]
                if char.isalpha():  # 如果是字母，则转为小写
                    char = char.lower()
                if '\u4e00' <= char <= '\u9fff':  # 如果是汉字，则转为简体
                    char = zhconv.convert(char, 'hans')
                if char in level:
                    start = i
                    record = ""
                    while start < len(message[lines]):
                        char = message[lines][start]
                        if not char.isalpha() and not ('\u4e00' <= char <= '\u9fff'):
                            start += 1
                            continue
                        else:
                            if char not in level:
                                break
                            record += char
                            if self.delimit not in level[char]:
                                level = level[char]

                            elif self.delimit in level[char]:
                                # print(lines, message[lines][i:start + 1])
                                if record in hash_keyword:
                                    result.append(
                                        "Line" + str(lines) + ": <" + hash_keyword[record] + "> " + message[lines][
                                                                                                    i:start + 1] + "\n")
                                level = self.keyword_chains
                                i = start + 1
                        start += 1
                else:
                    continue


# def test_first_character():
#     gfw = DFAFilter()
#     gfw.add("1989年")
#     assert gfw.filter("1989", "*") == "1989"


def read_file(file_path):  # 读出文件内容，以字符串的形式存在data
    with open(file_path, 'r', encoding='utf-8') as file:
        original_word = file.readlines()
    return original_word


def print_files(file_name):
    pass


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
    t = time.time()
    gfw = DFAFilter()

    # -------------------------------读入测试文件-------------------------------
    path = r"D:\own detailed files\FZU官方资料\软工\第一次个人编程作业\org.txt"
    org = read_file(path)  # 读入测试文件
    # -------------------------------添加敏感词到一个字典中-------------------------------
    gfw.parse(r"D:\own detailed files\FZU官方资料\软工\第一次个人编程作业\words.txt")  # 解析敏感词文件，将敏感词文件里的敏感词读出并存到gfw.keyword_chains

    # -------------------------------测试敏感词的核心算法-------------------------------
    gfw.filter(org)
    output_doc(r"res.txt")
    # -------------------------------将检测结果写入指定文件-------------------------------

    print(time.time() - t)

    # test_first_character()
