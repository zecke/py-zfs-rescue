#!/usr/bin/env python3

# Copyright (c) 2017 Hristo Iliev <github@hiliev.eu>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
B{Block server}

Provides remote clients with access to the local disks.
"""

from socketserver import TCPServer, BaseRequestHandler
import struct

SERVER_ADDRESS = "localhost"
SERVER_PORT = 24892

trans_table = {}
verbose = False


class BlockTCPHandler(BaseRequestHandler):
    """
    Request handler for the block server
    """
    def handle(self):
        cmd = self.request.recv(1024)
        if len(cmd) < 18:
            print("[-] Block Server: invalid request")
            return
        op = cmd[0]
        if op == 1:
            self.handle_read_block(cmd)
        elif op == 2:
            self.handle_read_blockv(cmd)

    def handle_read_block(self, cmd):
        (op, offset, count) = struct.unpack('=BQQ', cmd[:17])
        path = cmd[17:].decode('utf8')
        data = self._do_read(path, offset, count)
        self.request.sendall(data)

    def handle_read_blockv(self, cmd):
        (op, nreqs) = struct.unpack('=BB', cmd[:2])
        ptr = 2
        data = bytearray()
        for n in range(nreqs):
            (offset, count, pathlen) = struct.unpack('=QQB', cmd[ptr:ptr+17])
            ptr += 17
            path = cmd[ptr:ptr+pathlen].decode('utf8')
            ptr += pathlen
            data += self._do_read(path, offset, count)
        self.request.sendall(data)

    @staticmethod
    def _do_read(path, offset, count):
        if path in trans_table.keys():
            path = trans_table[path]
        if verbose:
            print("[+] Block server: {} -- {}/{}".format(path, offset, count))
        f = open(path, 'rb')
        f.seek(offset)
        data = f.read(count)
        f.close()
        if verbose:
            print("[+]  Read {} bytes".format(len(data)))
        return data


def populate_trans_table():
    global trans_table
    try:
        f = open('disks.tab', 'r')
        entries = [l.strip() for l in f.readlines() if l[0] != '#']
        f.close()
        for entry in entries:
            (path, sub) = entry.split('\t')
            trans_table[path] = sub
    except:
        pass


if __name__ == "__main__":
    populate_trans_table()
    server = TCPServer((SERVER_ADDRESS, SERVER_PORT), BlockTCPHandler)
    server.serve_forever()
