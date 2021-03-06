import math
import re
import numpy as np

def find_lcsubstr(s1, s2):
    '''
    最长公共子串（Longest Common Substring）
    :param s1:
    :param s2:
    :return: substr, ind in str1
    '''
    m = [[0 for i in range(len(s2) + 1)] for j in range(len(s1) + 1)]  # 生成0矩阵，为方便后续计算，比字符串长度多了一列
    mmax = 0  # 最长匹配的长度
    p = 0  # 最长匹配对应在s1中的最后一位
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i] == s2[j]:
                m[i + 1][j + 1] = m[i][j] + 1
                if m[i + 1][j + 1] > mmax:
                    mmax = m[i + 1][j + 1]
                    p = i + 1
    lcsubstr = s1[p - mmax:p].strip()
    ind_start = p - mmax
    ind_end = p
    return lcsubstr, ind_start, ind_end


def find_lcseque(s1, s2):
    '''
    最长公共子序列（Longest Common Subsequence）
    :param s1:
    :param s2:
    :return:
    '''
    m = [[0 for x in range(len(s2) + 1)] for y in range(len(s1) + 1)]  # 生成字符串长度加1的0矩阵，m用来保存对应位置匹配的结果

    d = [[None for x in range(len(s2) + 1)] for y in range(len(s1) + 1)]  # d用来记录转移方向

    for p1 in range(len(s1)):
        for p2 in range(len(s2)):
            if s1[p1] == s2[p2]:  # 字符匹配成功，则该位置的值为左上方的值加1
                m[p1 + 1][p2 + 1] = m[p1][p2] + 1
                d[p1 + 1][p2 + 1] = 'ok'
            elif m[p1 + 1][p2] > m[p1][p2 + 1]:  # 左值大于上值，则该位置的值为左值，并标记回溯时的方向
                m[p1 + 1][p2 + 1] = m[p1 + 1][p2]
                d[p1 + 1][p2 + 1] = 'left'
            else:  # 上值大于左值，则该位置的值为上值，并标记方向up
                m[p1 + 1][p2 + 1] = m[p1][p2 + 1]
                d[p1 + 1][p2 + 1] = 'up'
    (p1, p2) = (len(s1), len(s2))

    s = []
    while m[p1][p2]:  # 不为None时
        c = d[p1][p2]
        if c == 'ok':  # 匹配成功，插入该字符，并向左上角找下一个
            s.append(s1[p1 - 1])
            p1 -= 1
            p2 -= 1
        if c == 'left':  # 根据标记，向左找下一个
            p2 -= 1
        if c == 'up':  # 根据标记，向上找下一个
            p1 -= 1
    s.reverse()
    return ''.join(s)


def chunks(arr, n):
    '''
    split arr into chunks whose size is n
    :param arr:
    :param n:
    :return:
    '''
    return [arr[i:i + n] for i in range(0, len(arr), n)]


def chunks_avg(arr, m):
    '''
    split the arr into m chunks
    :param arr:
    :param m:
    :return:
    '''
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]


def get_all_styles(str):
    str = str.strip()
    if str == "":
        return [str, ]

    if len(str) < 2:
        return [str.upper(), str.lower()]

    word_list = str.split(" ")
    wl0 = [word for word in word_list]
    wl1 = [word.upper() for word in word_list]
    wl2 = [word.lower() for word in word_list]
    wl3 = [word[0].upper() + word.lower()[1:] for word in word_list]
    style_set = set()
    style_set.add(" ".join(wl0))
    style_set.add(" ".join(wl1))
    style_set.add(" ".join(wl2))
    style_set.add(" ".join(wl3))
    return list(style_set)


def tokenize_v1(str):
    token_list = [word for word in re.findall("[A-Za-z0-9\-]+", str) if len(word) > 1 and not re.match("\d+", word)]
    return list(set(token_list))


def edit_distance(word1, word2):
    len1 = len(word1)
    len2 = len(word2)
    dp = np.zeros((len1 + 1, len2 + 1), dtype=int)
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            delta = 0 if word1[i - 1] == word2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + delta, min(dp[i - 1][j] + 1, dp[i][j - 1] + 1))
    return dp[len1][len2]


if __name__ == "__main__":
    import time

    print(tokenize_v1("M-Lab google sfkwe"))
    pass
