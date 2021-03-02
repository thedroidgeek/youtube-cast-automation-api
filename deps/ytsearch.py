#!/usr/bin/python3

#
# Based on youtube-search
# https://github.com/joetats/youtube_search
#
# Released under the MIT License https://opensource.org/licenses/MIT
# Copyright (c) Joe Tatusko <tatuskojc@gmail.com>
#

import time
import json
import urllib.parse

from deps.utils import WebRequest

class YoutubeSearch:
    def __init__(self, search_terms: str, max_results = None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self.search()

    def search(self):
        encoded_search = urllib.parse.quote(self.search_terms)
        BASE_URL = "https://www.youtube.com"
        url = f"{BASE_URL}/results?search_query={encoded_search}&gl=US"
        response = WebRequest(url).get().content.decode("utf-8")
        while "ytInitialData" not in response:
            response = WebRequest(url).get().content.decode("utf-8")
            time.sleep(1)
        results = self.parse_html(response)
        return results

    def parse_vid_data(self, data):
        res = {}
        video_data = data.get("videoRenderer", {})
        res["id"] = video_data.get("videoId", None)
        res["thumbnails"] = [thumb.get("url", None) for thumb in video_data.get("thumbnail", {}).get("thumbnails", [{}]) ]
        res["title"] = video_data.get("title", {}).get("runs", [[{}]])[0].get("text", None)
        res["long_desc"] = video_data.get("descriptionSnippet", {}).get("runs", [{}])[0].get("text", None)
        res["channel"] = video_data.get("longBylineText", {}).get("runs", [[{}]])[0].get("text", None)
        res["duration"] = video_data.get("lengthText", {}).get("simpleText", 0)
        res["views"] = str(video_data.get("viewCountText", {}).get("simpleText", 0)).split()[0]
        res["url_suffix"] = video_data.get("navigationEndpoint", {}).get("commandMetadata", {}).get("webCommandMetadata", {}).get("url", None)
        return res

    def parse_html(self, response):
        results = []
        start = (
            response.index("ytInitialData")
            + len("ytInitialData")
            + 3
        )
        end = response.index("};", start) + 1
        json_str = response[start:end]
        data = json.loads(json_str)

        videos = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"][
            "sectionListRenderer"
        ]["contents"][0]["itemSectionRenderer"]["contents"]

        first_shelf = True
        count = self.max_results
        for video in videos:
            if count <= 0:
                break
            if "videoRenderer" in video.keys():
                results.append(self.parse_vid_data(video))
                count -= 1
            if "shelfRenderer" in video.keys() and first_shelf: # 'Latest from X'
                first_shelf = False
                num_latest = 2 # only grab 2
                for latest_vid in video["shelfRenderer"]["content"]["verticalListRenderer"]["items"]:
                    if count <= 0:
                        break
                    if "videoRenderer" in latest_vid.keys() and num_latest > 0:
                        results.append(self.parse_vid_data(latest_vid))
                        count -= 1
                        num_latest -= 1
        return results

    def as_dict(self):
        return self.videos

    def as_json(self):
        return json.dumps({"videos": self.videos})

    def count(self):
        return len(self.videos)

    def as_csv_ids(self):
        videoIdList = ''
        for i in range(len(self.videos)):
            videoIdList += self.videos[i]['id'] + ','
        return videoIdList[:-1]