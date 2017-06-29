#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import time
import socket
import json
import urllib2
import json
import gzip
from StringIO import StringIO
from urllib import urlencode
from raven import Client

config = None

class DbTransfer(object):

    instance = None

    def __init__(self):
        self.last_get_transfer = {}

    @staticmethod
    def get_instance():
        if DbTransfer.instance is None:
            DbTransfer.instance = DbTransfer()
        return DbTransfer.instance

    @staticmethod
    def send_command(cmd):
        data = ''

        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(1)
        cli.sendto(cmd, ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
        data, addr = cli.recvfrom(1500)
        cli.close()

        return data

    @staticmethod
    def get_servers_transfer():
        dt_transfer = {}
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(2)
        cli.sendto('transfer: {}', ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
        bflag = False
        while True:
            data, addr = cli.recvfrom(1500)
            if data == 'e':
                break
            data = json.loads(data)
            print data
            dt_transfer.update(data)
        cli.close()
        return dt_transfer

    @staticmethod
    def get_ports():
        ports = []
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(2)
        cli.sendto('ports: {}', ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
        bflag = False
        while True:
            data, addr = cli.recvfrom(1500)
            if data == 'e':
                break
            data = json.loads(data)
            ports.extend(data)
        cli.close()
        return ports

    def push_db_all_user(self):
        dt_transfer = self.get_servers_transfer()
        if dt_transfer:
            # apply ratio
            for k in dt_transfer.keys():
                dt_transfer[k] = config.TRANSFER_RATIO * dt_transfer[k]

            # upload stats
            payload = {
                'token': config.SYNC_TOKEN,
                'port_data': json.dumps(dt_transfer),
            }
            resp = urllib2.urlopen(config.SYNC_API_URL + '/v1/sync/traffic', urlencode(payload))
            if resp.code != 200:
                raise RuntimeError(json.load(resp))

    def pull_db_all_user(self):
        req = urllib2.Request(config.SYNC_API_URL + '/v1/sync/users', "token=%s" % config.SYNC_TOKEN)
        req.add_header('Accept-encoding', 'gzip')
        resp = urllib2.urlopen(req)
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            data = json.load(f)
        else:
            data = json.load(resp)
        traffic_ok_users = data['traffic_ok']
        traffic_exceed_users = data['traffic_exceed']
        r_ports = [user[1] for user in traffic_ok_users] + [user[1] for user in traffic_exceed_users]

        l_ports = self.get_ports()

        # for traffic ok active users, add or change password
        for user in traffic_ok_users:
            if user[1] in l_ports:
                server = json.loads(DbTransfer.get_instance().send_command('stat: {"server_port":%s}' % user[1]))
                if server['stat'] != 'ko':
                    if user[2] != server['password']:
                        logging.info('db stop server at port [%s] reason: password changed' % (user[1]))
                        DbTransfer.send_command('remove: {"server_port":%s}' % user[1])
            else:
                logging.info('db start server at port [%s] pass [%s]' % (user[1], user[2]))
                DbTransfer.send_command('add: {"server_port": %s, "password":"%s"}'% (user[1], user[2]))
        # for traffic not ok users, disable
        for user in traffic_exceed_users:
            if user[1] in l_ports:
                logging.info('db stop server at port [%s] reason: out bandwidth' % (user[1]))
                DbTransfer.send_command('remove: {"server_port":%s}' % user[1])
        # for not in users, remove
        for port in l_ports:
            if port not in r_ports:
                print port
                logging.info('db stop server at port [%s] reason: disable' % port)
                DbTransfer.send_command('remove: {"server_port":%s}' % port)

    @staticmethod
    def thread_db(conf):
        global config
        config = conf
        import socket
        import time
        timeout = 30
        socket.setdefaulttimeout(timeout)
        if config.SENTRY_DSN:
            client = Client(config.SENTRY_DSN)
        while True:
            logging.info('db loop')
            try:
                DbTransfer.get_instance().pull_db_all_user()
                DbTransfer.get_instance().push_db_all_user()
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.warn('db thread except:%s' % e)
                if config.SENTRY_DSN:
                    client.captureException()
            finally:
                time.sleep(60)


#SQLData.pull_db_all_user()
#print DbTransfer.send_command("")
