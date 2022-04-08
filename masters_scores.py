import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import gspread



def main():
    """
    Each of 8 players got to pick x number of players from five categories (13 total picks).
    Each player is scored on the combined over/under par of their top five picks
    This code pulls all golf leaderboard scores and compares them to participant's picks, and calculates overall scores

    reference google sheet: https://docs.google.com/spreadsheets/d/1HAWlREraUSJRVmaw3FSzeaqy3VRehL2gowTgTctg0X0/edit#gid=1256000086
    :return:
    """
    # reads in picks from json config
    picks = store_picks()

    # scrapes espn leaderboard for tournament scores
    scores = get_scores_and_players()

    # sends all scores and picks to calculate and publish results
    calculate_and_publish_scores(scores, picks)


def store_picks() -> dict:
    """
    Reads from a file titled picks_cfg.json which is stores "name: list(picks)" pairs.
    Essentially just used to cut down on code clutter
    :return: a python dict with participant_name:pick_list key/values
    """
    with open('picks_cfg.json') as json_file:
        picks = json.load(json_file)
    return picks


def get_scores_and_players() -> pd.DataFrame:
    """
    Scrapes ESPN leaderboard site for all player's scores.
    :return: dataframe with two columns: name and score
    """
    # get leaderboard html
    result = requests.get("http://www.espn.com/golf/leaderboard")
    soup = BeautifulSoup(result.text, "html.parser")
    header_rows = soup.find_all("tr",
                                class_="PlayerRow__Overview PlayerRow__Overview--expandable Table__TR Table__even")

    # dict for score pairs
    scores = []

    # looks at each row in the table of scores and enters scores.
    # if score != integer, sets other level
    for row, index in zip(header_rows, range(0, len(header_rows))):
        name = header_rows[index].find_all("a")
        score = header_rows[index].find_all("td")
        name = str(name[0].contents[0]).lower()
        try:
            score = int(score[3].contents[0])
        except ValueError:
            # set score to 0 if score = 'E' (even)
            if (score[3].contents[0]) == 'E':
                score = 0
            else:
                score = 1000  # doesn't mean anything, just don't want to count players unless they are playing and have a score listed
        pair = {'Name': name, 'Score': score}
        scores.append(pair)
    # change dict into dataframe for easier manipulation
    scores = pd.DataFrame(scores)

    return scores


def calculate_and_publish_scores(scores: pd.DataFrame, picks: dict) -> None:
    # creates google spreadsheet object and opens the sheet of interest by url key
    gc = gspread.service_account(filename='C:/Users/u0955471/service_account.json')
    sh = gc.open_by_key("1HAWlREraUSJRVmaw3FSzeaqy3VRehL2gowTgTctg0X0")

    # show all picks scores
    leaderboard = []
    for key in picks:
        # breaks down dict to iterables
        name = key
        choices = picks[name]
        # retrieves list of players for each participant
        ind_scores = scores[scores['Name'].isin(choices)]
        # sorts by score ascending
        ind_scores = ind_scores.sort_values(by='Score', ascending=True)
        # makes names into proper case for aesthetics
        ind_scores['Name'] = ind_scores['Name'].str.title()
        # writes each individual's picks/scores to a separate spreadsheet (created beforehand)
        worksheet = sh.worksheet(name)
        worksheet.clear()
        worksheet.update([ind_scores.columns.values.tolist()] + ind_scores.values.tolist())
        # gets top 5 scores (head returns five values, already sorted ascending)
        top_5 = ind_scores.head()
        # takes combined top 5 scores
        top_5_sum = top_5['Score'].sum()
        # stores scores in leaderboard df
        leaderboard_scores = {'Name': name, 'Top 5 Combined Score': top_5_sum}
        leaderboard.append(leaderboard_scores)

    # sort scores ascending and publish to Leaderboard worksheet
    leaderboard = pd.DataFrame(leaderboard)
    leaderboard.sort_values(by='Top 5 Combined Score', ignore_index=True, inplace=True)

    # publish overall scores to spreadsheet
    worksheet = sh.worksheet('Leaderboard')
    worksheet.clear()
    worksheet.update([leaderboard.columns.values.tolist()] + leaderboard.values.tolist())


if __name__ == "__main__":
    main()
