from random import randrange

from . import AudioTrack


class Player:
    def __init__(self, bot, guild_id: int):
        self.bot = bot

        self.shard_id = bot.get_guild(guild_id).shard_id
        self.guild_id = str(guild_id)

        self.is_playing = lambda: self.current is not None
        self.paused = False

        self.position = 0
        self.position_timestamp = 0
        self.volume = 100

        self.queue = []
        self.current = None

        self.shuffle = False
        self.repeat = False

    @property
    def connected_channel(self):
        g = self.bot.get_guild(int(self.guild_id))
        if not g or not g.voice_client:
            return None
        return g.voice_client.channel

    async def add(self, requester, track, play=False):
        self.queue.append(await AudioTrack().build(track, requester))

        if play and not self.is_playing():
            await self.play()

    async def play(self):
        if self.current is not None or not self.queue:
            return

        if self.shuffle:
            track = self.queue.pop(randrange(len(self.queue)))
        else:
            track = self.queue.pop(0)

        await self.bot.lavalink.ws.send(op='play', guildId=self.guild_id, track=track.track)
        self.current = track

    async def stop(self):
        await self.bot.lavalink.ws.send(op='stop', guildId=self.guild_id)
        self.current = None

    async def skip(self):
        await self.play()

    async def set_paused(self, pause: bool):
        await self.bot.lavalink.ws.send(op='pause', guildId=self.guild_id, pause=pause)
        self.paused = pause

    async def set_volume(self, vol: int):
        if isinstance(vol, int):
            self.volume = max(min(vol, 150), 0)

            await self.bot.lavalink.ws.send(op='volume', guildId=self.guild_id, volume=self.volume)
            return self.volume

    async def seek(self, pos: int):
        await self.bot.lavalink.ws.send(op='seek', guildId=self.guild_id, position=pos)

    async def on_track_end(self, data):
        self.position = 0
        self.paused = False
        self.current = None

        if data.get('reason') == 'FINISHED':
            await self.play()