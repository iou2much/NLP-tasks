
import pandas
import tensorflow as tf

from threading import Thread
from math import ceil
from six.moves import range
from util.audio import audiofile_to_input_vector
from util.gpu import get_available_gpus
from util.text import ctc_label_dense_to_sparse, text_to_char_array

class DataSets(object):
    def __init__(self, train, dev, test):
        '''Container for train, dev and test sets of one corpus.

        Args:
            train (DataSet): the train data set of the corpus
            dev (DataSet): the validation data set of the corpus
            test (DataSet): the test data set of the corpus
        '''
        self._dev = dev
        self._test = test
        self._train = train

    def start_queue_threads(self, session):
        self._dev.start_queue_threads(session)
        self._test.start_queue_threads(session)
        self._train.start_queue_threads(session)

    @property
    def train(self):
        return self._train

    @property
    def dev(self):
        return self._dev

    @property
    def test(self):
        return self._test

class DataSet(object):
    def __init__(self, files_list, thread_count, batch_size, numcep, numcontext, next_index=lambda x: x + 1):
        self._coord = None
        self._numcep = numcep
        self._x = tf.placeholder(tf.float32, [None, numcep + (2 * numcep * numcontext)])
        self._x_length = tf.placeholder(tf.int32, [])
        self._y = tf.placeholder(tf.int32, [None,])
        self._y_length = tf.placeholder(tf.int32, [])
        self.example_queue = tf.PaddingFIFOQueue(shapes=[[None, numcep + (2 * numcep * numcontext)], [], [None,], []],
                                                  dtypes=[tf.float32, tf.int32, tf.int32, tf.int32],
                                                  capacity=2 * self._get_device_count() * batch_size)
        self._enqueue_op = self.example_queue.enqueue([self._x, self._x_length, self._y, self._y_length])
        self._close_op = self.example_queue.close(cancel_pending_enqueues=True)
        self.batch_size = batch_size
        self._numcontext = numcontext
        self._thread_count = thread_count
        self._files_list = self._create_files_list(files_list)
        self._next_index = next_index

    def _get_device_count(self):
        available_gpus = get_available_gpus()
        return max(len(available_gpus), 1)

    def start_queue_threads(self, session, coord):
        self._coord = coord
        batch_threads = [Thread(target=self._populate_batch_queue, args=(session,)) for i in range(self._thread_count)]
        for batch_thread in batch_threads:
            self._coord.register_thread(batch_thread)
            batch_thread.daemon = True
            batch_thread.start()
        return batch_threads

    def close_queue(self, session):
        session.run(self._close_op)

    def _create_files_list(self, files_list):
        # 1. Sort by wav filesize
        # 2. Select just wav filename and transcript columns
        # 3. Return a NumPy representation
        return files_list.sort_values(by="wav_filesize")        \
                         .ix[:, ["wav_filename", "transcript"]] \
                         .values

    def _indices(self):
        index = -1
        while not self._coord.should_stop():
            index = self._next_index(index) % len(self._files_list)
            yield self._files_list[index]

    def _populate_batch_queue(self, session):
        for wav_file, transcript in self._indices():
            source = audiofile_to_input_vector(wav_file, self._numcep, self._numcontext)
            source_len = len(source)
            target = text_to_char_array(transcript)
            target_len = len(target)
            try:
                session.run(self._enqueue_op, feed_dict={
                    self._x: source,
                    self._x_length: source_len,
                    self._y: target,
                    self._y_length: target_len})
            except tf.errors.CancelledError:
                return

    def next_batch(self):
        source, source_lengths, target, target_lengths = self.example_queue.dequeue_many(self.batch_size)
        sparse_labels = ctc_label_dense_to_sparse(target, target_lengths, self.batch_size)
        return source, source_lengths, sparse_labels

    @property
    def total_batches(self):
        # Note: If len(_files_list) % batch_size != 0, this re-uses initial files
        return int(ceil(len(self._files_list) / self.batch_size))

class SwitchableDataSet(object):
    def __init__(self, data_sets):
        '''Data set that is wrapping a data sets instance to switch between train, dev and test instances during training.

        Args:
            data_sets (DataSets): the corpus container holding all three data sets
        '''
        self._data_sets = data_sets
        self._sets = [data_sets.train, data_sets.dev, data_sets.test]
        self._queues = [s.example_queue for s in self._sets]
        self._queue_selector = tf.placeholder(tf.int32, name='Queue_Selector')
        self._queue = tf.QueueBase.from_list(self._queue_selector, self._queues)
        self._close_op = self._queue.close(cancel_pending_enqueues=True)
        self._data_set = data_sets.train

    def set_data_set(self, feed_dict, data_set):
        index = self._sets.index(data_set)
        assert index >= 0
        feed_dict[self._queue_selector] = index
        self._data_set = data_set

    def start_queue_threads(self, session, coord):
        batch_threads = []
        for s in self._sets:
            batch_threads += s.start_queue_threads(session, coord)
        return batch_threads

    def close_queue(self, session):
        session.run(self._close_op, feed_dict={ self._queue_selector: 0 })
        for s in self._sets:
            s.close_queue(session)

    def next_batch(self):
        source, source_lengths, target, target_lengths = self._queue.dequeue_many(self._data_set.batch_size)
        sparse_labels = ctc_label_dense_to_sparse(target, target_lengths, self._data_set.batch_size)
        return source, source_lengths, sparse_labels

def read_data_sets(train_csvs, dev_csvs, test_csvs,
                   train_batch_size, dev_batch_size, test_batch_size,
                   numcep, numcontext, thread_count=8,
                   stride=1, offset=0, next_index=lambda s, i: i + 1,
                   limit_dev=0, limit_test=0, limit_train=0):
    # Read the processed set files from disk
    def read_csvs(csvs):
        files = None
        for csv in csvs:
            file = pandas.read_csv(csv)
            if files is None:
                files = file
            else:
                files = files.append(file)
        return files

    train_files = read_csvs(train_csvs)
    dev_files = read_csvs(dev_csvs)
    test_files = read_csvs(test_csvs)

    # Create train DataSet from all the train archives
    train = _read_data_set(train_files, thread_count, train_batch_size, numcep, numcontext, stride=stride, offset=offset, next_index=lambda i: next_index('train', i), limit=limit_train)

    # Create dev DataSet from all the dev archives
    dev = _read_data_set(dev_files, thread_count, dev_batch_size, numcep, numcontext, stride=stride, offset=offset, next_index=lambda i: next_index('dev', i), limit=limit_dev)

    # Create test DataSet from all the test archives
    test = _read_data_set(test_files, thread_count, test_batch_size, numcep, numcontext, stride=stride, offset=offset, next_index=lambda i: next_index('test', i), limit=limit_test)

    # Return DataSets
    return DataSets(train, dev, test)

def _read_data_set(filelist, thread_count, batch_size, numcep, numcontext, stride=1, offset=0, next_index=lambda i: i + 1, limit=0):
    # Optionally apply dataset size limits
    if limit > 0:
        filelist = filelist.iloc[:limit]

    filelist = filelist[offset::stride]

    # Return DataSet
    return DataSet(filelist, thread_count, batch_size, numcep, numcontext, next_index=next_index)
