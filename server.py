#!/usr/bin/python3

#
# YouTube remote API for Samsung TVs
#
# Allows remotely playing YouTube videos on a TV using a search query.
# Useful for IFTTT/automation purposes.
#
# Released under the MIT License https://opensource.org/licenses/MIT
# Copyright (c) Sami Alaoui Kendil (thedroidgeek)
#

import re
import sys
import json
import uuid
import time
import flask
import string
import threading
import traceback

from deps.ytsearch import YoutubeSearch
from deps.ytremote import YouTubeRemote, YouTubeCmd
from deps.utils import Config, WebRequest, TvUtil


if len(sys.argv) != 3:

    print('usage: %s <host> <port>' % sys.argv[0])
    exit()


Config('config.json')


api = flask.Flask(__name__)


@api.route('/ping', methods=['GET'])
def ping():
    return 'pong'


qlock = threading.Lock()

@api.route('/PlayYtQuery/<query>', methods=['GET'])
def PlayYtQuery(query):

    if qlock.locked():
        return 'Busy', 503

    with qlock:

        try:
            print("=> Processing YouTube remote query for: '%s'\n" % query)

            # search YouTube for videos using the query string
            searchResults = YoutubeSearch(str(query), max_results=10)
            print('=> Got %d YouTube search result(s)\n' % searchResults.count())
            '''for i in range(searchResults.count()):
                print('%d)' % (i + 1))
                print('Title: %s' % searchResults.as_dict()[i]['title'])
                print('ID: %s' % searchResults.as_dict()[i]['id'])
                print('Channel: %s' % searchResults.as_dict()[i]['channel'])
                print('Duration: %s' % searchResults.as_dict()[i]['duration'])
                print('Views: %s\n' % searchResults.as_dict()[i]['views'])'''

            if searchResults.count() == 0:
                return 'No results were found', 404

            # send Wake-on-LAN packet(s) to TV, in case it's off
            TvUtil.WoL()

            # initialize the YouTube remote
            remote = YouTubeRemote(Config.get('RemoteDisplayName'))

            if Config.get('ReadYtTokenFromDial'):
                # get the screen ID from the TV using the DIAL protocol
                screenId = TvUtil.getYtScreenId()
                print('=> Got YouTube screen ID from TV: %s\n' % screenId)

                # request the YouTube lounge API token using the screen ID
                loungeToken = remote.loadLoungeToken(screenId)
                print('=> Got lounge API token: %s\n' % loungeToken)

            else:
                # generate a random UUID for pairing
                code = remote.generatePairingcode()
                print('=> Generated a pairing code for the TV: %s\n' % code)

                # send YouTube pairing request to TV
                print('=> Sending a pairing request to the TV...\n')
                TvUtil.pairYt(code)

                # wait for pairing to succeed (or timeout)
                remote.waitForPairing(code)

            # set playing queue from YouTube search results
            print('=> Setting playing queue on TV...\n')
            firstVideoId = searchResults.as_dict()[0]['id']
            videoIdList = searchResults.as_csv_ids()
            remote.doCmd([YouTubeCmd(cmd="setPlaylist", videoId = firstVideoId, videoIds = videoIdList)])

            # play/pause to force the YouTube player UI to be briefly visible
            time.sleep(1)
            #remote.doCmd([YouTubeCmd(cmd="dpadCommand", key='UP')])
            remote.doCmd([YouTubeCmd(cmd="pause"), YouTubeCmd(cmd="play")])

        except:
            traceback.print_exc()
            return sys.exc_info(), 500

        return 'OK'


@api.route('/WakeTv', methods=['GET'])
def WakeTv():
    try:
        TvUtil.WoL()
        return 'OK'
    except:
        traceback.print_exc()
        return 'Error', 500


@api.route('/SetDisplayName/<name>', methods=['GET'])
def SetDisplayName(name):
    Config.set('RemoteDisplayName', name)
    return 'OK'


@api.route('/SetTvMac/<macAddr>', methods=['GET'])
def SetTvMac(macAddr):
    macAddr = macAddr.replace(':', '')
    if len(re.findall(r'[0-9A-Fa-f]{12}', macAddr)) == 1:
        Config.set('MacAddress', macAddr.upper())
        return 'OK'
    return 'Invalid format', 400


@api.route('/ClearTvMac', methods=['GET'])
def ClearTvMac():
    Config.clear('MacAddress')
    return 'OK'


@api.route('/SetTvHost/<host>', methods=['GET'])
def SetTvHost(host):
    Config.set('TvLanHost', host)
    return 'OK'


@api.errorhandler(404)
def page_not_found(e):
    return '404', 404


from werkzeug import serving

parent_log_request = serving.WSGIRequestHandler.log_request

def log_request(self, *args, **kwargs):

    # skip logging health check requests
    if self.path == '/ping':
        return

    parent_log_request(self, *args, **kwargs)

serving.WSGIRequestHandler.log_request = log_request


api.run(host=sys.argv[1], port=sys.argv[2])
