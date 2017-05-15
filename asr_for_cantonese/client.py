from pydub import AudioSegment

import sys
import scipy.io.wavfile as wav
from deepspeech import DeepSpeech
from format import decode_str

#sound = AudioSegment.from_file('test.mp3',format='mp3')
#sound.export('test.wav', format="wav")

ds = DeepSpeech('/Users/chibs/playground/bigdata-stack/themes/speech-reg/DeepSpeech/bibles_export/output_graph.pb', 26, 9)
fs, audio = wav.read(sys.argv[1])
#fs, audio = wav.read('01/chunk_04.wav')
output = ds.stt(audio, fs)
print(output)
print(decode_str(output))


#cbz aqk awp no ais kb cdo awz xi bwe bti alk bdn xy alk bud bsg aku
#cem ak aq ai kb cdo az xi ay ai alk xy alk bud cd xi
#以玛契线人的栖子麋线他为他是鸡子
