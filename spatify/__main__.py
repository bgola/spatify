import argparse
import asyncio
import ssl
import websockets
import logging

from spatify.rtc import ws_handler

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Spatify server"
    )
    parser.add_argument("--cert", help="SSL certificate path (for WSS)")
    parser.add_argument("--key", help="SSL key path (for WSS)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for WebSocket server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Port for WebSocket server (default: 8765)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--quiet", "-q", action="count")
    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s %(message)s")

    if args.cert:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(args.cert, args.key)
    else:
        ssl_context = None
    
    start_server = websockets.serve(
        ws_handler, args.host, args.port, ssl=ssl_context
    )

    logger.info(f"Listening for websocket signaling on {args.host}:{args.port}")

    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Quitting.")


if __name__ == "__main__":
    main()
