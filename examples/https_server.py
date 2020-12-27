from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl


httpd = HTTPServer(('0.0.0.0', 4443),  SimpleHTTPRequestHandler)

httpd.socket = ssl.wrap_socket (httpd.socket, 
                keyfile="localhost.key", 
                certfile='localhost.crt', server_side=True)

httpd.serve_forever()
