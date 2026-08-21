import socket
import os
import threading
from datetime import datetime
import html


# ========================================
# SERVER CONFIGURATION
# ========================================

HOST = "127.0.0.1"

# You can change the port here
PORT = 8080

BASE_DIR = os.path.dirname(__file__)

WEB_ROOT = os.path.join(
    BASE_DIR,
    "www"
)

LOG_FILE = os.path.join(
    BASE_DIR,
    "logs",
    "server.log"
)


# ========================================
# INPUT VALIDATION
# ========================================

def validate_form_data(form_data):

    # Limit submitted data to 1024 characters
    if len(form_data) > 1024:
        return False

    return True


# ========================================
# SECURITY HEADERS
# ========================================

def security_headers():

    return (
        "X-Content-Type-Options: nosniff\r\n"
        "X-Frame-Options: DENY\r\n"
        "Referrer-Policy: strict-origin-when-cross-origin\r\n"
        "Content-Security-Policy: "
        "default-src 'self'; "
        "style-src 'self'; "
        "img-src 'self';\r\n"
    )


# ========================================
# REQUEST LOGGING
# ========================================

def log_request(
    client_address,
    method,
    path,
    status_code
):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    client_ip = client_address[0]

    log_entry = (
        f"{timestamp} | "
        f"{client_ip} | "
        f"{method} | "
        f"{path} | "
        f"{status_code}\n"
    )

    with open(
        LOG_FILE,
        "a"
    ) as log_file:

        log_file.write(
            log_entry
        )


# ========================================
# HANDLE CLIENT
# ========================================

