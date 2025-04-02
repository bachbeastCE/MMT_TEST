import socket
import threading
import json
import sys

class USER:
    def __init__(self, TRACKER_IP, TRACKER_PORT):
        self.TRACKER_IP = TRACKER_IP
        self.TRACKER_PORT = TRACKER_PORT
        self.name = input("ENTER YOUR NAME: ")
        self.ip = input("ENTER YOUR IP (Nhấn Enter để dùng mặc định 127.0.0.1): ") or "127.0.0.1"
        self.port = input("ENTER YOUR PORT: ")



        #ATTRIBUTE
        self.session_id = None
        self.response_list = None
        self.status_login = None
        self.username_login = None
        self.all_channelist = None
        self.tracker_socket = None
        self.isChatRunning = False

    
        self.connect_to_tracker()
        self.menu()

# ========== TRACKER TASK ==========

    def connect_to_tracker(self):
        """Kết nối và đăng ký với Tracker."""
        try:
            self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tracker_socket.connect((self.TRACKER_IP, self.TRACKER_PORT))

            request = json.dumps({
                "command": "CONNECT",
                "name": self.name,
                "ip": self.ip,
                "port": self.port
            })
            self.tracker_socket.sendall(request.encode('utf-8'))

            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            print(f"[INFO] Tracker response: {response_data.get('message', 'Không có phản hồi')}")
        except Exception as e:
            print(f"[ERROR] Không thể kết nối đến Tracker: {e}")
            self.tracker_socket = None

    def get_peer_list(self):
        """Lấy danh sách peer từ Tracker."""
        if self.tracker_socket is None:
            print("[ERROR] Chưa kết nối đến tracker.")
            return []

        try:
            request = json.dumps({"command": "GET_LIST", "name": self.name})
            self.tracker_socket.sendall(request.encode('utf-8'))

            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            if response_data.get("status") == "OK":
                peer_list = response_data.get("peer_list", [])
                print("[INFO] Danh sách peer:")
                for peer in peer_list:
                    print(f" - {peer['name']} ({peer['ip']}:{peer['port']})")
                return peer_list
            else:
                print(f"[ERROR] Tracker trả về lỗi: {response_data.get('message', 'Không có thông báo lỗi')}")
                return []

        except Exception as e:
            print(f"[ERROR] Lỗi khi lấy danh sách peer: {e}")
            return []

    def leave_tracker(self):
        """Gửi yêu cầu rời khỏi tracker."""
        if self.tracker_socket is None:
            print("[ERROR] Chưa kết nối đến tracker.")
            return

        try:
            request = json.dumps({
                "command": "LEAVE",
                "name": self.name,
                "ip": self.ip,
                "port": self.port
            })
            self.tracker_socket.sendall(request.encode('utf-8'))

            response = self.tracker_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)
            print(f"[INFO] Tracker response: {response_data.get('message', 'Không có phản hồi')}")

        except Exception as e:
            print(f"[ERROR] Lỗi khi rời khỏi tracker: {e}")

        finally:
            self.tracker_socket.close()
            self.tracker_socket = None

    def send_to_tracker(self, message):
        try:
            parts = message.split()
            command = parts[0].lower()
            data = {"command": command}

            if command == "login":
                if len(parts) < 3:
                    return "[ERROR] Cần nhập username và password!"
                data["username"] = parts[1]
                data["password"] = parts[2]
            elif command == "register":
                if len(parts) < 4:
                    return "[ERROR] Cần nhập username, password và email!"
                data["username"] = parts[1]
                data["password"] = parts[2]
                data["email"] = parts[3]
            elif command == "visitor":
                if len(parts) < 2:
                    return "[ERROR] Cần nhập tên visitor!"
                data["name"] = parts[1]
            elif command == "logout":
                data["session_id"] = self.session_id
            elif command == "create_channel":
                data["host"] = parts[1]
                data["channel_name"] = parts[2]
            elif command == "join_channel":
                data["username"] = parts[1]
                data["channel_name"] = parts[2]
            elif command == "get_user_channels":
                data["username"] = parts[1]
            elif command == "send_message":
                data["username"] = parts[1]
                data["channel_name"] = parts[2]
                data["message"] = parts[3]
            elif command == "get_channel_info":
                data["channel_name"] = parts[1]
            elif command == "get_all_channels":
                pass
            elif command == "delete_channel":
                data["username"] = parts[1]
                data["channel_name"] = parts[2]
            elif command == "data":
                if len(parts) < 4:
                    return "[ERROR] Cần nhập IP, Port và tin nhắn!"
                data["target_ip"] = parts[1]
                data["target_port"] = parts[2]
                data["message"] = " ".join(parts[3:])

            json_message = json.dumps(data)
            self.tracker_socket.sendall(json_message.encode('utf-8'))

            response = self.tracker_socket.recv(1024)
            if not response:
                return "[ERROR] Không nhận được phản hồi từ server."

            response_data = response.decode('utf-8')
            if command == "get_user_channels":
                response_list = response_data
            elif command == "get_all_channels":
                all_channelist = response_data
            #print(response_list)
            #print(type(response_list))
            print(f"[DEBUG] Phản hồi từ Tracker: {response_data}")
            #print(type(response_data))
            #print(f"[DEBUG] Dữ liệu nhận được từ server: {response_data}")
            
            try:
                response_dict = json.loads(response_data)
                response_dict = json.loads(response_dict)
                status_login = response_dict.get("status", {})
                print(status_login)
                # print(type(response_dict))
                # print(f"[DEBUG] Phản hồi từ Tracker: {response_dict}")
                user_data = response_dict.get("user", {})
                #print("[DEBUG] user_data:", user_data)
                sessions = user_data.get("sessions", [])
                username_temp = user_data.get("username", {})
                print(username_temp);
                #print("[DEBUG] sessions:", sessions)

                if sessions:
                    self.session_id = sessions[-1]["session_id"]
                    print("session ID của phiên đăng nhập hiện tại:", self.session_id)
                else:
                    print("Không tìm thấy session nào!")

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print("[LỖI] Không thể lấy session_id:", str(e))

            
            return response_data

        except Exception as e:
            return f"[ERROR] Lỗi khi gửi dữ liệu: {e}"




