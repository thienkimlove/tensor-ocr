import os
import cv2
import random
import numpy as np 
import pandas as pd
import tensorflow as tf
from tensorflow.python.platform import gfile

ANNOTATION_FILE = 'gen_data/ano.csv'
CROP_DIR = 'gen_data/crops'

MAX_STR_LEN = 10
null = 43


def get_char_mapping():
    label_file = 'gen_data/charset-labels.txt'
    with open(label_file, "r") as f:
        char_mapping = {}
        rev_char_mapping = {}
        for line in f.readlines():
            m, c = line.split("\n")[0].split("\t")
            char_mapping[c] = m
            rev_char_mapping[m] = c
    return char_mapping, rev_char_mapping


def read_image(img_path):
    return cv2.imread(img_path)


def padding_char_ids(char_ids_unpadded, null_id = null, max_str_len=MAX_STR_LEN):
    return char_ids_unpadded + [null_id for x in range(max_str_len - len(char_ids_unpadded))]


def get_bytelist_feature(x):
    return tf.train.Feature(bytes_list = tf.train.BytesList(value=x))


def get_floatlist_feature(x):
    return tf.train.Feature(float_list = tf.train.FloatList(value=x))


def get_intlist_feature(x):
    return tf.train.Feature(int64_list = tf.train.Int64List(value=[int(y) for y in x]))


def get_tf_example(img_file, annotation, num_of_views=1):

	img_array = read_image(img_file)
	img = gfile.FastGFile(img_file, 'rb').read()
	char_map, _ = get_char_mapping()

	split_text = [x for x in annotation]
	char_ids_unpadded = [char_map[x] for x in split_text]
	char_ids_padded = padding_char_ids(char_ids_unpadded)
	char_ids_unpadded = [int(x) for x in char_ids_unpadded]
	char_ids_padded = [int(x) for x in char_ids_padded]

	features = tf.train.Features(feature = {
		'image/format': get_bytelist_feature([b'png']),
		'image/encoded': get_bytelist_feature([img]),
		'image/class': get_intlist_feature(char_ids_padded),
		'image/unpadded_class': get_intlist_feature(char_ids_unpadded),
		# 'image/height': get_intlist_feature([img_array.shape[0]]),
		'image/width': get_intlist_feature([img_array.shape[1]]),
		'image/orig_width': get_intlist_feature([img_array.shape[1]/num_of_views]),
		'image/text': get_bytelist_feature([annotation.encode('utf-8')])
		}
	)
	example = tf.train.Example(features=features)

	return example


def get_tf_records(train_total, test_total):
	train_file = 'gen_data/train.tfrecord'
	test_file = 'gen_data/test.tfrecord'
	valid_file = 'gen_data/valid.tfrecord'
	if os.path.exists(train_file):
		os.remove(train_file)
	if os.path.exists(test_file):
		os.remove(test_file)
	if os.path.exists(valid_file):
		os.remove(valid_file)
	train_writer = tf.io.TFRecordWriter(train_file)
	test_writer = tf.io.TFRecordWriter(test_file)
	valid_writer = tf.io.TFRecordWriter(valid_file)
	annot = pd.read_csv(ANNOTATION_FILE)
	files = list(annot['files'].values)
	random.shuffle(files)

	record_train = 0
	record_test = 0
	record_valid = 0

	for i, file in enumerate(files):
		print('writing file:', file)
		annotation = annot[annot['files'] == file]
		annotation = annotation['text'].values[0]
		example = get_tf_example(CROP_DIR + '/' + file, annotation)
		if i < train_total:
			train_writer.write(example.SerializeToString())
			record_train += 1
		elif i < test_total:
			test_writer.write(example.SerializeToString())
			record_test += 1
		else:
			valid_writer.write(example.SerializeToString())
			record_valid += 1

	train_writer.close()
	test_writer.close()
	valid_writer.close()

	print("TOtal train {}".format(record_train))
	print("TOtal test {}".format(record_test))
	print("TOtal valid {}".format(record_valid))


if __name__ == '__main__':
	get_tf_records(500, 700)





