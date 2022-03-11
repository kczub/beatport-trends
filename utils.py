import json
import pandas as pd


def jsonify_data(filepath):
    df = pd.read_csv(filepath)
    pd_data = df.to_json()
    json_data = json.loads(pd_data)

    genres = json_data.get('genre')
    n_occur = json_data.get('appearances')

    genre_list = [genre for genre in genres.values()]
    occur_list = [x for x in n_occur.values()]


    result = {}
    for k, v in zip(genre_list, occur_list):
        result[k] = v

    return result
