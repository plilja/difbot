import requests
from bs4 import BeautifulSoup
import sys
import re
import time
import os
from collections import namedtuple

Result = namedtuple('Result', 'date home home_goals away away_goals')

LOG_FILE_NAME = __file__ + '.log'

def get_published_results():
    res = set()
    if os.path.isfile(LOG_FILE_NAME):
        with open(LOG_FILE_NAME) as f:
            for row in f:
                xs = row.split()
                res |= {Result(xs[0], xs[1], int(xs[2]), xs[3], int(xs[4]))}
    return res


def write_published_result(result):
    with open(LOG_FILE_NAME, 'a') as f:
        f.write('%s %s %d %s %d\n' % (result.date, result.home, result.home_goals, result.away, result.away_goals))


def publish_result(result):
    if len(sys.argv) > 1 and sys.argv[1] == 'onlywins':
        if 'Djurgården' == result.home and result.home_goals > result.away_goals:
            should_publish = True
        elif 'Djurgården' == result.away and result.away_goals > result.home_goals:
            should_publish = True
        else:
            should_publish = False
    else:
        should_publish = True

    if should_publish:
        print(result)


def get_new_results():
    resp = requests.get('https://www.svt.se/svttext/tv/pages/344.html')
    if resp.status_code != 200:
        sys.exit(1)

    res = []
    soup = BeautifulSoup(resp.text, 'html.parser')
    for line in map(str.strip, soup.text.split('\n')):
        args = []
        for a in line.split(' - '):
            args += a.split('  ')
        args = [a.strip() for a in args if a.strip()]
        if len(args) > 0 and re.match(r'\d+\/\d+', args[0]):
            date = args[0]
        if len(args) in [3, 4] and re.match(r'\d+-\d+', args[-1]):
            if 'Djurgården' in args:
                [h, a] = list(map(int, args[-1].split('-')))
                res += [Result(date, args[-3], h, args[-2], a)]
    return res


def run():
    published = get_published_results()
    while True:
        for r in get_new_results():
            if r not in published:
                publish_result(r)
                write_published_result(r)
                published |= {r}
        time.sleep(60 * 60)


if __name__ == "__main__":
    run()
