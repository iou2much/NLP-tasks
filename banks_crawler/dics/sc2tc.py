#coding:utf-8
from langconv import *

def sc2tc(line):
    #将简体转换成繁体
    line = Converter('zh-hant').convert(line.decode('utf-8'))
    line = line.encode('utf-8')
    return line  
                  
def tc2sc(line):  
    # 将繁体转换成简体  
    line = Converter('zh-hans').convert(line.decode('utf-8'))  
    line = line.encode('utf-8')  
    return line  

scDictFile = open('dict.txt')
tcDictFile = open('dict-tc.txt','w')
for line in scDictFile.readlines():
    tcDictFile.write(sc2tc(line))
                                            
