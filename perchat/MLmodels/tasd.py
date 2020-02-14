# from sklearn.externals import joblib
import numpy as np
import os
import pandas as pd
import csv
import tensorflow as tf

# APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# fea = np.array([gettingFeatures(text)])
# open(os.path.join(APP_ROOT, "MLmodels/vectorizer.pickle"), "rb")
# loaded_model = joblib.load("LogisticRegression.sav")
data = pd.read_excel('train.xlsx').values
# data=pd.read_csv('train.tsv',sep='\t',header=None).values
with open("test.tsv","w") as csvfile:
    writer = csv.writer(csvfile,delimiter="\t")
    for d in data:
    #先写入columns_name
        writer.writerow(d)
    #写入多行用writerows
    # writer.writerows([[0,1,3],[1,2,3],[2,3,4]])
with tf.gfile.Open("test.tsv", "r") as f:
  reader = csv.reader(f, delimiter="\t")
  lines = []
  for line in reader:
    line[1] = line[1].replace('\n', '')
    lines.append(line)
  print(lines[:4])

# print(data[0][0])