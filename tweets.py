import csv
import re
import os
import sys
from urllib.request import urlopen
import matplotlib.pyplot as plt

import pandas as pd
import tweepy

auth = tweepy.OAuthHandler(os.environ['TWITTER_API_KEY'],
                           os.environ['TWITTER_API_SECRET_KEY'])
auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'],
                      os.environ['TWITTER_ACCESS_TOKEN_SECRET'])

api = tweepy.API(auth)

try:
    api.verify_credentials()
except:
    print("Error during authentication")


def process(df, handle, groupby, distinct_count, series_name, by):
    df = df.groupby(groupby)[distinct_count].nunique().sort_values(ascending=False)
    df.to_csv(f'{handle}_by_{by}.csv')
    fig, ax = fig, ax = plt.subplots(figsize=(20, 10))
    df.plot.bar(y=series_name, title=f'{handle} tweets by {by}', ax=ax)
    plt.setp(ax.get_xticklabels(), rotation=270, ha="left", rotation_mode="anchor")
    fig.subplots_adjust(bottom=0.3)
    fig.savefig(f'{handle}_by_{by}.png')


def analyse_user(handle):
    with open(f'{handle}.csv', 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['tweet_id', 'tweet_source', 'user_screen_name', 'user_name',
                      'handle', 'mentioned_name', 'url', 'base_url', 'url_obfuscated']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tweet in api.user_timeline(screen_name=handle, count=1000, include_rts=False, tweet_mode='extended'):
            if tweet.in_reply_to_status_id is None:
                mentions = tweet.entities['user_mentions']
                if not mentions:
                    mentions = [{'screen_name': 'no mentions', 'name': 'no mentions'}]

                urls = tweet.entities['urls']
                if not urls:
                    urls = [{'expanded_url': 'no link'}]
                for url in urls:
                    expanded_url = url['expanded_url']
                    if 'bit.ly' in expanded_url:
                        expanded_url = urlopen(expanded_url).geturl()
                        url['expanded_url'] = expanded_url
                        url['url_obfuscated'] = True
                    else:
                        url['url_obfuscated'] = False

                for mention in mentions:
                    for url in urls:
                        if not url['expanded_url'].startswith('https://twitter.com'):
                            writer.writerow({'tweet_id': tweet.id,
                                             'tweet_source': tweet.source,
                                             'user_screen_name': tweet.user.screen_name,
                                             'user_name': tweet.user.name,
                                             'handle': mention['screen_name'],
                                             'mentioned_name': mention['name'],
                                             'url': url['expanded_url'],
                                             'base_url': re.sub(r'((http)s?://)?(www.)?', "", url['expanded_url'])
                                            .split('/')[0],
                                             'url_obfuscated': url['url_obfuscated']
                                             })

    df = pd.read_csv(f'{handle}.csv')
    process(df, handle, groupby='handle', distinct_count='tweet_id', series_name='tweet_count', by='handle')
    process(df, handle, groupby='base_url', distinct_count='tweet_id', series_name='tweet_count', by='url')


def main():
    for user in sys.argv[1:]:
        analyse_user(user)


if __name__ == "__main__":
    main()
