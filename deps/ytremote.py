#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Based on youtube-remote
# https://github.com/mutantmonkey/youtube-remote
# https://github.com/qermit/youtube-remote
#
# Released under the ISC License https://opensource.org/licenses/ISC
# Copyright (c) mutantmonkey <mutantmonkey@mutantmonkey.in>
#

import json
import uuid
import time
import string
import random

from deps.utils import WebRequest


class RID(object):
    def __init__(self):
        self.Reset()

    def Reset(self):
        self.number = random.randrange(10000, 99999)

    def Next(self):
        self.number = self.number + 1
        return self.number


class YouTubeLoungeSession(object):
        def __init__(self, sid = None, gsession = None):
                self.sid = sid
                self.gsession = gsession
                self.ofs = 0
                self.setAID(5)

        def getOfs(self):
                ofs = self.ofs
                self.ofs = ofs+1
                return ofs

        def setSid(self, sid):
                self.sid = sid

        def setGsession(self, gsession):
                self.gsession = gsession

        def getAID(self):
                return self.aid

        def setAID(self, newAID):
                self.aid = newAID


class YouTubeCmd(object):
    def __init__(self, cmd, **kwargs):
        self.cmd = cmd
        self.params = {}
        if kwargs is not None:
            for key, value in kwargs.items():
                self.params[key] = value
    def create_dict(self, prefix, **kwargs):
        tmp_dict = { "{prefix}_sc".format(prefix=prefix) : self.cmd }
        for key in self.params.keys():
            tmp_dict["{prefix}{name}".format(prefix=prefix, name=key)] = self.params[key]
        if self.cmd == "setPlaylist":
            tmp_dict["{prefix}{name}".format(prefix=prefix, name="listId")] = kwargs["listId"]
        return tmp_dict


class YouTubeRemote(object):
    token = ""
    sid = ""
    gsessionid = ""
    seq = 0
    screen_id = None

    hooks = {}
    def hook_S(self, cmd, params):
        print('S = %s' % json.dumps(params, indent = 4))
        self.session.setGsession(params[0])
    def hook_c(self, cmd, params):
        print('c = %s' % json.dumps(params, indent = 4))
        self.session.setSid(params[0])

    def hook_playlistModified(self,cmd,params):
        print('playlistModified = %s' % json.dumps(params, indent = 4))
        if "listId" in params[0].keys():
            self.listId = params[0]["listId"]
            print('\nhook_playlistModified: got listId: %s\n' % self.listId)

    hooks["playlistModified"] = hook_playlistModified
    hooks["S"] = hook_S
    hooks["c"] = hook_c


    def __init__(self, displayName = "YouTube Remote 🐍"):
        self.screen_id = None
        self.uuid = uuid.uuid4()
        self.sid = ""
        self.aid = -1
        self.rid = RID()
        self.session = YouTubeLoungeSession()
        self.ofs = 0
        self.listId = None
        self.displayName = displayName

    def zx(self):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))

    def generatePairingcode(self):
        return str(uuid.uuid4())

    def checkPairingStatus(self, pairing_code):
        response = WebRequest("https://www.youtube.com/api/lounge/pairing/get_screen").post(body = {'pairing_code' : pairing_code})
        if response.status_code != 200:
            return False
        data = json.loads(response.content)["screen"]
        print('screen = %s\n' % json.dumps(data, indent = 4))
        self.screen_id = data["screenId"]
        self.loungeToken = data["loungeToken"]
        self.expiration = data["expiration"]
        return True

    def waitForPairing(self, pairing_code, timeout = 15):
        timeout = time.time() + timeout
        while time.time() < timeout:
            if self.checkPairingStatus(pairing_code):
                return True
            time.sleep(2)
        raise TimeoutError('Failed to pair with the TV')

    def loadLoungeToken(self, screen_ids):
        text_res = WebRequest("https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch").post(body = {'screen_ids' : screen_ids}).content
        data = json.loads(text_res)
        print('lounge_token_batch = %s\n' % json.dumps(data, indent = 4))
        self.screen_id = data['screens'][0]['screenId']
        self.loungeToken = data['screens'][0]['loungeToken']
        self.expiration = data['screens'][0]["expiration"]
        return self.loungeToken

    def doOpenChannel(self):

        url_str = None
        url_params = {}
        url_data = {}
        url_str = "https://www.youtube.com/api/lounge/bc/bind"
        url_params["device"] = "REMOTE_CONTROL"
        url_params["mdx-version"] = 3
        url_params["ui"] = 1
        url_params["v"] = 2
        url_params["name"] = self.displayName
        url_params['app'] = 'youtube-desktop'
        url_params["loungeIdToken"] = self.loungeToken
        url_params["id"] = str(self.uuid)
        url_params["VER"] = 8
        url_params["CVER"] = 1
        url_params["zx"] = self.zx()
        url_params["RID"] = self.rid.Next()
        url_data["count"] = 0

        res_text = WebRequest(url_str, params = url_params).post(body = url_data).content.decode("utf-8")
        print('url_params = %s' % json.dumps(url_params, indent = 4))

        index = 0
        while index < len(res_text):
            index_prim = res_text.find('\n', index)
            response_len = int(res_text[index : index_prim])
            j = json.loads(res_text[index_prim + 1 : index_prim + 1 + response_len])
            self.processHooks(j)
            index = index_prim + 1 + response_len
        return None

    def processHooks(self, messages):
        for _, data in messages:
            if data[0] in self.hooks:
                self.hooks[data[0]](self = self, cmd = data[0], params = data[1:])

    def doCmd(self, cmds):

        if self.session.sid == None:
            self.doOpenChannel()

        tmp_cmds = cmds
        if isinstance(cmds, YouTubeCmd):
            tmp_cmds = [ cmds ]

        cmd_array = {"count" : len(cmds), "ofs" : self.session.getOfs() }

        for idx, i in enumerate(tmp_cmds):
            prefix = "req{idx}_".format(idx=idx)
            cmd_array.update(i.create_dict(prefix, listId = self.listId))

        url_address = "https://www.youtube.com/api/lounge/bc/bind"
        url_params = {}
        url_params["device"] = "REMOTE_CONTROL"
        url_params["loungeIdToken"] = self.loungeToken
        url_params["id"] = str(self.uuid)
        url_params["VER"] = 8
        url_params["zx"] = self.zx()
        url_params["SID"] = self.session.sid
        url_params["RID"] = self.rid.Next()
        url_params["AID"] = self.session.getAID()
        url_params["gsessionid"] = self.session.gsession
        print('url_params = %s' % json.dumps(url_params, indent = 4))
        print('cmd_array = %s\n' % json.dumps(cmd_array, indent = 4))
        WebRequest(url_address, params = url_params).post(body = cmd_array)