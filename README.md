# Audio spatialization over WebRTC

Spatify provides a framework for building multichannel installations using WebRTC.

With Spatify each client becomes a JACK client on the host machine, any audio
sent to that client's ports will be streamed over WebRTC to the client.

The original idea behind this project was to use multiple smartphones as individual
speakers in installations or performances.


# Installing 

You will need Python >= 3.7 together with websockets and aiortc python libraries.

```
$ git clone git@github.com:bgola/spatify.git
$ cd spatify/
$ pip install websockets aiortc
$ python setup.py install
```

# Running

```
$ spatify -h
usage: spatify [-h] [--cert CERT] [--key KEY] [--host HOST] [--port PORT] [--verbose] [--quiet]

Spatify server

optional arguments:
  -h, --help     show this help message and exit
  --cert CERT    SSL certificate path (for WSS)
  --key KEY      SSL key path (for WSS)
  --host HOST    Host for WebSocket server (default: 0.0.0.0)
  --port PORT    Port for WebSocket server (default: 8765)
  --verbose, -v
  --quiet, -q
```

# Checking the example

In the examples/ folder there is an HTML/JavaScript example for using WebSockets as
signaling mechanism and establishing the WebRTC streams. Notice that the example
uses a self-signed SSL certificafe because you can't start the WebRTC stream over an 
unsecured connection (you need HTTPS). Your browser might complain that the certificate is
not to be trusted. Also, some browsers might fail to initiate the secure WebSocket
connection for the same reason. This example was tested on chromium and on chrome for android.
To fix this in a real case you need a proper certificate (by using letsencrypt for example).

You can use the python script to serve the examples/ folder via HTTPS (remember to edit the HTML example file
to use your IP address, otherwise it will only work for localhost):

```
$ cd examples/
$ python https_server.py
```

and on another terminal run spatify:

```
$ cd examples/
$ spatify --crt localhost.cert --key localhost.key
2020-12-12 15:25,509 Listening for websocket signaling on 0.0.0.0:8765
```

Now open `https://<ip_addr_of_the_host>/websockets.html` and click on "Start connection".

You should see a new JACK client called `spatify_*` registered (if you use QJackCtl or 
Carla it should appear in the routing). Route any audio to this new client and it should play
on the browser you used.
