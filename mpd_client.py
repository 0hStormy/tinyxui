import asyncio
from mpd import MPDClient
import mpd.base as MPDBase
import xui
import threading
import datetime


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
        "file": song["file"],
    }


def format_time(seconds: int) -> str:
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02}:{secs:02}"
    else:
        return f"{minutes}:{secs:02}"


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
            status = client.status()
            current_file = song["file"]
            elapsed = int(status["time"].split(":")[0])
            total = int(status["time"].split(":")[1])

            progress = (elapsed / total) * 100
            xui.set_attribute("song_progress", "progress", progress)
            xui.set_data("elapsed_time", format_time(elapsed))
            xui.set_data("total_time", format_time(total))


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
