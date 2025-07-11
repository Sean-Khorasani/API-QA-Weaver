# Client-Side Prediction & Server Reconciliation Tester

A comprehensive testing framework for validating client-side prediction accuracy and server reconciliation in multiplayer games.

## Overview

This tool simulates client-side prediction and server reconciliation to measure prediction accuracy, rollback frequency, and desync events under various network conditions. It's essential for ensuring smooth gameplay in fast-paced multiplayer games.

## Features

- **Accurate Physics Simulation**: Matching client and server physics
- **Network Condition Simulation**: Latency, jitter, and packet loss
- **Multiple Movement Patterns**: Circle, zigzag, random, static
- **Comprehensive Metrics**: Position error, rollback rate, prediction accuracy
- **Desync Detection**: Automatic detection of state divergence
- **Visual Analysis**: Graphs showing prediction performance

## Installation

```bash
cd prediction-tester
pip install -r requirements.txt
```

## Quick Start

### Basic Test

```python
import asyncio
from prediction_tester import PredictionTestFramework

async def test_prediction():
    framework = PredictionTestFramework()
    
    # Run a simple test
    result = await framework.run_test_scenario(
        duration=30.0,           # 30 second test
        latency_ms=50,          # 50ms latency
        latency_jitter_ms=10,   # ±10ms jitter
        packet_loss_rate=0.01,  # 1% packet loss
        input_pattern="circle"  # Circular movement
    )
    
    print(f"Average prediction error: {result['metrics']['average_position_error']:.3f} units")
    print(f"Rollback rate: {result['metrics']['rollback_rate']*100:.1f}%")
    print(f"Prediction accuracy: {result['metrics']['prediction_accuracy']*100:.1f}%")

asyncio.run(test_prediction())
```

### Running Full Test Suite

```bash
python prediction_tester.py
```

This runs comprehensive tests across different network conditions and generates:
- Console report with quality assessments
- `prediction_test_results.json` with detailed metrics
- `prediction_analysis.png` with visualization

## Understanding the System

### Client-Side Prediction

The client predicts player movement locally to provide immediate feedback:

```python
# Client applies input immediately
predicted_state = client.predict_movement(player_input)
# Display predicted position to player
render_player_at(predicted_state.position)
```

### Server Reconciliation

When the server's authoritative state arrives, the client reconciles:

```python
# Server sends authoritative state
server_state = await receive_from_server()

# Client checks prediction accuracy
if prediction_error > threshold:
    # Rollback to server state
    client.rollback_to(server_state)
    # Replay unacknowledged inputs
    client.replay_pending_inputs()
```

## Test Scenarios

### 1. Network Quality Tests

Test prediction accuracy across different network conditions:

```python
# Good home connection
await framework.run_test_scenario(
    duration=60.0,
    latency_ms=20,
    latency_jitter_ms=5,
    packet_loss_rate=0.001,
    input_pattern="circle"
)

# Mobile 4G connection
await framework.run_test_scenario(
    duration=60.0,
    latency_ms=80,
    latency_jitter_ms=20,
    packet_loss_rate=0.02,
    input_pattern="circle"
)

# Poor connection
await framework.run_test_scenario(
    duration=60.0,
    latency_ms=200,
    latency_jitter_ms=50,
    packet_loss_rate=0.05,
    input_pattern="circle"
)
```

### 2. Movement Pattern Tests

Test different player movement patterns:

```python
patterns = ["circle", "zigzag", "random", "static"]

for pattern in patterns:
    result = await framework.run_test_scenario(
        duration=30.0,
        latency_ms=50,
        latency_jitter_ms=10,
        packet_loss_rate=0.01,
        input_pattern=pattern
    )
    print(f"{pattern}: {result['metrics']['average_position_error']:.3f} error")
```

### 3. Stress Testing

Test extreme conditions:

```python
# High latency
stress_result = await framework.run_test_scenario(
    duration=30.0,
    latency_ms=500,     # 500ms latency
    latency_jitter_ms=100,
    packet_loss_rate=0.1,  # 10% loss
    input_pattern="random"
)

if stress_result['metrics']['desync_events'] > 0:
    print(f"⚠️ {stress_result['metrics']['desync_events']} desyncs detected!")
```

## Metrics Explained

### Position Error
- **Average**: Mean distance between predicted and actual position
- **Max**: Largest single prediction error
- **Threshold**: <0.1 units for competitive games

### Rollback Rate
- Percentage of predictions that required correction
- **Good**: <5% rollbacks
- **Acceptable**: <10% rollbacks
- **Poor**: >10% rollbacks

### Prediction Accuracy
- Percentage of predictions within acceptable error threshold
- **Target**: >95% for smooth gameplay

### Desync Events
- Complete state divergence requiring full resync
- **Target**: 0 desyncs in normal conditions

## Advanced Configuration

### Custom Physics

Modify physics parameters for your game:

