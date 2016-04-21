"""
Sending and receiving 433Mhz signals with cheap GPIO RF Modules on a Raspberry Pi.
"""

import logging
import time

from RPi import GPIO

MAX_CHANGES = 67

_LOGGER = logging.getLogger(__name__)


class RFDevice:
    """Representation of a GPIO RF device."""

    # pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self, gpio,
                 tx_proto=1, tx_pulselength=350, tx_repeat=10, tx_length=24, rx_tolerance=120):
        """Initialize the RF device."""
        self.gpio = gpio
        self.tx_enabled = False
        self.tx_proto = tx_proto
        self.tx_pulselength = tx_pulselength
        self.tx_repeat = tx_repeat
        self.tx_length = tx_length
        self.rx_enabled = False
        self.rx_tolerance = rx_tolerance
        # internal values
        self._rx_timings = [0] * (MAX_CHANGES + 1)
        self._rx_last_timestamp = 0
        self._rx_change_count = 0
        self._rx_repeat_count = 0
        # successful RX values
        self.rx_code = None
        self.rx_code_timestamp = None
        self.rx_proto = None
        self.rx_bitlength = None
        self.rx_delay = None

        GPIO.setmode(GPIO.BCM)
        _LOGGER.debug("Using GPIO " + str(gpio))

    def cleanup(self):
        """Disable TX and RX and clean up GPIO."""
        if self.tx_enabled:
            self.disable_tx()
        if self.rx_enabled:
            self.disable_rx()
        _LOGGER.debug("Cleanup")
        GPIO.cleanup()

    def enable_tx(self):
        """Enable TX, set up GPIO."""
        if self.rx_enabled:
            _LOGGER.error("RX is enabled, not enabling TX")
            return False
        if not self.tx_enabled:
            self.tx_enabled = True
            GPIO.setup(self.gpio, GPIO.OUT)
            _LOGGER.debug("TX enabled")
        return True

    def disable_tx(self):
        """Disable TX, reset GPIO."""
        if self.tx_enabled:
            # set up GPIO pin as input for safety
            GPIO.setup(self.gpio, GPIO.IN)
            self.tx_enabled = False
            _LOGGER.debug("TX disabled")
        return True

    def tx_code(self, code):
        """Send a decimal code."""
        rawcode = format(code, '#0{}b'.format(self.tx_length + 2))[2:]
        _LOGGER.debug("TX code: " + str(code))
        return self.tx_bin(rawcode)

    def tx_bin(self, rawcode):
        """Send a binary code."""
        _LOGGER.debug("TX bin: " + str(rawcode))
        for _ in range(0, self.tx_repeat):
            for byte in range(0, self.tx_length):
                if rawcode[byte] == '0':
                    if not self.tx_l0():
                        return False
                else:
                    if not self.tx_l1():
                        return False
            if not self.tx_sync():
                return False

        return True

    def tx_l0(self):
        """Send a '0' bit."""
        if self.tx_proto == 1:
            return self.tx_waveform(1, 3)
        elif self.tx_proto == 2:
            return self.tx_waveform(1, 2)
        else:
            return False

    def tx_l1(self):
        """Send a '1' bit."""
        if self.tx_proto == 1:
            return self.tx_waveform(3, 1)
        elif self.tx_proto == 2:
            return self.tx_waveform(2, 1)
        else:
            return False

    def tx_sync(self):
        """Send a sync."""
        if self.tx_proto == 1:
            return self.tx_waveform(1, 31)
        elif self.tx_proto == 2:
            return self.tx_waveform(1, 10)
        else:
            return False

    def tx_waveform(self, highpulses, lowpulses):
        """Send basic waveform."""
        if not self.tx_enabled:
            _LOGGER.error("TX is not enabled, not sending data")
            return False
        GPIO.output(self.gpio, GPIO.HIGH)
        time.sleep((highpulses * self.tx_pulselength) / 1000000)
        GPIO.output(self.gpio, GPIO.LOW)
        time.sleep((lowpulses * self.tx_pulselength) / 1000000)
        return True

    def enable_rx(self):
        """Enable RX, set up GPIO and add event detection."""
        if self.tx_enabled:
            _LOGGER.error("TX is enabled, not enabling RX")
            return False
        if not self.rx_enabled:
            self.rx_enabled = True
            GPIO.setup(self.gpio, GPIO.IN)
            GPIO.add_event_detect(self.gpio, GPIO.BOTH)
            GPIO.add_event_callback(self.gpio, self.rx_callback)
            _LOGGER.debug("RX enabled")
        return True

    def disable_rx(self):
        """Disable RX, remove GPIO event detection."""
        if self.rx_enabled:
            GPIO.remove_event_detect(self.gpio)
            self.rx_enabled = False
            _LOGGER.debug("RX disabled")
        return True

    # pylint: disable=unused-argument
    def rx_callback(self, gpio):
        """RX callback for GPIO event detection. Handle basic signal detection."""
        timestamp = int(time.perf_counter() * 1000000)
        duration = timestamp - self._rx_last_timestamp

        if duration > 5000:
            if self._rx_timings[0] + 200 > duration > self._rx_timings[0] - 200:
                self._rx_repeat_count += 1
                self._rx_change_count -= 1
                if self._rx_repeat_count == 2:
                    if self._rx_waveform(1, self._rx_change_count, timestamp):
                        _LOGGER.debug("RX code [protocol 1]: " + str(self.rx_code))
                    elif self._rx_waveform(2, self._rx_change_count, timestamp):
                        _LOGGER.debug("RX code [protocol 2]: " + str(self.rx_code))
                    self._rx_repeat_count = 0
            self._rx_change_count = 0

        if self._rx_change_count >= MAX_CHANGES:
            self._rx_change_count = 0
            self._rx_repeat_count = 0
        self._rx_timings[self._rx_change_count] = duration
        self._rx_change_count += 1
        self._rx_last_timestamp = timestamp

    def _rx_waveform(self, proto, change_count, timestamp):
        """Detect waveform and format code."""
        if proto == 1:
            sync = 31
            pulse = 3
        elif proto == 2:
            sync = 10
            pulse = 2
        else:
            return False
        code = 0
        delay = self._rx_timings[0] / sync
        delay_tolerance = delay * self.rx_tolerance * 0.01

        for i in range(1, change_count, 2):
            if (delay + delay_tolerance > self._rx_timings[i] > delay - delay_tolerance and
                    delay * pulse + delay_tolerance > self._rx_timings[i+1] > delay * pulse - delay_tolerance):
                code <<= 1
            elif (delay * pulse + delay_tolerance > self._rx_timings[i] > delay * pulse - delay_tolerance and
                  delay + delay_tolerance > self._rx_timings[i+1] > delay - delay_tolerance):
                code += 1
                code <<= 1
            else:
                code = 0
        code >>= 1

        if change_count > 6 and code != 0:
            self.rx_code = code
            self.rx_code_timestamp = timestamp
            self.rx_bitlength = change_count / 2
            self.rx_delay = delay
            self.rx_proto = proto
            return True

        return False