def handle_client(
    client_socket,
    client_address
):

    print(
        f"Connection received from "
        f"{client_address}"
    )

    try:

        # =================================
        # RECEIVE HTTP REQUEST
        # =================================

        request = client_socket.recv(
            4096
        ).decode(
            "utf-8",
            errors="ignore"
        )

        print("Request received:")
        print(request)


        # =================================
        # PARSE REQUEST LINE
        # =================================

        request_line = request.split(
            "\r\n"
        )[0]

        parts = request_line.split()


        if len(parts) < 2:

            client_socket.close()

            return


        method = parts[0]

        path = parts[1]


        print(
            f"Method: {method}"
        )

        print(
            f"Path: {path}"
        )


        # =================================
        # PARSE HOST HEADER
        # =================================

        host = "Unknown"


        for header in request.split(
            "\r\n"
        ):

            if header.lower().startswith(
                "host:"
            ):

                host = header.split(
                    ":",
                    1
                )[1].strip()

                break


        print(
            f"Host: {host}"
        )


        # =================================
        # 405 METHOD NOT ALLOWED
        # =================================

        if method not in [
            "GET",
            "HEAD",
            "POST"
        ]:

            status_code = 405

            body = b"""
            <html>

            <head>
                <title>405 Method Not Allowed</title>
            </head>

            <body>

                <h1>405 Method Not Allowed</h1>

                <p>
                    The requested HTTP method
                    is not supported.
                </p>

            </body>

            </html>
            """


            response_headers = (
                "HTTP/1.1 405 Method Not Allowed\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(body)}\r\n"
                + security_headers()
                + "Allow: GET, HEAD, POST\r\n"
                + "Connection: close\r\n"
                + "\r\n"
            )


            response = (
                response_headers.encode()
                + body
            )


            client_socket.sendall(
                response
            )


            log_request(
                client_address,
                method,
                path,
                status_code
            )

            return


        # =================================
        # POST REQUEST
        # =================================

        if (
            method == "POST"
            and path == "/submit"
        ):

            body_data = request.split(
                "\r\n\r\n",
                1
            )


            if len(body_data) == 2:

                form_data = body_data[1]

            else:

                form_data = ""


            print(
                f"POST data received: "
                f"{form_data}"
            )


            # =================================
            # INPUT VALIDATION
            # =================================

            if not validate_form_data(
                form_data
            ):

                status_code = 400

                body = b"""
                <html>

                <head>
                    <title>400 Bad Request</title>
                </head>

                <body>

                    <h1>400 Bad Request</h1>

                    <p>
                        The submitted data is
                        invalid or too large.
                    </p>

                </body>

                </html>
                """


                response_headers = (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: text/html\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    + security_headers()
                    + "Connection: close\r\n"
                    + "\r\n"
                )


                response = (
                    response_headers.encode()
                    + body
                )


                client_socket.sendall(
                    response
                )


                log_request(
                    client_address,
                    method,
                    path,
                    status_code
                )

                return


            # =================================
            # OUTPUT ENCODING
            # =================================

            safe_form_data = html.escape(
                form_data
            )


            # =================================
            # POST RESPONSE PAGE
            # =================================

            status_code = 200


            response_body = f"""
            <!DOCTYPE html>

            <html>

            <head>

                <meta charset="UTF-8">

                <meta
                    name="viewport"
                    content="width=device-width,
                    initial-scale=1.0"
                >

                <title>Form Submitted</title>

                <link
                    rel="stylesheet"
                    href="/style.css"
                >

            </head>

            <body>

                <header>

                    <h1>
                        Form Submitted Successfully
                    </h1>

                </header>

                <main>

                    <h2>Thank You!</h2>

                    <p>
                        Your POST request was
                        received by MiniHTTP.
                    </p>

                    <p>
                        <strong>
                            Submitted data:
                        </strong>
                    </p>

                    <pre>{safe_form_data}</pre>

                    <a href="/form.html">
                        Back to Form
                    </a>

                </main>

            </body>

            </html>
            """


            body = response_body.encode(
                "utf-8"
            )


            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; "
                "charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                + security_headers()
                + "Connection: close\r\n"
                + "\r\n"
            )


            response = (
                response_headers.encode()
                + body
            )


            client_socket.sendall(
                response
            )


            log_request(
                client_address,
                method,
                path,
                status_code
            )

            return


        # =================================
        # ROOT URL
        # =================================

        if path == "/":

            path = "/index.html"


        # =================================
        # CREATE FILE PATH
        # =================================

        file_path = os.path.join(
            WEB_ROOT,
            path.lstrip("/")
        )


        # =================================
        # PATH TRAVERSAL PROTECTION
        # =================================

        real_web_root = os.path.realpath(
            WEB_ROOT
        )

        real_file_path = os.path.realpath(
            file_path
        )


        if not real_file_path.startswith(
            real_web_root + os.sep
        ):

            status_code = 404

            body = b"""
            <html>

            <head>
                <title>404 Not Found</title>
            </head>

            <body>

                <h1>404 Not Found</h1>

                <p>
                    The requested resource
                    could not be found.
                </p>

            </body>

            </html>
            """


            response_headers = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(body)}\r\n"
                + security_headers()
                + "Connection: close\r\n"
                + "\r\n"
            )


            response = (
                response_headers.encode()
                + body
            )


            client_socket.sendall(
                response
            )


            log_request(
                client_address,
                method,
                path,
                status_code
            )

            return


        # =================================
        # CHECK REQUESTED FILE
        # =================================

        if os.path.isfile(
            real_file_path
        ):

            status_code = 200


            with open(
                real_file_path,
                "rb"
            ) as file:

                body = file.read()


            # =================================
            # MIME TYPES
            # =================================

            if real_file_path.endswith(
                ".html"
            ):

                content_type = "text/html"


            elif real_file_path.endswith(
                ".css"
            ):

                content_type = "text/css"


            elif real_file_path.endswith(
                ".png"
            ):

                content_type = "image/png"


            elif (
                real_file_path.endswith(".jpg")
                or
                real_file_path.endswith(".jpeg")
            ):

                content_type = "image/jpeg"


            else:

                content_type = (
                    "application/octet-stream"
                )


            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: "
                f"{content_type}\r\n"
                f"Content-Length: "
                f"{len(body)}\r\n"
                + security_headers()
                + "Connection: close\r\n"
                + "\r\n"
            )


            response = (
                response_headers.encode()
                + body
            )


        # =================================
        # 404 NOT FOUND
        # =================================

        else:

            status_code = 404


            error_page = os.path.join(
                WEB_ROOT,
                "404.html"
            )


            if os.path.isfile(
                error_page
            ):

                with open(
                    error_page,
                    "rb"
                ) as file:

                    body = file.read()

            else:

                body = b"""
                <html>

                <body>

                    <h1>404 Not Found</h1>

                    <p>
                        The requested resource
                        could not be found.
                    </p>

                </body>

                </html>
                """


            response_headers = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(body)}\r\n"
                + security_headers()
                + "Connection: close\r\n"
                + "\r\n"
            )


            response = (
                response_headers.encode()
                + body
            )


        # =================================
        # HEAD REQUEST
        # =================================

        if method == "HEAD":

            client_socket.sendall(
                response_headers.encode()
            )

        else:

            client_socket.sendall(
                response
            )


        # =================================
        # LOG REQUEST
        # =================================

        log_request(
            client_address,
            method,
            path,
            status_code
        )


    except Exception as error:

        print(
            f"Error handling client: "
            f"{error}"
        )


    finally:

        client_socket.close()


# ========================================
# CREATE SERVER SOCKET
# ========================================

server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)


server_socket.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)


server_socket.bind(
    (HOST, PORT)
)


server_socket.listen(
    10
)


print(
    f"MiniHTTP server running at "
    f"http://{HOST}:{PORT}"
)


# ========================================
# ACCEPT CLIENT CONNECTIONS
# ========================================

while True:

    client_socket, client_address = (
        server_socket.accept()
    )


    client_thread = threading.Thread(
        target=handle_client,
        args=(
            client_socket,
            client_address
        )
    )


    client_thread.start()


    print(
        f"Active threads: "
        f"{threading.active_count() - 1}"
    )