# ========== CHAT TASK ==========

    def send_message(self, channel_to_send):
        """Gửi tin nhắn"""
        while self.isChatRunning:
            client_input = input("")
            if client_input.lower() == "\exit":
                self.isChatRunning = False
                self.tracker_socket.sendall("OUTCHAT" .encode('utf-8'))
                break
                #self.leave_tracker()
                #os._exit(0)
            else:
                request = json.dumps({
                    "command": "MSG_SEND",
                    "ip": self.ip,
                    "port": self.port,
                    "name": self.name,
                    "channel": channel_to_send,
                    "message": client_input
                })
                try:
                    self.tracker_socket.sendall(request.encode('utf-8'))
                except Exception as e:
                    print(f"[ERROR] Lỗi khi gửi tin nhắn: {e}")
                    break

    def receive_message(self, channel_to_reiceve ):
        """Nhận tin nhắn từ server"""
        if self.tracker_socket is None:
            print("[ERROR] Không có kết nối socket, không thể nhận tin nhắn.")
            return

        while self.isChatRunning:
            try:
                server_message = self.tracker_socket.recv(1024).decode()
                if not server_message.strip():
                    break
                
                # Parse JSON từ server
                data = json.loads(server_message)
                
                if data.get("command") == "MSG_RECV":
                    print(f"\033[1;34m{data['client_name']} >> {data['message']}\033[0m")

                elif data.get("command") == "NOTIFY":
                    print(f"\033[1;32m[NOTIFY] {data['message']}\033[0m")

            except (json.JSONDecodeError, ConnectionResetError):
                print("[ERROR] Mất kết nối với server.")
                break

    def talk_to_channel(self, channel_name = "GENERAL" ):
        """Bắt đầu chat với server"""
        self.isChatRunning = True
        threading.Thread(target=self.receive_message, args= channel_name, daemon=True).start()
        self.send_message(channel_name)