```python
class CustomClientPrediction(ClientPrediction):
    def apply_input(self, input, state):
        # Custom physics implementation
        dt = self.tick_interval
        
        # Your game's movement physics
        acceleration = input.movement * 15.0  # Faster movement
        new_velocity = state.player_velocity + acceleration * dt
        
        # Custom friction
        new_velocity = new_velocity * 0.95
        
        # Gravity for jumping games
        if state.player_position.y > 0:
            new_velocity.y -= 9.8 * dt
            
        return GameState(...)
```

### Server Validation

Add custom server-side validation:

```python
class CustomServerSimulation(ServerSimulation):
    def _validate_state(self, state):
        # Anti-cheat validation
        if self._is_teleporting(state):
            logger.warning("Teleport detected!")
            return self.last_valid_state
            
        # Game-specific rules
        if self._in_forbidden_area(state.player_position):
            state = self._push_to_valid_area(state)
            
        return state
```

## Testing Best Practices

### 1. Baseline Testing
Always establish baseline metrics with perfect network conditions:

```python
baseline = await framework.run_test_scenario(
    duration=60.0,
    latency_ms=0,
    latency_jitter_ms=0,
    packet_loss_rate=0,
    input_pattern="circle"
)
```

### 2. Incremental Testing
Test incrementally worse conditions:

```python
latencies = [0, 20, 50, 100, 200, 500]
for latency in latencies:
    result = await framework.run_test_scenario(
        duration=30.0,
        latency_ms=latency,
        latency_jitter_ms=latency * 0.2,
        packet_loss_rate=0.01,
        input_pattern="circle"
    )
```

### 3. Long Duration Tests
Run extended tests to catch edge cases:

```python
# 10-minute stress test
long_test = await framework.run_test_scenario(
    duration=600.0,  # 10 minutes
    latency_ms=100,
    latency_jitter_ms=50,
    packet_loss_rate=0.02,
    input_pattern="random"
)
```

## Integration Examples

### Fortnite-Style Building System

```python
@dataclass
class BuildingInput(PlayerInput):
    build_type: str = None  # wall, ramp, floor
    build_position: Vector3 = None
    
class FortnitePredictionTest(PredictionTestFramework):
    def _generate_input(self, elapsed_time, pattern):
        input = super()._generate_input(elapsed_time, pattern)
        
        # Add building actions
        if pattern == "build_fight":
            if int(elapsed_time) % 2 == 0:
                input.build_type = "wall"
                input.build_position = input.movement * 2.0
                
        return input
```

### Rocket League Ball Prediction

```python
class RocketLeaguePrediction(ClientPrediction):
    def __init__(self):
        super().__init__(tick_rate=120)  # Higher tick rate
        self.ball_position = Vector3()
        self.ball_velocity = Vector3()
        
    def predict_ball_physics(self, dt):
        # Ball physics with gravity and bounce
        self.ball_velocity.y -= 650 * dt  # Gravity
        self.ball_position += self.ball_velocity * dt
        
        # Bounce off ground
        if self.ball_position.y <= 0:
            self.ball_position.y = 0
            self.ball_velocity.y *= -0.6  # Bounce damping
```

## Troubleshooting

### High Rollback Rate
- Check if client and server physics match exactly
- Verify tick rates are appropriate
- Consider increasing error threshold

### Frequent Desyncs
- Check for floating point determinism issues
- Verify state checksums
- Look for unhandled edge cases

### Poor Prediction Accuracy
- Tune prediction algorithm for your game
- Consider input buffering strategies
- Implement interpolation for smoother corrections

## Performance Considerations

### CPU Usage
- Adjust tick rates based on game requirements
- Use efficient physics calculations
- Implement spatial partitioning for complex scenes

### Memory Usage
- Limit state buffer size (default: 120 states)
- Clear old pending inputs regularly
- Use object pooling for state objects

## Visualization and Reporting

### Generate Custom Reports

```python
def generate_competitive_report(results):
    report = "Competitive Viability Analysis\n"
    
    for result in results:
        metrics = result['metrics']
        latency = result['test_config']['latency_ms']
        
        viable = (
            metrics['average_position_error'] < 0.1 and
            metrics['rollback_rate'] < 0.05 and
            metrics['desync_events'] == 0
        )
        
        status = "✅ VIABLE" if viable else "❌ NOT VIABLE"
        report += f"{latency}ms: {status}\n"
        
    return report
```

### Export for Analysis

```python
import pandas as pd

# Convert results to DataFrame
df = pd.DataFrame([
    {
        'latency': r['test_config']['latency_ms'],
        'avg_error': r['metrics']['average_position_error'],
        'rollbacks': r['metrics']['rollback_rate']
    }
    for r in framework.test_results
])

# Export to CSV
df.to_csv('prediction_analysis.csv', index=False)
```

## Future Enhancements

- [ ] Multi-player prediction testing
- [ ] Interpolation testing
- [ ] Lag compensation validation
- [ ] Machine learning for prediction optimization
- [ ] VR-specific prediction testing