import socket
import json


class UDPServer:
    def __init__(self, server_ip, server_port):
        # 设置UDP服务器地址和端口
        self.server = (server_ip, server_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)

    def send(self, control_cmd):
        self.socket.sendto(
            bytes(json.dumps(control_cmd), "utf-8"), self.server)

    def send_raw(self, control_cmd: bytes):
        self.socket.sendto(
            control_cmd, self.server)
        # print('sent: ', control_cmd, 'to: ', self.server)


class HandCommunication:
    def __init__(self, stupid=False):
        if stupid:
            self._left_hand_server_ip = '192.168.137.39'
            self._right_hand_server_ip = '192.168.137.19'
        else:
            self._left_hand_server_ip = '192.168.137.19'
            self._right_hand_server_ip = '192.168.137.39'
        self._server_port = 2333
        self.left_hand_udp_server = UDPServer(
            self._left_hand_server_ip, self._server_port)
        self.right_hand_udp_server = UDPServer(
            self._right_hand_server_ip, self._server_port)
        self.servers = {
            'left': self.left_hand_udp_server,
            'right': self.right_hand_udp_server
        }

    def _angle_set(self, id, angles):
        send_data = bytearray()
        send_data.append(0xEB)  # 包头
        send_data.append(0x90)  # 包头
        send_data.append(id)    # 灵巧手 ID 号
        send_data.append(0x0F)  # 该帧数据部分长度 12 + 3
        send_data.append(0x12)  # 写寄存器命令标志
        send_data.append(0xCE)  # 寄存器起始地址低八位
        send_data.append(0x05)  # 寄存器起始地址高八位

        # Append val1 to val6 as little-endian
        for angle in angles:
            angle = int(angle)
            send_data.append(angle & 0xFF)
            send_data.append((angle >> 8) & 0xFF)

        # Calculate checksum
        checksum = sum(send_data[2:19]) & 0xFF
        send_data.append(checksum)

        return send_data

    def get_angle(self, side: str, id: int):
        send_data = bytearray()
        send_data.append(0xEB)  # 包头
        send_data.append(0x90)  # 包头
        send_data.append(int(id))
        send_data.append(0x04)
        send_data.append(0x11)  # kCmd_Handg3_Read
        send_data.append(0x0a)
        send_data.append(0x06)
        send_data.append(0x0c)

        checksum = sum(send_data[2:8]) & 0xFF
        send_data.append(checksum)

        server = self.servers[side]

        server.send_raw(send_data)
        try:
            data, addr = server.socket.recvfrom(1024)
            received_checksum = data[19]
            calculated_checksum = sum(data[2:19]) & 0xFF

            if received_checksum != calculated_checksum:
                raise ValueError("Checksum mismatch")

            print(data)
            pos = [
                data[7] | (data[8] << 8),
                data[9] | (data[10] << 8),
                data[11] | (data[12] << 8),
                data[13] | (data[14] << 8),
                data[15] | (data[16] << 8),
                data[17] | (data[18] << 8)
            ]

            return pos

        except Exception as e:
            print(e)
            return None

    def send_hand_cmd(self, left_hand_angles, right_hand_angles):
        id = 1
        left_cmd = self._angle_set(id, left_hand_angles)
        self.left_hand_udp_server.send_raw(left_cmd)
        try:
            _, _ = self.left_hand_udp_server.socket.recvfrom(1024)
        except:
            pass

        right_cmd = self._angle_set(id, right_hand_angles)
        self.right_hand_udp_server.send_raw(right_cmd)
        try:
            _, _ = self.right_hand_udp_server.socket.recvfrom(1024)
        except:
            pass
