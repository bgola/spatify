#!/usr/bin/python

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCRtpCapabilities
from aiortc.rtcicetransport import candidate_from_aioice
from aiortc.contrib.media import MediaPlayer, MediaBlackhole
from aiortc.contrib.signaling import object_to_string
from aioice import Candidate

import asyncio
import json
import logging
import websockets
import uuid

logger = logging.getLogger(__name__)

class WebSocketSignaling:
    def __init__(self, websocket, identifier):
        self._ws = websocket
        self._queue = asyncio.Queue()
        rtc = RTCClient.registry.get(identifier, None)
        if rtc is None:
            rtc = RTCClient(identifier)
        rtc.signaling = self
        self._rtc = rtc

    def __repr__(self):
        return f"WebSocketSignaling({self._ws.remote_address})"

    async def sender(self):
        while True:
            message = await self._queue.get()
            if not isinstance(message, str) and not isinstance(message, bytes):
                message = object_to_string(message)
            logger.info(f"Sending message to {self}: {message}")
            await self._ws.send(message)

    async def receiver(self):
        async for message in self._ws:
            logger.info(f"Got new message from {self}: {message}")
            data_dict = json.loads(message)
            await self._rtc.handle(data_dict)

    async def leave(self):
        await self._ws.close()

    def send(self, message):
        try:
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            logger.error(f"Can't send mesage to {self}, queue is full")


class RTCClient:
    registry = {}

    def __init__(self, identifier):
        self.id = identifier
        self.peer_connection = RTCPeerConnection()
        self.signaling = None
        self.jack_client_name = f"spatify_{self.id}"
        RTCClient.registry[self.id] = self

    def send(self, message):
        if self.signaling is None:
            logger.error(f"Signaling not configure yet for {self.id}")
        self.signaling.send(message)

    async def handle(self, message):
        if message.get("type", None) in ["offer", "answer"]:
            await self.handle_offer(message)
        elif message.get("candidate", None) is not None:
            await self.handle_ice(message)
        elif message.get("type", None) == "bye":
            await self.handle_bye()

    async def handle_bye(self):
        await self.quit()

    async def quit(self):
        await self.peer_connection.close()
        del RTCClient.registry[self.id]

    async def handle_ice(self, message):
        candidate = message["candidate"].get("candidate", None)
        if not candidate:
            return
        ice_candidate = candidate_from_aioice(Candidate.from_sdp(candidate))
        ice_candidate.sdpMid = message["candidate"].get("sdpMid", None)
        ice_candidate.sdpMLineIndex = message["candidate"].get("sdpMLineIndex", None)
        await self.peer_connection.addIceCandidate(ice_candidate)

    async def handle_offer(self, message):
        offer = RTCSessionDescription(**message)
        recorder = MediaBlackhole()
        
        @self.peer_connection.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            state = self.peer_connection.iceConnectionState
            if state == "failed" or state == "closed":
                await self.quit()

            elif self.peer_connection.iceConnectionState == "completed":
                # send osc message
                pass

        @self.peer_connection.on("track")
        def on_track(track):
            if track.kind == "audio":
                player = MediaPlayer(self.jack_client_name, format='jack', options={'channels': '2'})
                self.peer_connection.addTrack(player.audio)
                recorder.addTrack(track)

            @track.on("ended")
            async def on_ended():
                await self.peer_connection.close()
                await recorder.stop()
        
        await self.peer_connection.setRemoteDescription(offer)
        await recorder.start()

        # only send high quality audio
        capabilities = []
        for sender in self.peer_connection.getSenders():
            capabilities = RTCRtpCapabilities(sender.getCapabilities('audio').codecs[:1])

        for track in self.peer_connection.getTransceivers():
            track.setCodecPreferences(capabilities.codecs)
            track._codecs = track._codecs[:1]
        
        answer = await self.peer_connection.createAnswer()
        await self.peer_connection.setLocalDescription(answer)
        self.send(self.peer_connection.localDescription)


async def ws_handler(websocket, path):
    identifier = path.replace("/", "")
    if identifier == '':
        identifier = str(uuid.uuid4())
    wsConnection = WebSocketSignaling(websocket, identifier)

    logger.info(f"New {wsConnection} connected.")

    receiver = asyncio.ensure_future(
        wsConnection.receiver())
    sender = asyncio.ensure_future(
        wsConnection.sender())
   
    wsConnection.send(json.dumps({'id': identifier}))

    try:
        done, pending = await asyncio.wait(
            [receiver, sender],
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        for task in pending:
            task.cancel()
        for task in done:
            # trigger exceptions, if any
            task.result()
    except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
            asyncio.exceptions.CancelledError):
        # Connection ended
        pass

    await wsConnection.leave()
    logger.info(f"{wsConnection} left")
