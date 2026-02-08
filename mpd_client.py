import asyncio
from mpd import MPDClient
import mpd.base as MPDBase
import xui
import threading


last_song_file = None


client = MPDClient()
client.connect("localhost", 6600)


def get_current_song():
    song = client.currentsong()
    status = client.status()
    state = status.get("state", "stop")
    return {
        "title": song.get("title", "Unknown"),
        "artist": song.get("artist", "Unknown"),
        "album": song.get("album", "Unknown"),
        "state": state,
        "file": song["file"]
    }


def play_song():
    status = client.status()
    if status.get("state") == "pause":
        client.play()
    else:
        client.pause()


def next_song():
    try:
        client.next()
    except MPDBase.CommandError:
        return


def previous_song():
    client.previous()


async def update_loop():
    global last_song_file
    while True:
        try:
            song = get_current_song()
            current_file = song["file"]

            if current_file != last_song_file:
                # Song has changed
                last_song_file = current_file

                # Update labels
                xui.set_data("song_label", song["title"])
                xui.set_data("artist_label", song["artist"])
                xui.set_data("album_label", song["album"])

                # Update album art
                try:
                    cover_art = client.albumart(song["file"])
                    with open("out.png", "wb") as f:
                        f.write(cover_art["binary"])
                    xui.refresh_image("cover_art")
                except KeyError:
                    pass
                except MPDBase.CommandError:
                    pass
                    with open("out.png", "wb") as f:
                        f.write(b"")
                    xui.refresh_image("cover_art")

        except Exception:
            # GUI not ready yet, or network hiccup
            pass

        await asyncio.sleep(0.1)


# Run XUI in a separate thread
def run_xui():
    xui.start("mpd.txm")


# Bind buttons
xui.bind_widget("playback_button", play_song)
xui.bind_widget("next_button", next_song)
xui.bind_widget("previous_button", previous_song)


if __name__ == "__main__":
    threading.Thread(target=run_xui, daemon=True).start()
    asyncio.run(update_loop())
