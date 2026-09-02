def build_prefix_table(pattern):
    prefix_table = [0] * len(pattern)
    j = 0  # longitud del prefijo más largo

    for i in range(1, len(pattern)):
        while j > 0 and pattern[i] != pattern[j]:
            j = prefix_table[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
            prefix_table[i] = j
    return prefix_table


def kmp_search(text, pattern):
    prefix_table = build_prefix_table(pattern)
    j = 0  # índice del patrón

    for i in range(len(text)):
        while j > 0 and text[i] != pattern[j]:
            j = prefix_table[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == len(pattern):
            return True  # patrón encontrado
    return False
