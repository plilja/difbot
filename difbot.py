import requests
import sys
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
                res |= {Result(xs[0], xs[1].replace('_', ' '), int(xs[2]), xs[3].replace('_', ' '), int(xs[4]))}
    return res


def write_published_result(result):
    with open(LOG_FILE_NAME, 'a') as f:
        f.write('%s %s %d %s %d\n' % (result.date, result.home.replace(' ', '_'), result.home_goals, result.away.replace(' ', '_'), result.away_goals))


def publish_result(result):
    if 'Djurgården' == result.home and result.home_goals > result.away_goals:
        should_publish = True
    elif 'Djurgården' == result.away and result.away_goals > result.home_goals:
        should_publish = True
    else:
        should_publish = False

    if should_publish:
        url = sys.argv[1]
        room_id = sys.argv[2]
        key = sys.argv[3]
        url = "https://%s/v2/room/%s/notification?auth_token=%s" % (url, room_id, key)
        data = {
            "from": "DIF-Bot",
            "color": "green",
            "message_format": "text",
            "notify": False,
            "message": '%s - %s %d-%d' % (result.home, result.away, result.home_goals, result.away_goals)
        }
        try:
            resp = requests.post(url, data=data)
            print("Code:", resp.status_code, "Response:", resp.text)
        except Exception:
            traceback.print_exc()


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
    for r in get_new_results():
        if r not in published:
            publish_result(r)
            write_published_result(r)
            published |= {r}


if __name__ == "__main__":
    run()
