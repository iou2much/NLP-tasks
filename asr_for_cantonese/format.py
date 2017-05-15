#coding:utf-8
import os,re,string
from zhon.hanzi import punctuation



def mp3toWav():
    from pydub import AudioSegment
    books = ['Old_Testament','New_Testament']
    re_sec_idx=re.compile(r'(\d{2,3})$')
    
    for book in books:
        for _chapt in os.listdir(book):
            chapt = _chapt.split('_')
            chap_name = chapt[1]

            chapt = chapt[0]
            print(chap_name)

            if not os.path.exists('wav/%s/%s'%(book,chapt)):
                os.makedirs('wav/%s/%s'%(book,chapt))
                chap_name_file = open('wav/%s/%s/chapname.txt'%(book,chapt),'w')
                chap_name_file.write(chap_name+"\n") 
                chap_name_file.close() 

            for _sec in os.listdir('%s/%s'%(book,_chapt)):
                sec = _sec.split('.')
                sec = sec[0].split('_')

                chap_indx = sec[0]
                sec_indx = re_sec_idx.findall(sec[2])[0]

                sec = '%s_%s'%(chapt,sec_indx)
                sound = AudioSegment.from_file('%s/%s/%s'%(book,_chapt,_sec),format='mp3')
                #print(sound.channels)
                #print(sound.frame_rate)
                #print(sound.frame_width)
                #print(sound.sample_width)
                #sound = AudioSegment(data=sound.raw_data,frame_rate=16000, channels=1, sample_width=2)
                sound.export('wav/%s/%s/%s.wav'%(book,chapt,sec), format="wav")#,bitrate='64k')

        #        break
        #    break
        #break
    
def formatTxt():    
    match = re.compile(r'(\w{3}) (\d{1,3}):\d{1,3} ?(.*)')
    txt = open('hgb.utf8.txt')
    content = ''
    pre_chap = ''
    pre_sec = ''
    
    books = ['Old_Testament','New_Testament']
    
    files={}
    for book in books:
        for _chapt in os.listdir('wav/%s'%book):
            files['%s_%s'%(book,_chapt)] = {}
            for _sec in os.listdir('wav/%s/%s'%(book,_chapt)):
                chap_name_file = open('wav/%s/%s/chapname.txt'%(book,_chapt))
                chap_name = chap_name_file.read()
                chap_name_file.close() 
                files['%s_%s'%(book,_chapt)][_sec.split('.')[0]] = chap_name.strip()
    
    i = 1
    isNew = False
    book_name = 'Old_Testament'


    for _line in txt.readlines():
        line = match.findall(_line)[0]

        chap = line[0]
        sec  = line[1]
        text = line[2]
    
        text = re.sub(u"[%s%s]+"%(punctuation,string.punctuation), " ", text )

        num_len = 2

        if pre_chap == '':
            pre_chap = chap
            pre_sec = sec
            chap_name = '%02d'%(i)
            sec_name = '%s_%02d'%(chap_name,int(sec))
    
        if pre_chap == chap and pre_sec == sec:
            content+=text
        else:

            chap_name = '%02d'%(i)

            if len(files['%s_%s'%(book_name,chap_name)])>99:
                num_len=3

            if '%s_%s'%(book_name,chap_name) in files:
                sec_name = '%s_%02d'%(chap_name,int(sec))
                if sec_name in files['%s_%s'%(book_name,chap_name)]:
                    print(files['%s_%s'%(book_name,chap_name)][sec_name])
                else:
                    sec_name = '%s_%03d'%(chap_name,int(sec))
                    print(files['%s_%s'%(book_name,chap_name)][sec_name])
    
            print('isNew:%s,%s,%s'%(isNew,i,sec))

            if not isNew:
                path = 'wav/%s/%s/%s-%s.trans.txt'%('Old_Testament',chap_name,book_name,chap_name)
                if i== 1 and pre_sec=='1':
                    book_name_char = '旧约全书 '
                else:
                    book_name_char = ''
            else:
                path = 'wav/%s/%s/%s-%s.trans.txt'%('New_Testament',chap_name,book_name,chap_name)
                if i== 1 and pre_sec=='1':
                    book_name_char = '新约全书 '
                else:
                    book_name_char = ''

            script = open(path,'a')
            #content = '%s%s第%d章.%s\n'%(i,int(pre_sec),book_name_char ,files['%s_%s'%(book_name,chap_name)][sec_name],int(pre_sec),content)

            if num_len==2:
                script.write('%02d_%02d %s%s第%d章 %s\n'%(i,int(pre_sec),book_name_char ,files['%s_%s'%(book_name,chap_name)][sec_name],int(pre_sec),content))
            else:
                script.write('%02d_%03d %s%s第%d章 %s\n'%(i,int(pre_sec),book_name_char ,files['%s_%s'%(book_name,chap_name)][sec_name],int(pre_sec),content))
            #script.write('%02d_%02d %s\n'%(i,int(pre_sec),content))

            if pre_chap != chap:
                i+=1
                if i==40 and pre_chap=='Mal':
                    i=1
                    isNew = True
                    book_name = 'New_Testament'

            pre_chap = chap
            pre_sec = sec

            content=text

    path = 'wav/%s/%s/%s-%s.trans.txt'%('New_Testament',chap_name,book_name,chap_name)
    script = open(path,'a')
    script.write('%02d_%02d %s%s第%d章 %s\n'%(i,int(pre_sec),book_name_char ,files['%s_%s'%(book_name,chap_name)][sec_name],int(pre_sec),content))


