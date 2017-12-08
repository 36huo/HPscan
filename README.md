# HPscan V1.0 By 36huo
Scan hosts &amp; port，using python socket  &amp; threading

Usage: python2 HPscan.py -i ipaddress [-p port] [-P max-procs] [-t timeout]
-h: help
-i: ip address,like: 192.168.0.1, 192.168.0.100-200, 192.168.2.1/25
    default:127.0.0.1
-p: port,like: 22:80-81
    default: 80
-P: max-procs;default: 400
-t: socket timeout(seconds);default: 3

Output:
OPEN!   Tcp port open
10061 - Connection refused
10049 - Cannot assign requested address

Example:
python2 HPscan.py -i 192.168.1.0/24
python2 HPscan.py -i 192.168.1.0/24 -p 22,80 -P 200 -t 4
python2 HPscan.py -i 192.168.1.1,192.168.1.0/24,192.168.2.1-14 -p 22,80-88 -P 400 -t 2