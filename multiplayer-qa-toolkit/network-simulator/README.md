# Network Condition Simulator

A comprehensive network condition simulator for testing multiplayer games under various real-world network scenarios.

## Overview

This tool simulates realistic network conditions including latency, jitter, packet loss, and bandwidth limitations. It's designed specifically for testing multiplayer games and can replicate conditions from perfect LAN to satellite internet.

## Features

- **Predefined Network Profiles**: 10+ real-world network conditions
- **Dynamic Condition Changes**: Simulate players moving between network types
- **Packet-Level Simulation**: Track individual packet delivery and loss
- **Game Traffic Patterns**: Simulate realistic game packet types and frequencies
- **Network Spikes**: Test behavior during temporary network degradation
- **Comprehensive Metrics**: Real-time tracking of latency, jitter, packet loss

## Installation

```bash
cd network-simulator
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
import asyncio
from network_simulator import NetworkConditionSimulator

async def test_network():
    # Create simulator
    sim = NetworkConditionSimulator()
    
    # Set network condition
    sim.set_condition("4G_GOOD")
    
    # Simulate sending a packet
    data = b"Player position update"
    result = await sim.simulate_packet(data)
    
    if result:
        print("Packet delivered!")
    else:
        print("Packet lost!")
    
    # Get metrics
    metrics = sim.get_metrics()
    print(f"Average latency: {metrics['average_latency']}")
    print(f"Packet loss: {metrics['loss_rate']}")

asyncio.run(test_network())
```

### Simulating Game Traffic

```python
from network_simulator import NetworkConditionSimulator, GamePacketSimulator

async def simulate_game():
    sim = NetworkConditionSimulator()
    game_sim = GamePacketSimulator(sim)
    
    # Set competitive gaming conditions
    sim.set_condition("COMPETITIVE_GAMING")
    
    # Simulate 60 seconds of game traffic
    await game_sim.simulate_game_traffic(
        duration=60.0,
        packet_types=['player_position', 'player_action', 'voice_data']
    )
    
    print(sim.get_metrics())

asyncio.run(simulate_game())
```

## Network Conditions

| Condition | Latency | Jitter | Loss Rate | Bandwidth | Use Case |
|-----------|---------|--------|-----------|-----------|----------|
| PERFECT | 1ms | 0ms | 0% | 1Gbps | LAN/Testing |
| FIBER | 5ms | 1ms | 0.01% | 100Mbps | Home fiber |
| CABLE | 20ms | 5ms | 0.1% | 50Mbps | Cable internet |
| 4G_GOOD | 50ms | 10ms | 0.1% | 20Mbps | Good mobile |
| 4G_POOR | 150ms | 50ms | 2% | 5Mbps | Poor mobile |
| 3G | 200ms | 100ms | 5% | 2Mbps | 3G network |
| SATELLITE | 600ms | 20ms | 1% | 25Mbps | Satellite |
| CONGESTED_WIFI | 100ms | 150ms | 8% | 5Mbps | Busy WiFi |
| COMPETITIVE_GAMING | 30ms | 5ms | 0.1% | 10Mbps | Max competitive |

## Advanced Features

### Dynamic Network Conditions

Simulate a player moving through different network environments:

```python
# Player moves from home WiFi to mobile network
await sim.simulate_dynamic_conditions([
    ("FIBER", 300.0),      # 5 minutes at home
    ("4G_GOOD", 120.0),    # 2 minutes transition
    ("4G_POOR", 180.0),    # 3 minutes poor signal
    ("4G_GOOD", 300.0),    # 5 minutes good signal
])
```

### Network Spikes

Test resilience to temporary network issues:

```python
# Normal conditions with a 5-second severe spike
await sim.simulate_network_spike(duration=5.0, severity=3.0)
```

### Custom Callbacks

Monitor specific events:

```python
def on_packet_lost(packet):
    print(f"Lost packet {packet.id} at {packet.timestamp}")
    
def on_high_latency(data):
    if data['latency'] > 100:
        print(f"High latency detected: {data['latency']}ms")

sim.add_callback('packet_lost', on_packet_lost)
sim.add_callback('packet_delivered', on_high_latency)
```

## Testing Scenarios

### 1. Competitive Match Simulation

```python
async def test_competitive_match():
    sim = NetworkConditionSimulator()
    
    # Start with good conditions
    sim.set_condition("COMPETITIVE_GAMING")
    
    # Simulate 10 minute match with occasional spikes
    for i in range(10):
        await game_sim.simulate_game_traffic(duration=50.0)
        
        # Random network spike every few minutes
        if random.random() < 0.3:
            await sim.simulate_network_spike(duration=2.0, severity=2.0)
        
        await asyncio.sleep(10)
    
    # Analyze match quality
    metrics = sim.get_metrics()
    if float(metrics['average_latency'].rstrip('ms')) < 50 and \
       float(metrics['loss_rate'].rstrip('%')) < 1:
        print("✅ Match quality: GOOD")
    else:
        print("❌ Match quality: POOR")
```

