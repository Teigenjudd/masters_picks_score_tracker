import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import datetime
import gspread



def main():
    picks = store_picks()
    scores = get_scores_and_players()
    calculate_and_publish_scores(scores, picks)

def store_picks():
    eric = ['cameron smith', 'rory mcilroy', 'patrick reed', 'robert macintyre', 'corey conners',
            'robert macintyre', 'thomas pieters', 'talor gooch', 'seamus power', 'patrick cantlay',
            'russell henley', 'tiger woods', 'sam burns']
    tate = ['justin thomas', 'scottie scheffler', 'patrick cantlay', 'bryson dechambeau', 'tiger woods',
            'sam burns', 'max homa', 'tony finau', 'patrick reed', 'joaquin niemann', 'talor gooch',
            'matthew wolff', 'cameron champ']
    andreas = ['justin thomas', 'jon rahm', 'patrick cantlay', 'daniel berger', 'louis oosthuizen', 'sam burns',
               'bubba watson', 'tony finau', 'sungjae im', 'max homa', 'kevin kisner', 'seamus power',
               'brian harman']
    kirk = ['jon rahm', 'cameron smith', 'hideki matsuyama', 'collin morikawa', 'louis oosthuizen', 'sam burns',
            'abraham ancer', 'joaquin niemann', 'tony finau', 'shane lowry', 'gary woodland', 'kevin kisner',
            'kevin na']
    kelly = ['dustin johnson', 'justin thomas', 'xander schauffele', 'patrick cantlay', 'paul casey',
             'marc leishman', 'shane lowry', 'sergio garcia', 'billy horschel', 'tommy fleetwood',
             'christiaan bezuidenhout', 'gary woodland', 'thomas pieters']
    hayden = ['jon rahm', 'scottie scheffler', 'xander schauffele', 'collin morikawa', 'tiger woods',
              'louis oosthuizen', 'shane lowry', 'corey conners', 'tony finau', 'sungjae im', 'gary woodland',
              'thomas pieters', 'talor gooch']
    matt = ['scottie scheffler', 'cameron smith', 'collin morikawa', 'xander schauffele', 'sam burns',
            'matt fitzpatrick', 'shane lowry', 'tony finau', 'joaquin niemann', 'abraham ancer', 'kevin kisner',
            'seamus power', 'kevin na']
    teigen = ['scottie scheffler', 'cameron smith', 'collin morikawa', 'hideki matsuyama', 'tyrrell hatton',
              'matt fitzpatrick', 'max homa', 'patrick reed', 'corey conners', 'shane lowry', 'thomas pieters',
              'cameron champ', 'matthew wolff']
    picks = {'Eric': eric, 'Tate': tate, 'Andreas': andreas, 'Kirk': kirk, 'Kelly': kelly, 'Hayden': hayden,
             'Matt': matt, 'Teigen': teigen}
    return picks


def get_scores_and_players():
    result = requests.get("http://www.espn.com/golf/leaderboard")
    soup = BeautifulSoup(result.text, "html.parser")
    header_rows = soup.find_all("tr",
                                class_="PlayerRow__Overview PlayerRow__Overview--expandable Table__TR Table__even")

    # other possible entries for what could show up, add here.
    scores = []
    players = []

    for row, index in zip(header_rows, range(0, len(header_rows))):
        name = header_rows[index].find_all("a")
        score = header_rows[index].find_all("td")
        name = str(name[0].contents[0]).lower()
        try:
            score = int(score[3].contents[0])
        except ValueError:
            if (score[3].contents[0]) == 'E':
                score = 0
            else:
                score = 1000  # doesn't mean anything, just don't want to count players unless they are playing and have a score listed
        pair = {'Name': name, 'Score': score}
        players.append(name)
        scores.append(pair)
    scores = pd.DataFrame(scores)
    print(scores)
    return scores


def calculate_and_publish_scores(scores, picks):
    gc = gspread.service_account(filename='C:/Users/u0955471/service_account.json')
    sh = gc.open_by_key("1HAWlREraUSJRVmaw3FSzeaqy3VRehL2gowTgTctg0X0")

    # show all picks scores
    leaderboard = []
    for key in picks:
        name = key
        choices = picks[name]
        ind_scores = scores[scores['Name'].isin(choices)]
        ind_scores = ind_scores.sort_values(by='Score', ascending=True)
        print(name)
        print(ind_scores)
        ind_scores['Name'] = ind_scores['Name'].str.title()
        worksheet = sh.worksheet(name)
        worksheet.clear()
        worksheet.update([ind_scores.columns.values.tolist()] + ind_scores.values.tolist())
        top_5 = ind_scores.head()
        top_5_sum = top_5['Score'].sum()
        leaderboard_scores = {'Name': name, 'Top 5 Combined Score': top_5_sum}
        leaderboard.append(leaderboard_scores)

    leaderboard = pd.DataFrame(leaderboard)
    leaderboard.sort_values(by='Top 5 Combined Score', ignore_index=True, inplace=True)

    worksheet = sh.worksheet('Leaderboard')
    worksheet.clear()
    worksheet.update([leaderboard.columns.values.tolist()] + leaderboard.values.tolist())


if __name__ == "__main__":
    main()