def char_map():
    punct = set(u'''， %/:!),.:;?]}¢'"、。〉》」』】〕〗〞︰︱︳﹐､﹒
            ﹔﹕﹖﹗﹚﹜﹞！），．：；？｜｝︴︶︸︺︼︾﹀﹂﹄﹏､～￠
            々‖•·ˇˉ―--′’”([{£¥'"‵〈《「『【〔〖（［｛￡￥〝︵︷︹︻
            ︽︿﹁﹃﹙﹛﹝（｛“‘-—_…''')
    alpha = set([ chr(i) for i in range(65,123) ])

    bb = open('hgb.utf8.txt')
    s = set(bb.read())
    bb.close()
    s = s-punct
    s = s - alpha
    s = list(s)
    char_map_file = open('char_map.txt','w')
    for i,_s in enumerate(s):
        char_map_file.write('%s %s\n'%(_s,to26(i+1)))
    char_map_file.write('<SPACE> %s'%(to26(i+2)))
    char_map_file.close()

#def split_train_test():
#    range(1,40)
#    range(1,28)
#    os.rename('wav/Old_Testment')
#    os.rename('wav/New_Testment')
#mp3toWav()
#formatTxt()
#split_train_test()
def get(p):
    return 26**p

def count_(s):
    map={}
    for i in range(97,123):
        map[chr(i)] = i-96
    p=len(s)-1
    count=0
    for x in range(len(s)):
        count+=get(x)*map[s[p-x]]
    return count

def to26(num):
    mul,remain = num//26,num%26

    result = chr(remain+96) if remain!=0 else 'z'
    if mul>0 and remain==0:
        mul -= 1

    while mul > 26:
        mul,remain = mul//26,mul%26
        result = chr(remain+96) + result if remain!=0 else 'z' + result
        if mul>0 and remain==0:
            mul -= 1

    if mul>0:
        result = chr(mul+96) + result
    return result

#char_map()
def get_char_map():
    map={}
    char_map_str = open('char_map.txt').read()
    for line in char_map_str.strip().split('\n'):
        ch, index = line.split()
        map[ch] = index
    return map


def encode_str(map,txt):
    list_txt = []
    for c in txt:
        if c in map:
            list_txt.append(map[c])
    return ' '.join(list_txt)

def decode_str(txt):
    map=get_char_map()
    map = dict((map[k],k) for k in map)

    chars = txt.split(' ')
    res = []
    for c in chars:
        res.append(map.get(c,""))
    return ''.join(res)

def encode_bibles():
    map=get_char_map()
    bible = open('hgb.utf8.txt')
    words = ''
    for line in bible.readlines():
        try:
            txt = line.split(' ')[2]
        except:
            pass
        words += encode_str(map,txt)

    open('bible-words.txt','w').write(words)
#encode_bibles()

def __encode_corpus():
    map=get_char_map()
    corpus = open('01/trans.csv.bak')
    result = open('01/trans.csv','w')
    for line in corpus.readlines():
        f,s,c = line.split(',')
        c = encode_str(map,c)
        result.write('%s,%s,%s\n'%(f,s,c))

def encode_corpus_():
    map=get_char_map()
    out_corpus = open('trans.train.csv','w')
    out_corpus.write('wav_filename,wav_filesize,transcript\n')

    corpus = open('wav/Old_Testament/01/Old_Testament-01.trans.txt')
    corpus = open('wav/Old_Testament/01/Old_Testament-01.trans.txt')
    base_path = '/Users/chibs/playground/bigdata-stack/themes/speech-reg/DeepSpeech/test/wav/Old_Testament/01'
    for line in corpus.readlines():
        ss = line.split(' ')
        wav = ss[0]+'.wav'
        wav = '%s/%s'%(base_path,wav)
        size = os.path.getsize(wav)

        c = encode_str(map,''.join(ss[1:]))
        out_corpus.write('%s,%s,%s\n'%(wav,size,c))

def encode_corpus():
    map=get_char_map()
    out_corpus = open('trans.full.csv','w')
    out_corpus.write('wav_filename,wav_filesize,transcript\n')

    corpus = open('trans.char.csv')
    # base_path = '/Users/chibs/playground/bigdata-stack/themes/speech-reg/DeepSpeech/test/wav/Old_Testament/01'
    for line in corpus.readlines()[1:]:
        ss = line.split(',')

        c = encode_str(map,''.join(ss[2]))
        out_corpus.write('%s,%s,%s\n'%(ss[0],ss[1],c))
if __name__ == '__main__':
    encode_corpus()
