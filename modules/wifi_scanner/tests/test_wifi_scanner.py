import unittest
import subprocess
from unittest.mock import patch

from modules.wifi_scanner import (
    NetshBackend,
    SecurityAssessment,
    WifiNetwork,
    WifiScanner,
    assess_security,
    parse_netsh_output,
)


SAMPLE_NETSH_OUTPUT = """\
Interface name : Wi-Fi
There are 3 networks currently visible.

SSID 1 : MyHome
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : aa:bb:cc:dd:ee:01
         Signal             : 80%
         Radio type         : 802.11n
         Channel            : 6

SSID 2 : OpenCafe
    Network type            : Infrastructure
    Authentication          : Open
    Encryption              : None
    BSSID 1                 : aa:bb:cc:dd:ee:02
         Signal             : 55%
         Radio type         : 802.11g
         Channel            : 11

SSID 3 : OldNet
    Network type            : Infrastructure
    Authentication          : WEP
    Encryption              : WEP
    BSSID 1                 : aa:bb:cc:dd:ee:03
         Signal             : 30%
         Radio type         : 802.11b
         Channel            : 3
"""


class FakeNetshBackend:
    def __init__(self, raw_output: str) -> None:
        self._raw_output = raw_output

    def get_raw_output(self) -> str:
        return self._raw_output


class TestParseNetshOutput(unittest.TestCase):
    def test_parses_all_visible_networks(self) -> None:
        networks = parse_netsh_output(SAMPLE_NETSH_OUTPUT)

        self.assertEqual(len(networks), 3)
        self.assertEqual(networks[0].ssid, "MyHome")
        self.assertEqual(networks[0].bssid, "aa:bb:cc:dd:ee:01")
        self.assertEqual(networks[0].signal_percent, 80)
        self.assertEqual(networks[0].auth_type, "WPA2-Personal")
        self.assertEqual(networks[0].encryption, "CCMP")

    def test_parses_open_network(self) -> None:
        networks = parse_netsh_output(SAMPLE_NETSH_OUTPUT)

        open_network = networks[1]
        self.assertEqual(open_network.ssid, "OpenCafe")
        self.assertEqual(open_network.auth_type, "Open")
        self.assertEqual(open_network.encryption, "None")


class TestSecurityAssessment(unittest.TestCase):
    def test_open_network_is_high_risk(self) -> None:
        network = WifiNetwork(
            ssid="OpenCafe",
            bssid="aa:bb:cc:dd:ee:02",
            signal_percent=55,
            auth_type="Open",
            encryption="None",
        )

        assessment = assess_security(network)

        self.assertEqual(assessment.risk_level, "high")

    def test_wep_network_is_high_risk(self) -> None:
        network = WifiNetwork(
            ssid="OldNet",
            bssid="aa:bb:cc:dd:ee:03",
            signal_percent=30,
            auth_type="WEP",
            encryption="WEP",
        )

        assessment = assess_security(network)

        self.assertEqual(assessment.risk_level, "high")

    def test_wpa2_network_is_low_risk(self) -> None:
        network = WifiNetwork(
            ssid="MyHome",
            bssid="aa:bb:cc:dd:ee:01",
            signal_percent=80,
            auth_type="WPA2-Personal",
            encryption="CCMP",
        )

        assessment = assess_security(network)

        self.assertEqual(assessment.risk_level, "low")


class TestWifiScanner(unittest.TestCase):
    def test_scan_returns_networks_from_backend(self) -> None:
        scanner = WifiScanner(backend=FakeNetshBackend(SAMPLE_NETSH_OUTPUT))

        networks = scanner.scan()

        self.assertEqual(len(networks), 3)
        self.assertEqual(networks[0].ssid, "MyHome")

    def test_scan_with_assessment_returns_risk_levels(self) -> None:
        scanner = WifiScanner(backend=FakeNetshBackend(SAMPLE_NETSH_OUTPUT))

        assessments = scanner.scan_with_assessment()

        self.assertEqual(len(assessments), 3)
        self.assertEqual(assessments[0].risk_level, "low")
        self.assertEqual(assessments[1].risk_level, "high")
        self.assertEqual(assessments[2].risk_level, "high")


class TestNetshBackend(unittest.TestCase):
    @patch("modules.wifi_scanner.scanner.subprocess.run")
    def test_raises_helpful_error_when_netsh_fails(self, mock_run) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["netsh"])
        backend = NetshBackend()

        with self.assertRaises(RuntimeError) as context:
            backend.get_raw_output()

        self.assertIn("Location", str(context.exception))


if __name__ == "__main__":
    unittest.main()