# ========== AUTHENTICATION ==========

    def login_or_register(self):
        while True:
            print("\n=== ĐĂNG NHẬP / ĐĂNG KÝ / VISITOR ===")
            print("1. Đăng nhập")
            print("2. Đăng ký")
            print("3. Vào với tư cách visitor")
            print("4. Thoát chương trình")

            choice = input("Chọn: ").strip()
            if choice == "1":
                username = input("Tên đăng nhập: ").strip()
                password = input("Mật khẩu: ").strip()
                response = self.send_to_tracker(f"LOGIN {username} {password}")
                if username and self.status_login == "success":
                    self.menu(username)
                else:
                    print("[ERROR] Đăng nhập thất bại, thoát chương trình.")
                return username
            
            elif choice == "2":
                username = input("Tên đăng ký: ").strip()
                password = input("Mật khẩu: ").strip()
                email = input("Email: ").strip()
                response = self.send_to_tracker(f"REGISTER {username} {password} {email}")
            
            elif choice == "3":
                visitor_name = input("Tên của bạn: ").strip()
                response = self.send_to_tracker(f"VISITOR {visitor_name}")
                print("[INFO]", response)
                if visitor_name and self.status_login == "success":
                    self.menu(self.tracker_socket, visitor_name)
                else:
                    print("[ERROR] Đăng nhập thất bại, thoát chương trình.")
                #return visitor_name
            
            elif choice == "4":
                print("[INFO] Thoát chương trình.")
                sys.exit(0)
            else:
                print("[ERROR] Vui lòng chọn 1, 2, 3, 4")

    def logout(self):
        global session_id
        global response_list
        print("Session ID của phiên đăng nhập hiện tại:", session_id)
        if session_id:
            self.send_to_tracker("LOGOUT")
            print("[INFO] Đã đăng xuất. Quay lại màn hình đăng nhập...")
            session_id = None
            response_list = None
        else:
            print("[ERROR] Bạn chưa đăng nhập hoặc session đã hết hạn!")


