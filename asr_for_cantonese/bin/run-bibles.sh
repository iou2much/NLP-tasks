#!/bin/sh
set -xe
if [ ! -f DeepSpeech.py ]; then
    echo "Please make sure you run this from DeepSpeech's top level directory."
    exit 1
fi;

if [ ! -f "test/trans.train.csv" ]; then
    echo "empty data"
fi;

#checkpoint_dir=$(python -c 'from xdg import BaseDirectory as xdg; print(xdg.save_data_path("deepspeech/bibles"))')
#echo $checkpoint_dir
#/Users/chibs/.local/share/deepspeech/bibles
# --validation_step 5 \
# --default_stddev 0.046875 \
# --learning_rate 0.0005 \
# --use_warpctc True \

python -u DeepSpeech.py \
  --train_files test/trans.train.csv \
  --dev_files test/trans.test.csv \
  --test_files test/trans.test.csv \
  --train_batch_size 8 \
  --dev_batch_size 2 \
  --test_batch_size 2 \
  --epoch 50 \
  --display_step 1 \
  --dropout_rate 0.20 \
  --n_hidden 494 \
  --checkpoint_dir "bibles_checkpoint" \
  --export_dir "bibles_export" \
  "$@"
