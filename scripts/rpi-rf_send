#!/usr/bin/env python3

import argparse
import logging

from rpi_rf import RFDevice

logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s',)

parser = argparse.ArgumentParser(description='Sends a decimal code via a 433/315MHz GPIO device')
parser.add_argument('code', metavar='CODE', type=int,
                    help="Decimal code to send")
parser.add_argument('-g', dest='gpio', type=int, default=17,
                    help="GPIO pin (Default: 17)")
parser.add_argument('-p', dest='pulselength', type=int, default=None,
                    help="Pulselength (Default: 350)")
parser.add_argument('-t', dest='protocol', type=int, default=None,
                    help="Protocol (Default: 1)")
parser.add_argument('-l', dest='length', type=int, default=None,
                    help="Codelength (Default: 24)")
parser.add_argument('-r', dest='repeat', type=int, default=10,
                    help="Repeat cycles (Default: 10)")
args = parser.parse_args()

rfdevice = RFDevice(args.gpio)
rfdevice.enable_tx()
rfdevice.tx_repeat = args.repeat

if args.protocol:
    protocol = args.protocol
else:
    protocol = "default"
if args.pulselength:
    pulselength = args.pulselength
else:
    pulselength = "default"
if args.length:
    length = args.length
else:
    length = "default"

logging.info(str(args.code) +
             " [protocol: " + str(protocol) +
             ", pulselength: " + str(pulselength) +
             ", length: " + str(length) +
             ", repeat: " + str(rfdevice.tx_repeat) + "]")

rfdevice.tx_code(args.code, args.protocol, args.pulselength, args.length)
rfdevice.cleanup()
