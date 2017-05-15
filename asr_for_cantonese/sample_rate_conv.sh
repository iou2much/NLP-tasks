#!/bin/bash
#for x in ./wav/*/*/*.wav
#do 
#  b=${x##*/}
#  echo $b
#  #sox $b -r 16000 tmp_$b
#  #rm -rf $b
#  #mv tmp_$b $b
#done

#!/bin/sh
list_alldir(){  
    #echo $PWD
    for file2 in `ls $1`  
        do  
        #echo 'top:'$file2
            if [ x"$file2" != x"." -a x"$file2" != x".."  ];then  
                if [ -d "$1/$file2"  ];then  
                    echo "entering $1/$file2"  
                    cd "$1/$file2"  

                    if [ -f "chapname.txt" ];then
                        for x in ./*.wav
                        do
                            b=${x##*/}
                            echo $b
                            sox $b -r 16000 tmp_$b
                            rm -rf $b
                            mv tmp_$b $b
                        done
                    else
                        list_alldir .
                    fi
                    cd ..
                fi  
             fi  
        done
#    cd ..
}

list_alldir .

