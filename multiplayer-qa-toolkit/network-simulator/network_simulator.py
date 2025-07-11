#!/usr/bin/env python3
"""
Network Condition Simulator for Multiplayer Game Testing
Epic Games QA Toolkit
"""

import asyncio
import random
import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from collections import deque
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NetworkCondition:
    """Represents network conditions for simulation"""
    name: str
    latency_ms: float
    jitter_ms: float
    packet_loss_rate: float
    bandwidth_kbps: Optional[float] = None
    description: str = ""


@dataclass
class PacketMetrics:
    """Tracks packet delivery metrics"""
    sent: int = 0
    received: int = 0
    lost: int = 0
    duplicated: int = 0
    out_of_order: int = 0
    latencies: List[float] = field(default_factory=list)
    
    @property
    def average_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0
    
    @property
    def jitter(self) -> float:
        return statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0
    
    @property
    def loss_rate(self) -> float:
        return self.lost / self.sent if self.sent > 0 else 0
    
    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index] if index < len(sorted_latencies) else sorted_latencies[-1]


@dataclass
class Packet:
    """Represents a network packet"""
    id: int
    data: bytes
    timestamp: float
    size: int
    priority: int = 0


class NetworkConditionSimulator:
    """Simulates various network conditions for game testing"""
    
    # Predefined network conditions based on real-world scenarios
    CONDITIONS = {
        "PERFECT": NetworkCondition(
            name="Perfect LAN",
            latency_ms=1,
            jitter_ms=0,
            packet_loss_rate=0,
            bandwidth_kbps=1_000_000,
            description="Ideal LAN conditions"
        ),
        "FIBER": NetworkCondition(
            name="Fiber Broadband",
            latency_ms=5,
            jitter_ms=1,
            packet_loss_rate=0.0001,
            bandwidth_kbps=100_000,
            description="High-speed fiber connection"
        ),
        "CABLE": NetworkCondition(
            name="Cable Internet",
            latency_ms=20,
            jitter_ms=5,
            packet_loss_rate=0.001,
            bandwidth_kbps=50_000,
            description="Typical cable internet"
        ),
        "4G_GOOD": NetworkCondition(
            name="4G Good Signal",
            latency_ms=50,
            jitter_ms=10,
            packet_loss_rate=0.001,
            bandwidth_kbps=20_000,
            description="Good 4G mobile connection"
        ),
        "4G_POOR": NetworkCondition(
            name="4G Poor Signal",
            latency_ms=150,
            jitter_ms=50,
            packet_loss_rate=0.02,
            bandwidth_kbps=5_000,
            description="Poor 4G mobile connection"
        ),
        "3G": NetworkCondition(
            name="3G Mobile",
            latency_ms=200,
            jitter_ms=100,
            packet_loss_rate=0.05,
            bandwidth_kbps=2_000,
            description="3G mobile network"
        ),
        "SATELLITE": NetworkCondition(
            name="Satellite Internet",
            latency_ms=600,
            jitter_ms=20,
            packet_loss_rate=0.01,
            bandwidth_kbps=25_000,
            description="Satellite internet connection"
        ),
        "CONGESTED_WIFI": NetworkCondition(
            name="Congested WiFi",
            latency_ms=100,
            jitter_ms=150,
            packet_loss_rate=0.08,
            bandwidth_kbps=5_000,
            description="Overloaded WiFi network"
        ),
        "COMPETITIVE_GAMING": NetworkCondition(
            name="Competitive Gaming Acceptable",
            latency_ms=30,
            jitter_ms=5,
            packet_loss_rate=0.001,
            bandwidth_kbps=10_000,
            description="Maximum acceptable for competitive gaming"
        )
    }
    
    def __init__(self, condition: NetworkCondition = None):
        self.current_condition = condition or self.CONDITIONS["PERFECT"]
        self.packet_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = PacketMetrics()
        self.packet_id = 0
        self.is_active = False
        self.callbacks: Dict[str, List[Callable]] = {
            'packet_sent': [],
            'packet_delivered': [],
            'packet_lost': [],
            'condition_changed': []
        }
        self._bandwidth_limiter = None
        
    def set_condition(self, condition: str | NetworkCondition):
        """Set network condition"""
        if isinstance(condition, str):
            self.current_condition = self.CONDITIONS.get(condition, self.CONDITIONS["PERFECT"])
        else:
            self.current_condition = condition
            
        self._trigger_callbacks('condition_changed', self.current_condition)
        logger.info(f"Network condition changed to: {self.current_condition.name}")
        
    async def simulate_packet(self, data: bytes, priority: int = 0) -> Optional[bytes]:
        """Simulate sending a packet through the network"""
        packet = Packet(
            id=self.packet_id,
            data=data,
            timestamp=time.time(),
            size=len(data),
            priority=priority
        )
        self.packet_id += 1
        self.metrics.sent += 1
        
        self._trigger_callbacks('packet_sent', packet)
        
        # Simulate packet loss
        if random.random() < self.current_condition.packet_loss_rate:
            self.metrics.lost += 1
            self._trigger_callbacks('packet_lost', packet)
            return None
            
        # Calculate latency with jitter
        jitter = random.uniform(-self.current_condition.jitter_ms, self.current_condition.jitter_ms)
        actual_latency = max(0, self.current_condition.latency_ms + jitter)
        
        # Simulate bandwidth limitation
        if self.current_condition.bandwidth_kbps:
            transmission_time = (packet.size * 8) / (self.current_condition.bandwidth_kbps * 1000)
            await asyncio.sleep(transmission_time)
            
        # Schedule packet delivery
        await asyncio.sleep(actual_latency / 1000)
        
        # Simulate packet duplication (rare)
        if random.random() < 0.001:  # 0.1% chance
            self.metrics.duplicated += 1
            await self._deliver_packet(packet, actual_latency)
            
        return await self._deliver_packet(packet, actual_latency)
        
    async def _deliver_packet(self, packet: Packet, latency: float) -> bytes:
        """Deliver a packet and update metrics"""
        self.metrics.received += 1
        self.metrics.latencies.append(latency)
        
        # Keep only last 1000 latency samples for metrics
        if len(self.metrics.latencies) > 1000:
            self.metrics.latencies.pop(0)
            
        self._trigger_callbacks('packet_delivered', {
            'packet': packet,
            'latency': latency,
            'metrics': self.get_metrics()
        })
        
        return packet.data
        
    def get_metrics(self) -> Dict:
        """Get current network metrics"""
        return {
            'sent': self.metrics.sent,
            'received': self.metrics.received,
            'lost': self.metrics.lost,
            'duplicated': self.metrics.duplicated,
            'loss_rate': f"{self.metrics.loss_rate * 100:.2f}%",
            'average_latency': f"{self.metrics.average_latency:.2f}ms",
            'p95_latency': f"{self.metrics.p95_latency:.2f}ms",
            'jitter': f"{self.metrics.jitter:.2f}ms"
        }
        
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = PacketMetrics()
        
    def add_callback(self, event: str, callback: Callable):
        """Add event callback"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            
    def _trigger_callbacks(self, event: str, data: any):
        """Trigger callbacks for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
                
    async def simulate_dynamic_conditions(self, scenarios: List[Tuple[str, float]]):
        """Simulate changing network conditions over time"""
        for condition_name, duration in scenarios:
            self.set_condition(condition_name)
            await asyncio.sleep(duration)
            
    async def simulate_network_spike(self, duration: float, severity: float = 2.0):
        """Simulate a temporary network degradation"""
        original = self.current_condition
        
        # Create degraded condition
        degraded = NetworkCondition(
            name=f"{original.name} (Spike)",
            latency_ms=original.latency_ms * severity,
            jitter_ms=original.jitter_ms * severity * 2,
            packet_loss_rate=min(0.5, original.packet_loss_rate * severity * 10),
            bandwidth_kbps=original.bandwidth_kbps / severity if original.bandwidth_kbps else None
        )
        
        self.set_condition(degraded)
        await asyncio.sleep(duration)
        self.set_condition(original)


