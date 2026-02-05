"""
Example MPD Client with python-mpd2 and TinyXUI.
by 0Stormy
"""

import xui
from mpd import MPDClient

client = MPDClient()
client.connect("localhost", 6600)

def play_song():
    if client.status()["state"] == "pause":
        client.play()
    else:
        client.pause()

def next_song():
    client.next()

def previous_song():
    client.previous()

xui.bind_button("playback_toggle", play_song)
xui.bind_button("next_button", next_song)
xui.bind_button("previous_button", previous_song)

if __name__ == "__main__":
    xui.start("mpd.xml")
