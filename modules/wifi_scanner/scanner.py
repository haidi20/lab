import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class WifiNetwork:
    ssid: str
    bssid: str
    signal_percent: int
    auth_type: str
    encryption: str


@dataclass(frozen=True)
class SecurityAssessment:
    network: WifiNetwork
    risk_level: str
    reason: str


SSID_PATTERN = re.compile(r"^SSID \d+\s*:\s*(.*)$")
AUTH_PATTERN = re.compile(r"(?:Authentication|Autentikasi)\s*:\s*(.+)$")
ENCRYPTION_PATTERN = re.compile(r"(?:Encryption|Enkripsi)\s*:\s*(.+)$")
BSSID_PATTERN = re.compile(r"^BSSID \d+\s*:\s*(\S+)$")
SIGNAL_PATTERN = re.compile(r"(?:Signal|Sinyal)\s*:\s*(\d+)%")


def parse_netsh_output(raw: str) -> list[WifiNetwork]:
    networks: list[WifiNetwork] = []
    current: dict[str, object] = {}

    for line in raw.splitlines():
        ssid_match = SSID_PATTERN.match(line.strip())
        if ssid_match:
            if current:
                networks.append(_build_network(current))
            current = {"ssid": ssid_match.group(1).strip()}
            continue

        if not current:
            continue

        auth_match = AUTH_PATTERN.search(line)
        if auth_match:
            current["auth_type"] = auth_match.group(1).strip()
            continue

        encryption_match = ENCRYPTION_PATTERN.search(line)
        if encryption_match:
            current["encryption"] = encryption_match.group(1).strip()
            continue

        bssid_match = BSSID_PATTERN.match(line.strip())
        if bssid_match:
            current["bssid"] = bssid_match.group(1).strip()
            continue

        signal_match = SIGNAL_PATTERN.search(line)
        if signal_match:
            current["signal_percent"] = int(signal_match.group(1))

    if current:
        networks.append(_build_network(current))

    return networks


def _build_network(fields: dict[str, object]) -> WifiNetwork:
    return WifiNetwork(
        ssid=str(fields.get("ssid", "")),
        bssid=str(fields.get("bssid", "")),
        signal_percent=int(fields.get("signal_percent", 0)),
        auth_type=str(fields.get("auth_type", "")),
        encryption=str(fields.get("encryption", "")),
    )


def assess_security(network: WifiNetwork) -> SecurityAssessment:
    auth = network.auth_type.lower()

    if auth == "open":
        return SecurityAssessment(network, "high", "Jaringan terbuka tanpa enkripsi.")
    if auth == "wep":
        return SecurityAssessment(network, "high", "WEP sudah tidak aman dan mudah dipecahkan.")
    if auth.startswith("wpa3"):
        return SecurityAssessment(network, "low", "WPA3 adalah standar keamanan terkini.")
    if auth.startswith("wpa2"):
        return SecurityAssessment(network, "low", "WPA2 dengan enkripsi modern masih layak digunakan.")
    if auth.startswith("wpa"):
        return SecurityAssessment(network, "medium", "WPA versi pertama sudah usang, sebaiknya upgrade ke WPA2/WPA3.")
    return SecurityAssessment(network, "medium", "Jenis autentikasi tidak dikenali, perlu pemeriksaan manual.")


class NetshBackend:
    def get_raw_output(self) -> str:
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "Netsh gagal memindai WiFi. Aktifkan Location services di Windows "
                "(Settings > Privacy & security > Location) dan jalankan terminal "
                "sebagai administrator, lalu coba lagi."
            ) from exc


class WifiScanner:
    def __init__(self, backend: NetshBackend | None = None) -> None:
        self._backend = backend if backend is not None else NetshBackend()

    def scan(self) -> list[WifiNetwork]:
        return parse_netsh_output(self._backend.get_raw_output())

    def scan_with_assessment(self) -> list[SecurityAssessment]:
        return [assess_security(network) for network in self.scan()]
