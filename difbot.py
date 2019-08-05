import requests
import sys
from bs4 import BeautifulSoup
import re
import os
import traceback
from collections import namedtuple

Result = namedtuple('Result', 'date home home_goals away away_goals')
TableTeam = namedtuple('TableTeam', 'position team_name points')

LOG_FILE_NAME = __file__ + '.log'

arg = sys.argv[1]
url = sys.argv[2]
room_id = sys.argv[3]
key = sys.argv[4]

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


def publish(fr, message):
    uri = 'https://%s/v2/room/%s/notification?auth_token=%s' % (url, room_id, key)
    data = {
        'from': '%s' % fr,
        'color': 'green',
        'message_format': 'text',
        'notify': False,
        'message': '%s' % (message)
    }
    try:
        resp = requests.post(uri, data=data)
        print("Code:", resp.status_code, "Response:", resp.text)
    except Exception:
        traceback.print_exc()


def publish_result(result):
    if 'Djurgården' == result.home and result.home_goals > result.away_goals:
        should_publish = True
    elif 'Djurgården' == result.away and result.away_goals > result.home_goals:
        should_publish = True
    else:
        should_publish = False

    if should_publish:
        message = '%s - %s %d-%d' % (result.home, result.away, result.home_goals, result.away_goals)
        publish('Allsvenskt resultat', message)


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


def publish_table(table):
    stockholm_teams = ['AIK', 'Djurgården', 'Hammarby']
    stockholm_table = list(filter(lambda x: x in stockholm_teams, map(lambda x: x.team_name, table)))
    if stockholm_table[0] == 'Djurgården':
        message = '\n'.join(map(lambda x: '%2d %16s %3d' % (x.position, x.team_name, x.points), table))
        publish('Allsvensk tabell', message)


def get_table():
    resp = requests.get('https://www.svt.se/svttext/tv/pages/343.html')
    if resp.status_code != 200:
        sys.exit(1)

    res = []
    soup = BeautifulSoup(resp.text, 'html.parser')
    for line in map(str.strip, soup.text.split('\n')):
        m = re.match(r'(\d+) +([A-Za-zÅÄÖåäö ]+) +\d+ +\d+ +\d+ +\d+ +\d+-\d+ +(\d+)', line)
        if m:
            [position, team, points] = m.groups()
            res += [TableTeam(int(position), team.strip(), int(points))]
    return res


def run():
    if arg == 'table':
        publish_table(get_table())
    elif arg == 'result':
        published = get_published_results()
        for r in get_new_results():
            if r not in published:
                publish_result(r)
                write_published_result(r)
                published |= {r}
    else:
        print('Valid first arguments are table or result')
        sys.exit(1)


if __name__ == "__main__":
    run()
