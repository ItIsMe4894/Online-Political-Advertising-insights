import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from os import listdir
from os.path import isfile, join
import os, psutil

# Returns dataframe without columns that we dont use
def loadCsv(csv):
    df = pd.read_csv(csv)
    df = df.drop(columns=['page_id', 'page_name', 'ad_creation_time', 'ad_delivery_stop_time', 'byline', 'impressions', 'spend', 'currency', 'demographic_distribution', 'delivery_by_region', 'publisher_platforms', 'estimated_audience_size', 'languages'])
    return df

def filterDef(row):
    print(row)
    exit()

democratDir = './ads/democrats'
republicanDir = './ads/republicans'

stopwords = set([i.lower() for i in STOPWORDS])

for party, directory in {'democrats': democratDir, 'republicans': republicanDir}.items():
    dfs = []
    onlyfiles = [f for f in listdir(directory) if isfile(join(directory, f))]
    for file in onlyfiles:
        dfs.append(loadCsv(directory + '/' + file))

    df = pd.concat(dfs)

    df['texts'] = df['ad_creative_bodies'].astype(str) + ' ' + df['ad_creative_link_titles'].astype(str) + ' ' + df['ad_creative_link_descriptions'].astype(str)
    df = df.drop(columns=['ad_creative_bodies', 'ad_creative_link_titles', 'ad_creative_link_descriptions'])
    df['texts'] = df['texts'].astype(str).str.replace('\n'," ")
    df = df.assign(texts=df['texts'].str.split(' ')).explode('texts')
    df = df.assign(texts=df['texts'].str.lower())
    df["texts"] = df['texts'].str.replace('[^\w\s]','')
    textCounts = df['texts'].value_counts()

    f = open(party+"-3-counts.txt", "a", encoding="utf-8")
    for word, count in textCounts.items():
        if (count < 3):
            break
        if (word.lower() not in stopwords):
            f.write(word + " --- " + str(count) + "\n")

    f.close()
