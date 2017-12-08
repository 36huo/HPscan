#!/usr/bin/env python2
#-*- coding:utf-8 -*-

import ipaddress
import os
import sys
import socket
import threading
import Queue
import time
import getopt


def scanIt(host,port,timeout):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host,port))
        mutex.acquire()
        res = host+':' + str(port)+ '\tOPEN!'
        mutex.release()
    except socket.error, v:
        errorcode=v[0]
        if errorcode!="timed out":
            mutex.acquire()
            print host+':' + str(port)+'\t'+ str(errorcode)
            mutex.release()
        #res = ''
        res = ' '
        #print sys.exc_info()
        pass
    s.close()
    return res

class MyThread(threading.Thread):
    def  __init__(self, workQueue, resultQueue, timeout=1,  *args, **kwargs):
        threading.Thread.__init__(self)
        self.workQueue =  workQueue
        self.resultQueue = resultQueue
        self.timeout = timeout
        self.kwargs = kwargs
        self.args = args
        self.setDaemon(False)
        self.start()

    #overwrite run()
    def run(self):
        while True:
            try:
                callable, host, port,timeout = self.workQueue.get(timeout=self.timeout)
                result = callable(host,port,timeout)
                if result != ' ':
                    # result = callable(host, port)
                    self.resultQueue.put(result)
            except Queue.Empty:
                break
            except:
                print sys.exc_info()
                #raise
                pass

class ThreadPool(object):
    def __init__(self ,num_of_threads=5):
        self.workQueue = Queue.Queue()
        self.resultQueue =Queue.Queue()
        self.num_of_threads = num_of_threads
        self.threads = []
        self.createThreadPool(self.num_of_threads)

    def createThreadPool(self,num_of_threads):
        for i in range(num_of_threads):
            thread = MyThread(self.workQueue, self.resultQueue)
            self.threads.append(thread)

    def waitThreadComplet(self):
        while len(self.threads):
            thread = self.threads.pop()
            if thread.isAlive():
                thread.join()

    def add_job(self, callable, *args):#, **kwargs):
        self.workQueue.put((callable, args[0], args[1], args[2]))#, kwargs)
        #self.resultQueue.put( 'add done')


class Argv2IP:
    def __init__(self):
        pass

    # 解析文件格式
    def file_parse(self, file):
        hosts = []
        if not os.path.isfile(file):
            return hosts
        lines = open(file, 'r').readlines()
        for line in lines:
            hosts += self.meta_parse(line.strip())
        return hosts

    # 解析复合格式
    def complex_parse(self, str):
        host = []
        for item in  [i.strip() for i in str.split(",")]:
            host += self.meta_parse(item)
        return host

    # 解析原始格式
    def meta_parse(self, string):
        hosts = []
        if string.find("/") > 0:
            hosts += self.parse_with_netmask(string)
        elif string.find("-") > 0:
            hosts += self.parse_with_range(string)
        else:
            h = self.parse_with_alone(string)
            if h!= None:
                hosts.append(h)
        return hosts

    def parse_with_netmask(self, string):
        hosts = []
        try:
            for item in ipaddress.IPv4Interface(string).network:
                hosts.append(str(item))
        except:
            hosts = []
        #hosts = hosts[1:-1]
        return hosts

    def parse_with_range(self,string):
        hosts = []
        try:
            startip = string.split("-")[0];
            start = int(startip.split(".")[-1])
            end = int(string.split("-")[1])
        except:
            return []
        if start >= end or end > 255 or start < 0:
            return []
        try:
            ip = ipaddress.ip_address(startip)
        except ValueError as e:
            return []
        hosts.append(str(ip))
        for i in range(end - start):
            hosts.append(str(ip + i + 1))
        return hosts

    def parse_with_alone(self, string):
        try:
            ip = ipaddress.ip_address(string)
        except ValueError as e:
            return None
        return str(ip)

    @staticmethod
    def string(str):
        hosts = []
        arg2ip = Argv2IP()
        #print("<li> 要处理的字符串: ", str)
        if str.find(",") != -1:
            hosts += arg2ip.complex_parse(str)
        else:
            hosts += arg2ip.meta_parse(str)
        return hosts

    @staticmethod
    def file(file):
        arg2ip = Argv2IP()
        hosts = arg2ip.file_parse(file)
        return hosts


class Argv2port:
    def __init__(self):
        pass

    def parse_with_range(self,string):
        ports = []
        try:
            startport = int(string.split("-")[0]);
            endport = int(string.split("-")[1]);
        except:
            return []

        if startport >= endport or endport > 65535 or startport < 0:
            return []
        for i in range(startport,endport+1,1):
            ports.append(i)

        return ports

    def complex_parse(self, str):
        ports = []
        for item in  [i.strip() for i in str.split(",")]:
            ports += self.meta_parse(item)
        return ports

    def meta_parse(self, string):
        ports = []
        if string.find("-") > 0:
            ports+=self.parse_with_range(string)
        else:
            ports.append(int(string))
        return ports

    @staticmethod
    def string(str):
        ports = []
        arg2port = Argv2port()
        if str.find(",") != -1:
            ports += arg2port.complex_parse(str)
        else:
            ports += arg2port.meta_parse(str)
        return ports

def main(argv):

    MaxProcs=400
    port=80
    ipadd='127.0.0.1'
    timeout=3
    if len(argv)==0:
        print sys.argv[0]+' -i ipaddress -p port [-P max-procs] [-t timeout]'
        sys.exit(2)
    try:
        opts, args = getopt.getopt(argv,"hP:p:i:t:")
    except getopt.GetoptError:
        print sys.argv[0]+' -i ipaddress -p port [-P max-procs] [-t timeout]'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print sys.argv[0]+' -i ipaddress -p port [-P max-procs] [-t timeout]'
            sys.exit()
        elif opt in ("-P"):
            MaxProcs = int(arg)
        elif opt in ("-p"):
            port = arg
        elif opt in ("-i"):
            ipadd = arg
        elif opt in ("-t"):
            timeout = int(arg)

    hosts = Argv2IP.string(ipadd.decode('ascii'))
    ports = Argv2port.string(str(port))


    w = ThreadPool(MaxProcs)
    print 'start..',time.ctime()
    # urls = []
    # for i in xrange(1,256):
    #     urls.append("192.168.187."+str(i))
    port=80
    for host in hosts:
        for port in ports:
            w.add_job(scanIt, host, port,timeout)

    w.waitThreadComplet()

    while w.resultQueue.qsize():
        print w.resultQueue.get()
    print 'end...',time.ctime()


if __name__ == '__main__':
    mutex = threading.Lock()
    main(sys.argv[1:])
