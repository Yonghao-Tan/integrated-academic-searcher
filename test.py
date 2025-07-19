import re

def normalize_title(title):
    # 全部转小写
    title = title.lower()
    # 把连字符、冒号等替换为空格
    title = re.sub(r'[-:]', ' ', title)
    # 把多个空格合并
    title = re.sub(r'\s+', ' ', title)
    # 去除首尾空格
    title = title.strip()
    return title

def titles_match(title1, title2, threshold=0.9):
    n1 = normalize_title(title1)
    n2 = normalize_title(title2)
    print(n1, n2)
    n1 = title1
    n2 = title2
    # 直接全等
    if n1 == n2:
        return True
    # Levenshtein相似度
    from rapidfuzz import fuzz
    score = fuzz.ratio(n1, n2) / 100.0
    print(score, threshold)
    return score >= threshold

# 示例
t1 = "Speed up the model"
t2 = "Speed-up the model"
print(titles_match(t1, t2))  # True

t1 = "Deep learning: a survey"
t2 = "Deep learning a survey"
print(titles_match(t1, t2))  # True

t1 = "Deep learning techniques"
t2 = "Deep learning for images"
print(titles_match(t1, t2))  # False