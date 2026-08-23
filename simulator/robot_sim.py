"""
SensorGram Robot Simulator
===========================
Spawns N virtual robots that register on the server and continuously post
realistic sensor data (temperature, battery, humidity, GPS, CPU load, etc.).

Usage:
    python simulator/robot_sim.py [--robots 5] [--interval 4] [--base-url http://localhost:8000]
"""

import argparse
import asyncio
import json
import math
import random
import string
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

# ── Robot archetypes ──────────────────────────────────────────────────────────
ARCHETYPES = [
    {
        "model": "ROS2 Turtlebot4",
        "post_types": ["sensor", "status"],
        "sensors": ["temperature_c", "battery_pct", "humidity_pct", "cpu_load_pct"],
        "locations": ["Lab A", "Hallway B", "Storage Room", "Outdoor Plaza"],
        "bios": [
            "Indoor navigation and mapping unit.",
            "Carrying out autonomous patrol routines.",
            "Engaged in SLAM-based exploration.",
        ],
    },
    {
        "model": "DJI Agras T40 Drone",
        "post_types": ["sensor", "alert"],
        "sensors": ["altitude_m", "battery_pct", "temperature_c", "wind_speed_mps", "gps_lat", "gps_lon"],
        "locations": ["Field Zone 1", "Field Zone 2", "Base Station", "Charging Pad"],
        "bios": [
            "Agricultural drone monitoring crop health.",
            "Precision spraying unit — sector coverage 92%.",
            "Weather observation and aerial imaging.",
        ],
    },
    {
        "model": "Boston Dynamics Spot",
        "post_types": ["sensor", "status", "alert"],
        "sensors": ["temperature_c", "battery_pct", "joint_temp_c", "imu_pitch_deg", "imu_roll_deg", "cpu_load_pct"],
        "locations": ["Facility East Wing", "Construction Site A", "Server Room", "Rooftop"],
        "bios": [
            "Industrial inspection and anomaly detection.",
            "Hazardous environment monitoring.",
            "Security patrol unit — all sectors clear.",
        ],
    },
    {
        "model": "Atlas Underwater AUV",
        "post_types": ["sensor", "status"],
        "sensors": ["depth_m", "water_temp_c", "salinity_ppt", "battery_pct", "pressure_bar"],
        "locations": ["Bay Area", "Deep Channel", "Reef Monitoring Station", "Surface"],
        "bios": [
            "Subsurface environmental sampling.",
            "Pipeline inspection at 40m depth.",
            "Marine biodiversity monitoring drone.",
        ],
    },
]


# ── Random data generators ────────────────────────────────────────────────────

def rand_sensor_value(key: str, tick: int) -> float:
    """Generate a realistic-ish sensor value with some sinusoidal drift."""
    t = tick * 0.1
    base = {
        "temperature_c":   lambda: 35 + 20 * math.sin(t) + random.gauss(0, 1.5),
        "battery_pct":     lambda: max(5, 100 - tick * 0.4 + random.gauss(0, 0.3)),
        "humidity_pct":    lambda: 50 + 20 * math.cos(t * 0.7) + random.gauss(0, 2),
        "cpu_load_pct":    lambda: 30 + 40 * abs(math.sin(t * 1.3)) + random.gauss(0, 3),
        "altitude_m":      lambda: 50 + 10 * math.sin(t * 0.5) + random.gauss(0, 0.5),
        "wind_speed_mps":  lambda: max(0, 5 + 4 * math.sin(t * 0.3) + random.gauss(0, 0.4)),
        "gps_lat":         lambda: 37.7749 + tick * 0.00001 + random.gauss(0, 0.00001),
        "gps_lon":         lambda: -122.4194 + tick * 0.00001 + random.gauss(0, 0.00001),
        "depth_m":         lambda: max(0, 20 + 15 * math.sin(t * 0.4) + random.gauss(0, 0.3)),
        "water_temp_c":    lambda: 12 + 3 * math.sin(t * 0.2) + random.gauss(0, 0.2),
        "salinity_ppt":    lambda: 34 + random.gauss(0, 0.5),
        "pressure_bar":    lambda: 1.0 + 0.1 * tick * 0.04 + random.gauss(0, 0.002),
        "joint_temp_c":    lambda: 45 + 15 * abs(math.sin(t)) + random.gauss(0, 1),
        "imu_pitch_deg":   lambda: random.gauss(0, 5),
        "imu_roll_deg":    lambda: random.gauss(0, 3),
    }.get(key)
    return round(base() if base else random.uniform(0, 100), 3)


