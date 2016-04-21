#!/usr/bin/env python3

import argparse
import logging

from rpi_rf import RFDevice

logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s',)

parser = argparse.ArgumentParser(description='Sends a decimal code via a 433MHz GPIO device')
parser.add_argument('code', metavar='CODE', type=int,
                    help="Decimal code to send")
parser.add_argument('-g', dest='gpio', type=int, default=17,
                    help="GPIO pin (Default: 17)")
parser.add_argument('-p', dest='pulselength', type=int, default=350,
                    help="Pulselength (Default: 350)")
parser.add_argument('-t', dest='protocol', type=int, default=1,
                    help="Protocol (Default: 1)")
args = parser.parse_args()

rfdevice = RFDevice(args.gpio)
rfdevice.enable_tx()
rfdevice.tx_pulselength = args.pulselength
rfdevice.tx_proto = args.protocol
logging.info(str(args.code) +
             " [pulselength " + str(args.pulselength) +
             ", protocol " + str(args.protocol) + "]")
rfdevice.tx_code(args.code)
rfdevice.cleanup()