# ========== MENU TASK ==========

    def menu(self, username):
        try:
            while True:
                print("\n=== MENU ===")
                print("1. User channel list")
                print("2. Gửi tin nhắn đến peer")
                print("3. Create channel")
                print("4. Join channel")
                print("5. All Channel")
                print("6. Đăng xuất")

                choice = input("Chọn một hành động: ").strip()
                if choice == "1":
                    # response_list = json.dumps(response_list)
                    # print(type(response_list))
                    self.send_to_tracker(f"GET_USER_CHANNELS {username}")
                    #print(response_list)
                    #print(type(response_list))
                    try:
                        channel_info = json.loads(self.response_list)
                        #print(channel_info)
                        #print(type(channel_info))
                        joined_channels = channel_info["data"].get("joined_channels", [])
                            
                        hosted_channels = channel_info["data"].get("hosted_channels", [])
                        print("\n=== DANH SÁCH KÊNH ===")
                        if joined_channels:
                            print("Joined Channels:")
                            for idx, channel in enumerate(joined_channels, 1):
                                print(f"{idx}. {channel}")
                        else:
                            print("[INFO] Bạn chưa tham gia kênh nào.")
                        
                        if hosted_channels:
                            print("Hosted Channels:")
                            for idx, channel in enumerate(hosted_channels, 1):
                                print(f"{idx}. {channel}")
                        else:
                            print("[INFO] Bạn chưa tạo kênh nào.")

                        #Select channel
                        channels = joined_channels + hosted_channels

                        selected_channel = input("Nhập tên kênh để vào (hoặc Enter để quay lại): ").strip()
                        if selected_channel in channels:
                            print(f"[INFO] Đang vào kênh: {selected_channel}")
                            print(f"\n=== {selected_channel} ===")
                            print("1. Channel_Info")
                            print("2. Delete channel")
                            print("3. Send Message (Not P2P)")
                            print("ENTER to back")
                            option = input("Chon: ").strip()
                            if option == "1":
                                self.send_to_tracker(f"GET_CHANNEL_INFO {selected_channel}")
                            elif option == "2":
                                self.send_to_tracker(f"DELETE_CHANNEL {username} {selected_channel}")
                            elif option == "3":
                                while True:
                                    print("Nhập tin nhắn (Nhấn ENTER để quay lại màn hình trước): ")
                                    text = input("Message: ").strip()
                                    if text == "":
                                        break
                                    else:
                                        self.send_to_tracker(f"SEND_MESSAGE {username} {selected_channel} {text}")
                            else:
                                break
                        else:
                            print("[ERROR] Tên kênh không hợp lệ.")
                    except Exception as e:
                        print(f"[ERROR] Không thể lấy danh sách kênh: {e}")
                elif choice == "2":
                    target_ip = input("Nhập IP của Peer: ").strip()
                    target_port = input("Nhập Port của Peer: ").strip()
                    message = input("Nhập tin nhắn: ").strip()
                    self.send_to_tracker(f"DATA {target_ip} {target_port} {message}")
                elif choice == "3":
                    channel_name = input("Name of channel: ").strip()
                    host = username
                    self.send_to_tracker(f"CREATE_CHANNEL {host} {channel_name}")
                elif choice == "4":
                    channel_name = input("Name of channel: ").strip()
                    self.send_to_tracker(f"JOIN_CHANNEL {username} {channel_name}")
                elif choice == "5":
                    print("\n=== All Channels ===")
                    
                    self.send_to_tracker("GET_ALL_CHANNELS")
                    
                    try:
                        channel_info = json.loads(self.all_channelist)
                        
                        all_channels = channel_info["data"]
                        
                        print("\n=== DANH SÁCH TẤT CẢ CÁC KÊNH ===")
                        if all_channels:
                            for idx, channel in enumerate(all_channels, 1):
                                print(f"{idx}. {channel['channel_name']} (Chủ kênh: {channel['owner']})")
                        else:
                            print("[INFO] Hiện tại không có kênh nào.")
                        
                        # Chọn kênh để tham gia
                        selected_channel = input("Nhập tên kênh để vào (hoặc Enter để quay lại): ").strip()
                        
                        # Kiểm tra nếu kênh hợp lệ
                        valid_channels = [c["channel_name"] for c in all_channels]
                        if selected_channel in valid_channels:
                            print(f"[INFO] Đang vào kênh: {selected_channel}")
                            print(f"\n=== {selected_channel} ===")
                            print("1. Channel_Info")
                            print("2. Send Message ")
                            print("ENTER để quay lại")
                            
                            option = input("Chọn: ").strip()
                            
                            if option == "1":
                                self.send_to_tracker(f"GET_CHANNEL_INFO {selected_channel}")
                            elif option == "2":
                                self.talk_to_channel(selected_channel)

                            else:
                                print("[INFO] Quay lại menu chính.")
                        
                        else:
                            print("[ERROR] Tên kênh không hợp lệ.")
                    
                    except Exception as e:
                        print(f"[ERROR] Không thể lấy danh sách kênh: {e}")
                elif choice == "6":
                    self.logout()
                    #username = None
                    self.login_or_register()
                else:
                    print("[ERROR] Vui lòng chọn từ 1 đến 3.")
        except KeyboardInterrupt:
            print("\n[INFO] Thoát chương trình...")
            self.logout(username)
            self.sock.close()
            sys.exit()


if __name__ == '__main__':
    USER("127.0.0.1", 5000)




























"""

    def menu(self):
        #Hiển thị menu tùy chọn
        while True:
            print("\n===== MENU =====")
            print("0. Thoát")
            print("1. Lấy danh sách peer")
            print("2. Rời khỏi mạng")
            print("3. Gửi tin nhắn")
            choice = input("Chọn một tùy chọn: ")

            if choice == "0":
                self.leave_tracker()
                break
            elif choice == "1":
                self.get_peer_list()
            elif choice == "2":
                self.leave_tracker()
                break
            elif choice == "3":
                self.talk_to_server()
            else:
                print("[ERROR] Lựa chọn không hợp lệ. Hãy nhập lại.")
"""