### 2. Mobile Player Testing

```python
async def test_mobile_player():
    sim = NetworkConditionSimulator()
    
    # Simulate typical mobile session
    scenarios = [
        ("4G_GOOD", 120),     # Start with good signal
        ("4G_POOR", 30),      # Enter building
        ("CONGESTED_WIFI", 180),  # Connect to coffee shop WiFi
        ("4G_GOOD", 60),      # Leave on mobile
    ]
    
    for condition, duration in scenarios:
        sim.set_condition(condition)
        print(f"Testing {condition} for {duration}s")
        
        # Monitor for unplayable conditions
        await game_sim.simulate_game_traffic(duration=duration)
        
        metrics = sim.get_metrics()
        if float(metrics['p95_latency'].rstrip('ms')) > 200:
            print(f"⚠️  Warning: High latency in {condition}")
```

### 3. Stress Testing

```python
async def stress_test():
    sim = NetworkConditionSimulator()
    
    # Test worst-case scenarios
    worst_conditions = ["3G", "SATELLITE", "CONGESTED_WIFI"]
    
    for condition in worst_conditions:
        sim.set_condition(condition)
        sim.reset_metrics()
        
        # Generate heavy traffic
        tasks = []
        for _ in range(5):  # 5 concurrent players
            task = game_sim.simulate_game_traffic(duration=30.0)
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        
        # Check if game is playable
        metrics = sim.get_metrics()
        print(f"{condition}: {metrics}")
```

## Integration with Game Testing

### Example: Fortnite-style Battle Royale Testing

```python
class BattleRoyaleNetworkTest:
    def __init__(self):
        self.sim = NetworkConditionSimulator()
        self.game_sim = GamePacketSimulator(self.sim)
        
    async def simulate_match(self, player_count=100):
        # Early game - all players active
        print("🎮 Early game - 100 players")
        self.sim.set_condition("COMPETITIVE_GAMING")
        
        # High packet rate with all players
        for _ in range(player_count):
            await self.sim.simulate_packet(b"player_update", priority=1)
            
        # Mid game - 50 players, some network variation
        print("🎮 Mid game - 50 players")
        await self.simulate_with_network_variety(50)
        
        # End game - 10 players, critical performance needed
        print("🎮 End game - 10 players")
        self.sim.set_condition("FIBER")  # Best conditions for final fight
        await self.game_sim.simulate_game_traffic(duration=120)
        
    async def simulate_with_network_variety(self, player_count):
        # Simulate players with different network conditions
        conditions = ["FIBER", "CABLE", "4G_GOOD", "4G_POOR", "CONGESTED_WIFI"]
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]
        
        for _ in range(player_count):
            condition = random.choices(conditions, weights=weights)[0]
            self.sim.set_condition(condition)
            await self.sim.simulate_packet(b"player_update")
```

## Metrics and Analysis

The simulator provides detailed metrics:

- **Sent**: Total packets sent
- **Received**: Total packets successfully delivered
- **Lost**: Packets lost due to network conditions
- **Duplicated**: Packets received multiple times
- **Loss Rate**: Percentage of packets lost
- **Average Latency**: Mean delivery time
- **P95 Latency**: 95th percentile latency
- **Jitter**: Variation in latency

## Best Practices

1. **Reset Metrics Between Tests**: Call `sim.reset_metrics()` for clean measurements
2. **Use Appropriate Durations**: Test for at least 30 seconds for stable metrics
3. **Monitor P95 Latency**: More important than average for player experience
4. **Test Edge Cases**: Always include worst-case scenarios
5. **Simulate Real Patterns**: Use game-specific packet types and frequencies

## Troubleshooting

### High CPU Usage
- Reduce packet frequency in `GamePacketSimulator`
- Increase sleep intervals between packets

### Inaccurate Metrics
- Ensure sufficient test duration (>30s)
- Check that metrics are reset between tests
- Verify packet sizes match your game

### Memory Issues
- Metrics keep only last 1000 latency samples
- Clear callbacks when done testing

## Future Enhancements

- [ ] Packet reordering simulation
- [ ] Bandwidth burst/throttling patterns  
- [ ] Geographic routing simulation
- [ ] ISP-specific behavior patterns
- [ ] WebRTC support for voice chat testing