updateInterval = 5000

words = set((
    'shemale',
    'shemales',
    'hentai',
    'titty',
    'busty',
    'milf',
    'milfs',
    'meme',
    'memes'
))

with open('words.txt.formatted', encoding='utf-8') as rf:
    
    line = rf.readline()
    i = 0
    
    while line:
        if i%updateInterval == 0: print(f'line number: {i}')
        i+=1

        word = line.strip()
        if len(word) > 2:
            words.add(word.casefold())
        line = rf.readline()

    print(f'done, {i} lines.')


def my_url_parser(s: str) -> 'str[]':
    
    longestWord = ''
    
    for i in range(len(s)):
        
        if not s[i].isalpha(): continue
        
        for j in range(i+1, len(s)+1):
            potentialWord = s[i:j]
            if potentialWord in words:
                longestWord = potentialWord
                
        if longestWord:
           return [longestWord] + my_url_parser(s[i+len(longestWord):])
        
    return []


if __name__=='__main__':


    for filename in ['notPornUrls.csv', 'pornUrls.csv']:
        
        with open(filename, encoding='utf-8') as rf,\
            open(filename + '.words', 'w', encoding='utf-8') as wf:

            rf.readline() #skip heading
            url = rf.readline()
            i = 0
            print(f'file: {filename}')
            
            while url:
                i+=1
                
                url_words = my_url_parser(url)
                if len(url_words)==0:
                    url = rf.readline()
                    continue

                #print(f'{i}) url:{url}\n\twords: {url_words}\n')

                wf.write(' '.join(url_words)+'\n')
                url = rf.readline()

            print(f'done, {i} lines.\n')

"""
def getLongestWord(s: str) -> 'str, int, int':
    # n^2
    longestWord, start, end = '', 0, 0
    
    for i in range(len(s)):
        for j in range(1, len(s)+1):
            
            potentialWord = s[i:j]
            
            if potentialWord in words and len(potentialWord) > len(longestWord):

                longestWord, start, end = potentialWord, i, j
    
    return longestWord, start, end
    
def my_url_parser(s: str) -> 'str[]':
    '''
    A greedy heuristic that chooses the
    largest word in a string every iteration,
    to get as many words as possible
    '''
    if not s: return []

    word, i, j = getLongestWord(s.casefold())
    
    if not word: return []

    return my_url_parser(s[:i]) + [word] + my_url_parser(s[j:])
"""        


'''
with open('pornUrls.csv', encoding='utf-8') as rf:

    rf.readline() #skip heading
    url = rf.readline()
    i = 0
    
    while url and i<10:
        i+=1
        parser = my_url_parser(url)
        print(f'{i}) url=${url}:\n\tparser: {parser}\n')
        url = rf.readline()

    print(f'done, {i} lines.')
'''
    




