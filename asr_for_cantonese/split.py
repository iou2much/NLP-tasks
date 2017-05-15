import os,math
from pydub import AudioSegment
from pydub.silence import split_on_silence

def split_wav():
    books = {"Old_Testament":39,"New_Testament":27}
    base_path = '/Users/chibs/playground/bigdata-stack/themes/speech-reg/DeepSpeech/test/wav/'
    output = open('trans.char.csv','a')
    # output.write("wav_filename,wav_filesize,transcript\n")
    for book in books:
        chapters = dict(('%02d'%i,[]) for i in range(1,books[book]+1))

        for chap in chapters:
            cur_path = '%s/%s/%s'%(base_path,book,chap)
            words={}


            trans = open('%s/%s-%s.trans.txt'%(cur_path,book,chap))
            for line in trans.readlines():
                sec = line.split(" ")[0].split('_')[1]
                words[sec] = line.strip().split(" ")[1:]


            for _sec in os.listdir(cur_path):
                if _sec in ['01_01.wav','01_02.wav','01_03.wav','01_04.wav','01_05.wav',
                            '01_06.wav','01_07.wav','01_08.wav','01_09.wav','01_10.wav',
                            '01_11.wav','01_12.wav','01_13.wav','01_14.wav','01_15.wav',
                            '01_16.wav','01_17.wav','01_18.wav','01_19.wav','01_20.wav']:
                    continue
                # 14

                if _sec.endswith('wav'):
                    sec =_sec.split('_')[1].split('.')[0]
                    sound = AudioSegment.from_file("%s/%s"%(cur_path,_sec))
                    chunks = split_on_silence(sound,
                             min_silence_len=1050,
                             silence_thresh=-32,
                             keep_silence=100
                    )

                    total_duration = math.ceil(len(sound)/1000.0)
                    # print('total_duration:%s,%s '%(total_duration, len(''.join(words[sec]))))
                    ratio = len(''.join(words[sec])) / total_duration

                    cursor = 0
                    last_cursor = 0
                    for i, chunk in enumerate(chunks):
                        duration = math.ceil(len(chunk)/1000.0)
                        estimate_char_num = duration * ratio
                        # print('estimate_char_num:%s'%estimate_char_num )

                        accum_char_num = 0
                        last_cursor = cursor
                        while ( (estimate_char_num >= 60 and accum_char_num/estimate_char_num <= 1.07) or (60>estimate_char_num >= 50 and accum_char_num/estimate_char_num <= 1.10) or (50>estimate_char_num >= 30 and accum_char_num/estimate_char_num <= 1.20) or (30>estimate_char_num >= 23 and accum_char_num/estimate_char_num <= 1.25) or (13 <= estimate_char_num < 23 and accum_char_num/estimate_char_num <= 1.26) or (6<=estimate_char_num < 13 and accum_char_num/estimate_char_num <= 1.4) or (estimate_char_num < 6 and accum_char_num/estimate_char_num <= 1.45)) and cursor < len(words[sec]):
                            accum_char_num += len(words[sec][cursor])
                            if len(words[sec][cursor])<3 and accum_char_num/estimate_char_num > 0.9:
                                break
                            if ( (estimate_char_num >= 60 and accum_char_num/estimate_char_num <= 1.07) or (60>estimate_char_num >= 50 and accum_char_num/estimate_char_num <= 1.10) or (50>estimate_char_num >= 30 and accum_char_num/estimate_char_num <= 1.20) or (30>estimate_char_num >= 23 and accum_char_num/estimate_char_num <= 1.25) or (13 <= estimate_char_num < 23 and accum_char_num/estimate_char_num <= 1.26) or (6<=estimate_char_num < 13 and accum_char_num/estimate_char_num <= 1.4) or (estimate_char_num < 6 and accum_char_num/estimate_char_num <= 1.45)):
                                cursor += 1
                            # elif cursor > last_cursor and  (len(words[sec][cursor+1]) / math.ceil(len(chunks[i+1])/1000.0) * ratio) > 1.5:
                            #     cursor += 1

                                # if cursor - last_cursor > 2:
                                #     accum_char_num += 0.3


                        if cursor == last_cursor:
                            cursor += 1
                        elif cursor < len(words[sec]):
                            accum_char_num -= len(words[sec][cursor])

                        if accum_char_num/estimate_char_num < 0.75 and cursor < len(words[sec]):
                            cursor += 1
                            if cursor < len(words[sec]):
                                accum_char_num += len(words[sec][cursor])
                        if i == len(chunks)-1:
                            cursor += 10000
                        print('%s...ratio:%s'%(words[sec][last_cursor:cursor],accum_char_num/estimate_char_num ))
                        print('%s,%s,%s'%(sec,i,estimate_char_num))
                        wav_file = "/Users/chibs/playground/bigdata-stack/themes/speech-reg/DeepSpeech/test/%s_chunk_%02d.wav"%(sec,i)
                        chunk.export(wav_file , format="wav")
                        #chunk.export("%s_chunk_%02d.wav"%(sec,i), format="wav")
                        size = os.path.getsize(wav_file)

                        output.write("%s,%s,%s\n"%(wav_file,size,''.join(words[sec][last_cursor:cursor])))
                    #print(words[sec])


                # break
            break
        break

def split_txt():
    from sklearn.model_selection import train_test_split
    full = open('trans.full.csv').readlines()[1:]
    train_file = open('trans.train.csv','w')
    train_file.write('wav_filename,wav_filesize,transcript\n')
    test_file = open('trans.test.csv','w')
    test_file.write('wav_filename,wav_filesize,transcript\n')

    train,test = train_test_split(full,test_size=0.2)

    print(len(train),len(test))
    for data in train:
        train_file.write(data)
    for data in test:
        test_file.write(data)
if __name__ == '__main__':
    split_txt()
#split_wav()
