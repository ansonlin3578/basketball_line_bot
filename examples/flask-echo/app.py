# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# call nba-api
from nba_api.live.nba.endpoints import scoreboard
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        if event.message.text == "games":
            curr_time = datetime.now() - timedelta(days=1)
            curr_year, curr_month, curr_day = curr_time.year, curr_time.month, curr_time.day
            print("year : ", curr_year)
            print("month : ", curr_month)
            print("date : ", curr_day)

            # Today's Score Board
            games = scoreboard.ScoreBoard()

            games_count = len(games.get_dict()["scoreboard"]["games"])
            total_games = games.get_dict()["scoreboard"]["games"]
            pd_idx = ['Visit', 'Home']

            result_str = f'Date: {curr_year}-{curr_month}-{curr_day}\n'
            for i in range(games_count):
                teams = [total_games[i]['awayTeam']['teamCity'], total_games[i]['homeTeam']['teamCity']]
                totals = [total_games[i]['awayTeam']['score'], total_games[i]['homeTeam']['score']]
                data = {'team': teams,
                        'total': totals
                        }
                df = pd.DataFrame(data, index=pd_idx)
                game_string = df.to_string()
                result_str = f"{result_str}\n#########################\n" + game_string
                return 'OK'

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )

    return 'OK'


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
