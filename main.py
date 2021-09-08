# -*- coding:utf-8 -*-
from collections import defaultdict
import re

'''
__all__ = ['DFAFilter']
__author__ = 'wanghaitao93'
__date__ = '2020.02.04'
'''

from xmnlp.checker import unicode

class DFAFilter():

    def __init__(self):
        self.keyword_chains = {}
        self.delimit = '\x00'

    def add(self, keyword):
        if not isinstance(keyword, str):
            keyword = keyword.decode('utf-8')

        keyword = keyword.lower()
        chars = keyword.strip() # 删除前后空格等
        '''在这附近应该加上对字符的处理，比如拼音、英文、特殊符号'''

        '''print()
        print(chars)'''

        if not chars:
            return
        level = self.keyword_chains

        '''print(len(chars))
        print(level)'''

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

        if i == len(chars) - 1:
            level[self.delimit] = 0



    def parse(self, path):                      # 解析路径，读入文件，并去除每个词前后的空格
        with open(path, encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def filter(self, message, repl="*"):
        if not isinstance(message, str):
            message = message.decode('utf-8')
        message = message.lower()
        ret = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        ret.append(repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1
        return ''.join(ret)


def test_first_character():
    gfw = DFAFilter()
    gfw.add("1989年")
    assert gfw.filter("1989", "*") == "1989"


def read_file(path):
    with open(path, encoding="utf-8") as f1:
        data = f1.read()
        return data


if __name__ == "__main__":
    # gfw = NaiveFilter()
    # gfw = BSFilter()

    import time

    t = time.time()

    gfw = DFAFilter()
    gfw.parse(r"D:\own detailed files\FZU官方资料\软工\第一次个人编程作业\keywords.txt")


    path = r"D:\own detailed files\FZU官方资料\软工\第一次个人编程作业\org.txt"

    data=read_file(path)
    #print(data)
    print(gfw.filter(data, "*"))
    print(time.time() - t)

    test_first_character()