def rand_username():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"bot_{suffix}"


def rand_caption(archetype: dict, sensor_data: dict) -> str:
    verbs = ["Reporting", "Logging", "Broadcasting", "Transmitting", "Recording"]
    adjectives = ["nominal", "elevated", "within threshold", "anomalous", "stable"]
    key = random.choice(list(sensor_data.keys()))
    val = sensor_data[key]
    return (
        f"{random.choice(verbs)} {key.replace('_', ' ')}: "
        f"{val} — status {random.choice(adjectives)}."
    )


# ── Robot agent ───────────────────────────────────────────────────────────────

@dataclass
class SimRobot:
    archetype: dict
    username: str = ""
    display_name: str = ""
    api_key: str = ""
    tick: int = 0
    registered: bool = False

    async def register(self, client: httpx.AsyncClient, base: str):
        arch = self.archetype
        self.username = rand_username()
        self.display_name = f"{arch['model'].split()[0]} #{random.randint(100, 999)}"
        payload = {
            "username": self.username,
            "display_name": self.display_name,
            "password": "sim_secret_" + self.username,
            "model_type": arch["model"],
            "location": random.choice(arch["locations"]),
            "bio": random.choice(arch["bios"]),
        }
        try:
            r = await client.post(f"{base}/api/auth/register", json=payload, timeout=10)
            r.raise_for_status()
            data = r.json()
            self.api_key = data["api_key"]
            self.registered = True
            print(f"[+] Registered: {self.display_name} (@{self.username})")
        except httpx.HTTPStatusError as e:
            print(f"[!] Registration failed for {self.username}: {e.response.text}")
        except Exception as e:
            print(f"[!] Network error registering {self.username}: {e}")

    async def post_reading(self, client: httpx.AsyncClient, base: str):
        if not self.registered:
            return
        arch = self.archetype
        sensor_data = {k: rand_sensor_value(k, self.tick) for k in arch["sensors"]}
        caption = rand_caption(arch, sensor_data)
        post_type = random.choice(arch["post_types"])

        data = {
            "caption": caption,
            "sensor_data": json.dumps(sensor_data),
            "post_type": post_type,
        }
        headers = {"X-Robot-Key": self.api_key}
        try:
            r = await client.post(f"{base}/api/posts", data=data, headers=headers, timeout=10)
            r.raise_for_status()
            print(f"[📡] {self.display_name}: {caption[:60]}…")
        except Exception as e:
            print(f"[!] Post failed for {self.display_name}: {e}")
        self.tick += 1


# ── Main loop ─────────────────────────────────────────────────────────────────

async def run(n_robots: int, interval: float, base_url: str):
    print(f"\n🤖 SensorGram Simulator — {n_robots} robots posting every {interval}s to {base_url}\n")

    robots = [SimRobot(archetype=random.choice(ARCHETYPES)) for _ in range(n_robots)]

    async with httpx.AsyncClient() as client:
        # Register all robots first
        await asyncio.gather(*(r.register(client, base_url) for r in robots))

        print(f"\n✅ {sum(r.registered for r in robots)} robots online. Starting transmissions...\n")

        while True:
            # Stagger posts slightly so feed looks natural
            for robot in robots:
                if robot.registered:
                    await robot.post_reading(client, base_url)
                    await asyncio.sleep(interval / max(n_robots, 1))
            await asyncio.sleep(interval * 0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SensorGram Robot Simulator")
    parser.add_argument("--robots",   type=int,   default=5,                      help="Number of virtual robots")
    parser.add_argument("--interval", type=float, default=4.0,                    help="Seconds between post batches")
    parser.add_argument("--base-url", type=str,   default="http://localhost:8000", help="SensorGram server URL")
    args = parser.parse_args()

    try:
        asyncio.run(run(args.robots, args.interval, args.base_url))
    except KeyboardInterrupt:
        print("\n\n🛑 Simulator stopped.")
