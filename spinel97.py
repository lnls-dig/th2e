########## Spinel97 protocol binary implementation ###########
# Inspired by and adapted from pyspinel
# http://sourceforge.net/projects/pyspinel
#
#   This class is a more generic version of pyspinel, which
# interfaces with equipments that use the Spinel 97 protocol
# created by Papouch
import socket
from random import randint
import struct
from time import sleep

#   Protocol Constants
PRE = 0x2A    #Prefix is char '*' = 2Ah
FRM = 0x61    #Format is Spinel 97 = 61h (There's also Spinel 66, not implemented here)
CR = 0x0D     #Carriage return is the last char of every message
broadcast_address = 0xFF
universal_address = 0xFE

class Sensor():
    def __init__(self, ip, port=10001, timeout = 5):
        self.ip = ip
        self.port = port
        try:
            self.socket = socket.create_connection((self.ip,self.port), timeout)
        except socket.error:
            raise

    def query(self, inst, param, receive=True, addr=universal_address):
        self.current_sig = randint(0,255)
        NUM = 5 + len(param)
        SUMA = 255 - (PRE + FRM + NUM + addr + self.current_sig + inst)

        #Calculate Checksum
        for value in param:
            SUMA = SUMA - value

        while SUMA < 0: #simulate byte overrun
            SUMA += 256

        #Build the message
        msg = struct.pack('>2BH3B', PRE, FRM, NUM, addr, self.current_sig, inst)

        #Append the parameters
        for data in param:
            msg += struct.pack('B', data)

        #Finish the message
        msg += struct.pack('2B', SUMA, CR)

        #Connect to device and send message
        try:
            self.socket.sendall(msg)
        except socket.error:
            raise

        if addr == broadcast_address or not receive: #broadcast address, no response should be received OR we don't want to receive anything
            return None
        else: #should get a response
            try:
                adr, data = self.receive()
            except socket.error:
                raise
            if adr != addr and addr != universal_address:
                raise ValueError("Wrong packet address ADR, expected " + str(address) + " , got " + str(adr))
            else:
                return data

    def receive(self):
        resp = []
        while True:
            resp += self.socket.recv(1024)
            if resp[0] == '*' and resp[len(resp)-1] == chr(0x0d):
                header = struct.unpack('>2BH3B', ''.join(resp[:7]))
                if not self.check_header(header):
                    raise Exception
                return header[2], resp[7:]
            else:
                sleep(0.1)

    def check_header(self, header):
        pre, frm, num, address, sig, ack = header
        if pre != PRE:
            print ("Wrong prefix char PRE, expected " + str(PRE) + " got " + str(pre))
            return False
        elif frm != FRM:
            print ("Wrong packet format FRM, expected " + str(FRM) + " got " + str(frm))
            return False
        elif sig != self.current_sig:
            print ("Wrong packet signature SIG, expected " + str(self.current_sig) + " , got " + str(sig))
            return False
        #TODO: Check ACK Code according to selected mode
        #elif ack != 0:
            #print ("Error reported by ACK: " + ACK[ack])
            #return False
        else:
            return True

    def instruct(self, inst, param, addr=universal_address):
        self.query(inst, param, True, addr)