class GamePacketSimulator:
    """Simulates game-specific packet patterns"""
    
    def __init__(self, network_sim: NetworkConditionSimulator):
        self.network_sim = network_sim
        self.packet_types = {
            'player_position': {'size': 64, 'frequency': 60, 'priority': 1},
            'player_action': {'size': 32, 'frequency': 10, 'priority': 2},
            'world_state': {'size': 1024, 'frequency': 10, 'priority': 0},
            'chat_message': {'size': 256, 'frequency': 0.1, 'priority': 3},
            'voice_data': {'size': 128, 'frequency': 50, 'priority': 1}
        }
        
    async def simulate_game_traffic(self, duration: float, packet_types: List[str] = None):
        """Simulate realistic game traffic patterns"""
        if packet_types is None:
            packet_types = list(self.packet_types.keys())
            
        start_time = time.time()
        tasks = []
        
        for packet_type in packet_types:
            if packet_type in self.packet_types:
                task = asyncio.create_task(
                    self._generate_packet_stream(
                        packet_type,
                        duration,
                        **self.packet_types[packet_type]
                    )
                )
                tasks.append(task)
                
        await asyncio.gather(*tasks)
        
    async def _generate_packet_stream(self, packet_type: str, duration: float, 
                                    size: int, frequency: float, priority: int):
        """Generate a stream of packets for a specific type"""
        interval = 1.0 / frequency
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Add some variance to packet size
            actual_size = int(size * random.uniform(0.8, 1.2))
            data = bytes([random.randint(0, 255) for _ in range(actual_size)])
            
            await self.network_sim.simulate_packet(data, priority)
            await asyncio.sleep(interval)


