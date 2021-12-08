#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Released under the MIT License https://opensource.org/licenses/MIT
# Copyright (c) Sami Alaoui Kendil (thedroidgeek)
#

import os
import re
import sys
import json
import time
import socket
import struct
import requests
import threading
import traceback
import urllib.parse

class Config:

    data = {}
    file_path = None

    # loads config from storage
    @staticmethod
    def load():
        # try reading the config file
        try:
            f = open(Config.file_path, 'r')
            Config.data = json.load(f)
            f.close()
        except:
            pass
        # set default values, for undefined settings
        if Config.get('RemoteDisplayName') == None:
            Config.set('RemoteDisplayName', '🌈 Google Assistant')
        if Config.get('TvLanHost') == None:
            Config.set('TvLanHost', 'tizen')
        if Config.get('ReadYtTokenFromDial') == None:
            Config.set('ReadYtTokenFromDial', False)

    cfg_write_mtx = threading.Lock()
    # persists the current config to storage
    @staticmethod
    def commit():
        with Config.cfg_write_mtx:
            f = open(Config.file_path, 'w')
            f.write(json.dumps(Config.data, indent = 4))
            f.close()

    # gets a config setting
    @staticmethod
    def get(key):
        if not key in Config.data.keys():
            return None
        return Config.data[key]

    # sets a config setting
    @staticmethod
    def set(key, val):
        Config.data[key] = val
        Config.commit()

    # clears a config setting
    @staticmethod
    def clear(key):
        if Config.get(key) == None:
            Config.data.pop(key)
            Config.commit()

    def __init__(self, config_file):
        Config.file_path = ((os.path.dirname(os.path.abspath(sys.argv[0])) + '/') if not os.path.isabs(config_file) else '') + config_file
        Config.load()
        Config.commit()

class WebRequest:

    def __init__(self, url, params = None):
        self.session = requests.Session()
        self.url_address = url + (('?' + urllib.parse.urlencode(params)) if params != None else '')
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.27 Safari/537.36'})

    def get(self, timeout = 10):
        try:
            return self.session.get(self.url_address, proxies = urllib.request.getproxies(), timeout = timeout)
        except:
            traceback.print_exc()
            return None

    def post(self, body = None, timeout = 10):
        try:
            return self.session.post(self.url_address, data = body, proxies = urllib.request.getproxies(), timeout = timeout)
        except:
            traceback.print_exc()
            return None

class TvUtil:

    @staticmethod
    def pairYt(pairingCode):
        tvDialYouTubeEndpoint = 'http://%s:8080/ws/app/YouTube' % Config.get('TvLanHost')
        timeout = time.time() + 40
        tvRequest = WebRequest(tvDialYouTubeEndpoint)
        while time.time() < timeout:
            response = tvRequest.get(timeout = 3)
            if response != None and response.status_code == 200: # check if TV is reachable
                ytStatus = tvRequest.post(body = {"pairingCode" : pairingCode, "theme" : "cl"}, timeout = 30)
                if ytStatus != None:
                    if ytStatus.status_code == 401:
                        raise PermissionError("The YouTube pairing request was denied by the TV")
                    if ytStatus.status_code == 201 or ytStatus.status_code == 200:
                        return True
                raise Exception("Got an unexpected response from the TV")
            time.sleep(0.5)
        raise TimeoutError('Failed to send pairing request to the TV')

    @staticmethod
    def getYtScreenId():
        tvDialYouTubeEndpoint = 'http://%s:8080/ws/app/YouTube' % Config.get('TvLanHost')
        timeout = time.time() + 40
        tvRequest = WebRequest(tvDialYouTubeEndpoint)
        while time.time() < timeout:
            ytStatus = tvRequest.get(timeout = 3)
            if ytStatus != None:
                match = re.findall(r'<screenId>(.*)</screenId>', ytStatus.content.decode("utf-8"))
                if len(match) != 0:
                    return match[0]
            tvRequest.post(timeout = 3)
            time.sleep(0.5)
        raise TimeoutError('Failed to obtain screen ID from TV')

    @staticmethod
    def getYtLoungeToken():
        tvDialYouTubeEndpoint = 'http://%s:8080/ws/app/YouTube' % Config.get('TvLanHost')
        timeout = time.time() + 40
        tvRequest = WebRequest(tvDialYouTubeEndpoint)
        while time.time() < timeout:
            ytStatus = tvRequest.get(timeout = 3)
            if ytStatus != None:
                match = re.findall(r'<loungeToken>(.*)</loungeToken>', ytStatus.content.decode("utf-8"))
                if len(match) != 0:
                    return match[0]
            tvRequest.post(timeout = 3)
            time.sleep(0.5)
        raise TimeoutError('Failed to obtain lounge token from TV')

    @staticmethod
    def WoL():

        if Config.get('MacAddress') == None:
            try:
                import getmac
                Config.set('MacAddress', getmac.get_mac_address(hostname=Config.get('TvLanHost')).replace(':', '').upper())
            except:
                traceback.print_exc()
                return False

        # Pad the synchronization stream.
        data = ('F' * 12) + (Config.get('MacAddress') * 16)

        # Split up the hex values and pack.
        send_data = b''
        for i in range(0, len(data), 2):
            send_data = b''.join([send_data, struct.pack('B', int(data[i: i + 2], 16))])

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(10):
            sock.sendto(send_data, ('<broadcast>', 9))
        return True
