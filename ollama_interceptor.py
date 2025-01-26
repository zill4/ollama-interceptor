import sys
import socket
import threading
from datetime import datetime
from urllib.parse import urlparse

# Configuration
PROXY_PORT = 11435
TARGET_PORT = 11434
LOG_FILE = "ollama_traffic.log"
BUFFER_SIZE = 4096

class HTTPParser:
    @staticmethod
    def parse_request(data):
        """Parse HTTP request into components"""
        try:
            headers_end = data.find(b'\r\n\r\n')
            if headers_end == -1:
                return None
                
            header_part = data[:headers_end].decode('utf-8')
            body = data[headers_end+4:]
            
            # Parse request line
            lines = header_part.split('\r\n')
            method, path, version = lines[0].split(' ', 2)
            
            # Parse headers
            headers = {}
            for line in lines[1:]:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    headers[key.lower()] = value
                    
            return {
                'type': 'request',
                'method': method,
                'path': path,
                'version': version,
                'headers': headers,
                'body': body.decode('utf-8', errors='replace')
            }
        except Exception as e:
            return None

    @staticmethod
    def parse_response(data):
        """Parse HTTP response into components"""
        try:
            headers_end = data.find(b'\r\n\r\n')
            if headers_end == -1:
                return None
                
            header_part = data[:headers_end].decode('utf-8')
            body = data[headers_end+4:]
            
            # Parse status line
            lines = header_part.split('\r\n')
            version, status, reason = lines[0].split(' ', 2)
            
            # Parse headers
            headers = {}
            for line in lines[1:]:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    headers[key.lower()] = value
                    
            return {
                'type': 'response',
                'version': version,
                'status': int(status),
                'reason': reason,
                'headers': headers,
                'body': body.decode('utf-8', errors='replace')
            }
        except Exception as e:
            return None

def format_log_entry(parsed, direction):
    """Format parsed HTTP data into human-readable log entry"""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")
    entry = [f"\n{direction} {timestamp}"]
    
    if parsed['type'] == 'request':
        entry.append(f"{parsed['method']} {parsed['path']} {parsed['version']}")
        entry.append("Headers:")
        for k, v in parsed['headers'].items():
            entry.append(f"  {k}: {v}")
        if parsed['body']:
            entry.append("\nBody:")
            entry.append(parsed['body'])
            
    elif parsed['type'] == 'response':
        entry.append(f"{parsed['version']} {parsed['status']} {parsed['reason']}")
        entry.append("Headers:")
        for k, v in parsed['headers'].items():
            entry.append(f"  {k}: {v}")
        if parsed['body']:
            entry.append("\nBody:")
            entry.append(parsed['body'])
    
    entry.append("-" * 60)
    return "\n".join(entry)

def log_http(parsed, direction):
    """Log parsed HTTP traffic"""
    log_entry = format_log_entry(parsed, direction)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    print(log_entry)

def handle_client(client_sock):
    try:
        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_sock.connect(("localhost", TARGET_PORT))
        
        # Set socket timeouts (30 seconds)
        client_sock.settimeout(30)
        target_sock.settimeout(30)
        
        def forward(src, dst, direction):
            buffer = b''
            while True:
                try:
                    data = src.recv(BUFFER_SIZE)
                    if not data:
                        src.shutdown(socket.SHUT_RDWR)
                        break
                        
                    # Add keep-alive header if missing
                    if b'connection: keep-alive' not in data.lower():
                        data = data.replace(
                            b'\r\n\r\n', 
                            b'\r\nConnection: keep-alive\r\n\r\n', 
                            1
                        )
                    
                    dst.sendall(data)  # Use sendall for complete transmission
                    
                    # Accumulate for parsing
                    buffer += data
                    
                    while True:  # Process multiple messages in buffer
                        parsed = None
                        if direction == "CLIENT -> SERVER":
                            parsed = HTTPParser.parse_request(buffer)
                        else:
                            parsed = HTTPParser.parse_response(buffer)
                        
                        if parsed:
                            # Log structured data
                            log_http(parsed, direction)
                            
                            # Remove processed data from buffer
                            message_end = buffer.find(b'\r\n\r\n') + 4
                            if 'content-length' in parsed['headers']:
                                content_length = int(parsed['headers']['content-length'])
                                message_end += content_length
                            buffer = buffer[message_end:]
                        else:
                            # Log partial data if buffer exceeds limit
                            if len(buffer) > 4096:  # 4KB max buffer
                                log_data(direction, buffer)
                                buffer = b''
                            break
                            
                except Exception as e:
                    print(f"Forward error: {str(e)}")
                    break

        # Start bidirectional forwarding
        client_to_server = threading.Thread(
            target=forward, 
            args=(client_sock, target_sock, "CLIENT -> SERVER")
        )
        server_to_client = threading.Thread(
            target=forward,
            args=(target_sock, client_sock, "SERVER -> CLIENT")
        )
        
        client_to_server.start()
        server_to_client.start()
        
        client_to_server.join()
        server_to_client.join()

    except Exception as e:
        print(f"Connection error: {str(e)}")
    finally:
        try:
            client_sock.close()
        except:
            pass
        try:
            target_sock.close()
        except:
            pass

def log_data(direction, data):
    """Fallback raw data logger"""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")
    hexdump = " ".join(f"{b:02x}" for b in data)
    ascii_view = "".join(chr(b) if 32 <= b <= 126 else '.' for b in data)
    
    log_entry = (
        f"\n{direction} RAW {len(data)} bytes {timestamp}\n"
        f"HEX: {hexdump}\n"
        f"ASCII: {ascii_view}\n"
        f"{'-'*60}\n"
    )
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(log_entry)

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", PROXY_PORT))
    server.listen(5)
    print(f"Interceptor running on port {PROXY_PORT}...")
    
    while True:
        client_sock, addr = server.accept()
        print(f"New connection from {addr[0]}:{addr[1]}")
        handler = threading.Thread(target=handle_client, args=(client_sock,))
        handler.start()

if __name__ == "__main__":
    start_proxy() 