# Example usage and testing
async def demo():
    """Demonstrate network simulation capabilities"""
    print("=== Epic Games Network Condition Simulator ===\n")
    
    # Create simulator
    sim = NetworkConditionSimulator()
    
    # Add monitoring callbacks
    def on_packet_lost(packet):
        print(f"❌ Packet {packet.id} lost!")
        
    def on_metrics_update(data):
        metrics = data['metrics']
        print(f"📊 Latency: {metrics['average_latency']} | Loss: {metrics['loss_rate']}")
        
    sim.add_callback('packet_lost', on_packet_lost)
    sim.add_callback('packet_delivered', on_metrics_update)
    
    # Test different network conditions
    print("Testing network conditions...")
    
    for condition_name in ["FIBER", "4G_GOOD", "SATELLITE", "CONGESTED_WIFI"]:
        print(f"\n--- Testing {condition_name} ---")
        sim.set_condition(condition_name)
        sim.reset_metrics()
        
        # Simulate game traffic
        game_sim = GamePacketSimulator(sim)
        await game_sim.simulate_game_traffic(duration=5.0)
        
        # Print final metrics
        metrics = sim.get_metrics()
        print(f"\nFinal metrics for {condition_name}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
            
    # Test dynamic conditions (simulating player movement)
    print("\n--- Testing Dynamic Conditions (Player moving through areas) ---")
    await sim.simulate_dynamic_conditions([
        ("FIBER", 5.0),
        ("4G_GOOD", 3.0),
        ("4G_POOR", 2.0),
        ("CONGESTED_WIFI", 3.0),
        ("FIBER", 5.0)
    ])
    
    # Test network spike
    print("\n--- Testing Network Spike ---")
    sim.set_condition("FIBER")
    print("Normal conditions for 3 seconds...")
    await asyncio.sleep(3)
    print("Network spike!")
    await sim.simulate_network_spike(duration=2.0, severity=5.0)
    print("Network recovered")


if __name__ == "__main__":
    asyncio.run(demo())