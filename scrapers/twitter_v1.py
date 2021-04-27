# -*- coding: utf-8 -*-
"""Scraper to Twitter V1
* Autor: Alixandro
* Versão: 0.0.2
* Editor de Texto: indent=4 speces=1
* Requisitos:
  + tweepy>=3.10.0
  + pandas
  + nltk>=3.6.2
  + textblob>=0.15.3
"""

# importa os pacotes necessários
import os
import tweepy
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import numpy as np
import re
from zipfile import ZipFile
from nltk.corpus import stopwords
import string
import traceback
import datetime

# autenticação com o Twitter
consumer_key = 'wupqfMXWTodaVXGo9AwlUKsql'
consumer_secret = 'crAtEKHUlsN9zw9CagyJj1QnyPPvsk7s7E1kVqZg6PcbTZbHTQ'
access_token = '874736407-zJ0r3VC4K2Q8DbnQlG7O3kwjEBIpdvreHqqWIl2e'
access_token_secret = 'NWMoZE0RACYnvCRBY791yymcAwke2DyWRRFzIUnc5MrTG'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, timeout=60)

# configuração da query
search_query = "covid 19+news -filter:retweets"
current_date = datetime.datetime.today()
cursor_limit = 50000
tweets = tweepy.Cursor(api.search, q=search_query, lang="en", location=True, created_at=True, since=current_date.strftime('%Y-%m-%d'), source=True).items(cursor_limit)
tweets

# collect a list of tweets by content, user, location
allinfo = []
try:
    for tweet in tweets:
        allinfo.append([tweet.user.url,tweet.created_at,tweet.source,tweet.text,tweet.user.screen_name, tweet.user.location])
except (Exception ) as e: traceback.print_stack()

df = pd.DataFrame(allinfo, columns = ['URL','Date','Source','Text','Author','Country'])
df

# remover linhas dumplicadas
df.drop_duplicates(subset=['Text'], keep=False, inplace=True)
# inserir novas colunas ao DataFrame não providos pela API do Twitter
df.insert(3, 'Categories','#')
df.insert(4, 'Search', search_query)
# versão final do DataFrame
df.head(3)

if not os.path.exists('csv'): os.makedirs('csv')  # criar uma pasta chamada csv caso não exista
out_csv_1 = 'csv/tweets_{data}.csv'.format(data=current_date.strftime('%Y-%m-%d'))
df.to_csv(out_csv_1)  # salvar o dataframe em csv

if not os.path.exists('zip'): os.makedirs('zip')
nome_zip = 'data-{data}.zip'.format(data=current_date.strftime('%Y-%m'))
zipObj = ZipFile('zip/%s' % nome_zip, mode='a')  # mode='a': abre o zip para atualização
zipObj.write(out_csv_1)  # adiciona o CSV ao zip
zipObj.close()  # salva o zip e fecha
