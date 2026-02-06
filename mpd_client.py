"""
Example MPD Client with python-mpd2 and TinyXUI.
by 0Stormy
"""

import asyncio
from threading import Thread
from mpd.asyncio import MPDClient
import xui as xui

client = MPDClient()

async def connect_mpd():
    await client.connect("localhost", 6600)

async def get_current_song():
    song = await client.currentsong()
    status = await client.status()
    state = status.get("state", "stop")
    return {
        "title": song.get("title", "Unknown"),
        "artist": song.get("artist", "Unknown"),
        "album": song.get("album", "Unknown"),
        "state": state
    }

async def play_song():
    playback_button = xui.widget_from_id("playback_toggle")
    status = await client.status()
    if status.get("state") == "pause":
        await client.play()
        playback_button.set_attribute("label", "Pause")
    else:
        await client.pause()
        playback_button.set_attribute("label", "Play")

async def next_song():
    await client.next()

async def previous_song():
    await client.previous()

def async_button(fn):
    def wrapper(*args, **kwargs):
        asyncio.run_coroutine_threadsafe(fn(*args, **kwargs), loop)
    return wrapper

async def wait_for_widget(widget_id):
    while True:
        try:
            return xui.widget_from_id(widget_id)
        except ValueError:
            await asyncio.sleep(0.1)

async def song_updater():
    await connect_mpd()
    song_label = await wait_for_widget("song_label")
    album_label = await wait_for_widget("album_label")
    artist_label = await wait_for_widget("artist_label")

    while True:
        song = await get_current_song()
        song_label.set_label(song["title"])
        album_label.set_label(song["album"])
        artist_label.set_label(song["artist"])
        await asyncio.sleep(1)

def start_asyncio_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(song_updater())
    loop.run_forever()


xui.bind_button("playback_toggle", async_button(play_song))
xui.bind_button("next_button", async_button(next_song))
xui.bind_button("previous_button", async_button(previous_song))

if __name__ == "__main__":
    Thread(target=start_asyncio_loop, daemon=True).start()
    xui.start("mpd.xml")
