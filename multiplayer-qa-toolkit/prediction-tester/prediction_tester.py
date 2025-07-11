#!/usr/bin/env python3
"""
Client-Side Prediction and Server Reconciliation Tester
Epic Games QA Toolkit
"""

import asyncio
import time
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
import logging
from collections import deque
import math
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Vector3:
    """3D Vector for position/velocity"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def distance(self, other) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def to_dict(self):
        return {'x': self.x, 'y': self.y, 'z': self.z}


@dataclass
class PlayerInput:
    """Player input at a specific timestamp"""
    timestamp: float
    movement: Vector3
    actions: Dict[str, any] = field(default_factory=dict)
    sequence_number: int = 0


@dataclass
class GameState:
    """Complete game state at a point in time"""
    timestamp: float
    player_position: Vector3
    player_velocity: Vector3
    player_health: float = 100.0
    sequence_number: int = 0
    checksum: Optional[int] = None
    
    def calculate_checksum(self) -> int:
        """Calculate state checksum for validation"""
        # Simple checksum for demo - in production use CRC32 or similar
        data = f"{self.player_position.x:.2f}{self.player_position.y:.2f}{self.player_position.z:.2f}"
        return hash(data) & 0xFFFFFFFF


@dataclass
class PredictionMetrics:
    """Metrics for prediction accuracy"""
    position_errors: List[float] = field(default_factory=list)
    velocity_errors: List[float] = field(default_factory=list)
    rollback_count: int = 0
    prediction_hits: int = 0
    prediction_misses: int = 0
    max_position_error: float = 0.0
    average_position_error: float = 0.0
    desync_events: int = 0
    
    def update(self):
        """Update calculated metrics"""
        if self.position_errors:
            self.average_position_error = np.mean(self.position_errors)
            self.max_position_error = max(self.position_errors)


class ClientPrediction:
    """Client-side prediction system"""
    
    def __init__(self, tick_rate: int = 60, max_prediction_time: float = 0.5):
        self.tick_rate = tick_rate
        self.tick_interval = 1.0 / tick_rate
        self.max_prediction_time = max_prediction_time
        
        # State management
        self.current_state = GameState(
            timestamp=time.time(),
            player_position=Vector3(),
            player_velocity=Vector3()
        )
        self.state_buffer: deque = deque(maxlen=120)  # 2 seconds at 60 tick
        self.input_buffer: deque = deque(maxlen=120)
        self.pending_inputs: deque = deque()
        
        # Metrics
        self.metrics = PredictionMetrics()
        
    def apply_input(self, input: PlayerInput, state: GameState) -> GameState:
        """Apply input to game state (client-side physics)"""
        # Simple physics simulation
        dt = self.tick_interval
        
        # Update velocity based on input
        acceleration = input.movement * 10.0  # Movement speed
        new_velocity = state.player_velocity + acceleration * dt
        
        # Apply friction
        new_velocity = new_velocity * 0.9
        
        # Update position
        new_position = state.player_position + new_velocity * dt
        
        # Create new state
        new_state = GameState(
            timestamp=input.timestamp,
            player_position=new_position,
            player_velocity=new_velocity,
            player_health=state.player_health,
            sequence_number=input.sequence_number
        )
        new_state.checksum = new_state.calculate_checksum()
        
        return new_state
    
    def predict_movement(self, input: PlayerInput) -> GameState:
        """Predict movement based on input"""
        # Store input for later reconciliation
        self.input_buffer.append(input)
        self.pending_inputs.append(input)
        
        # Apply prediction
        predicted_state = self.apply_input(input, self.current_state)
        self.current_state = predicted_state
        self.state_buffer.append(predicted_state)
        
        return predicted_state
    
    def reconcile_with_server(self, server_state: GameState):
        """Reconcile client state with authoritative server state"""
        # Find the matching state in our buffer
        matching_state = None
        for state in self.state_buffer:
            if state.sequence_number == server_state.sequence_number:
                matching_state = state
                break
                
        if not matching_state:
            logger.warning(f"No matching state for sequence {server_state.sequence_number}")
            self.metrics.desync_events += 1
            return
            
        # Calculate prediction error
        position_error = matching_state.player_position.distance(server_state.player_position)
        self.metrics.position_errors.append(position_error)
        
        # Check if rollback is needed
        error_threshold = 0.1  # 10cm
        if position_error > error_threshold:
            self.metrics.rollback_count += 1
            self.metrics.prediction_misses += 1
            
            # Rollback to server state
            self.current_state = server_state
            
            # Replay inputs after the server state
            inputs_to_replay = [
                inp for inp in self.pending_inputs 
                if inp.sequence_number > server_state.sequence_number
            ]
            
            for input in inputs_to_replay:
                self.current_state = self.apply_input(input, self.current_state)
                
            logger.info(f"Rollback performed: error={position_error:.3f}, replayed {len(inputs_to_replay)} inputs")
        else:
            self.metrics.prediction_hits += 1
            
        # Clean up acknowledged inputs
        self.pending_inputs = deque([
            inp for inp in self.pending_inputs 
            if inp.sequence_number > server_state.sequence_number
        ])
        
        self.metrics.update()


class ServerSimulation:
    """Simulates authoritative game server"""
    
    def __init__(self, tick_rate: int = 30, process_delay: float = 0.0):
        self.tick_rate = tick_rate
        self.tick_interval = 1.0 / tick_rate
        self.process_delay = process_delay
        
        self.current_state = GameState(
            timestamp=time.time(),
            player_position=Vector3(),
            player_velocity=Vector3()
        )
        self.processed_inputs: Dict[int, PlayerInput] = {}
        
    async def process_input(self, input: PlayerInput) -> GameState:
        """Process input on server with network delay"""
        # Simulate processing delay
        if self.process_delay > 0:
            await asyncio.sleep(self.process_delay)
            
        # Check for duplicate/out-of-order inputs
        if input.sequence_number in self.processed_inputs:
            logger.warning(f"Duplicate input: {input.sequence_number}")
            return self.current_state
            
        # Apply input using same physics as client
        client_pred = ClientPrediction(self.tick_rate)
        new_state = client_pred.apply_input(input, self.current_state)
        
        # Add server-specific validation
        new_state = self._validate_state(new_state)
        
        self.current_state = new_state
        self.processed_inputs[input.sequence_number] = input
        
        return new_state
        
    def _validate_state(self, state: GameState) -> GameState:
        """Server-side validation and anti-cheat"""
        # Clamp position to world bounds
        world_size = 1000.0
        state.player_position.x = max(-world_size, min(world_size, state.player_position.x))
        state.player_position.y = max(0, min(100, state.player_position.y))  # Height limit
        state.player_position.z = max(-world_size, min(world_size, state.player_position.z))
        
        # Validate velocity (anti-speed hack)
        max_speed = 20.0
        speed = math.sqrt(
            state.player_velocity.x**2 + 
            state.player_velocity.y**2 + 
            state.player_velocity.z**2
        )
        if speed > max_speed:
            scale = max_speed / speed
            state.player_velocity = state.player_velocity * scale
            
        return state


class PredictionTestFramework:
    """Framework for testing prediction accuracy under various conditions"""
    
    def __init__(self):
        self.client = ClientPrediction()
        self.server = ServerSimulation()
        self.sequence_number = 0
        self.test_results = []
        
    async def run_test_scenario(self, 
                               duration: float,
                               latency_ms: float,
                               latency_jitter_ms: float,
                               packet_loss_rate: float,
                               input_pattern: str = "circle") -> Dict:
        """Run a complete test scenario"""
        logger.info(f"Starting test: latency={latency_ms}ms, jitter={latency_jitter_ms}ms, loss={packet_loss_rate*100}%")
        
        # Reset systems
        self.client = ClientPrediction()
        self.server = ServerSimulation()
        self.sequence_number = 0
        
        start_time = time.time()
        last_input_time = start_time
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Generate input at client tick rate
            if current_time - last_input_time >= self.client.tick_interval:
                # Generate movement input based on pattern
                input = self._generate_input(current_time - start_time, input_pattern)
                
                # Client prediction
                predicted_state = self.client.predict_movement(input)
                
                # Simulate sending to server
                if await self._simulate_network(input, latency_ms, latency_jitter_ms, packet_loss_rate):
                    # Server processing
                    server_state = await self.server.process_input(input)
                    
                    # Simulate server response with network delay
                    response_latency = latency_ms + np.random.uniform(-latency_jitter_ms, latency_jitter_ms)
                    await asyncio.sleep(response_latency / 1000.0)
                    
                    # Client reconciliation
                    self.client.reconcile_with_server(server_state)
                    
                last_input_time = current_time
                
            await asyncio.sleep(0.001)  # 1ms sleep to prevent CPU spinning
            
        # Compile results
        metrics = self.client.metrics
        metrics.update()
        
        accuracy_rate = metrics.prediction_hits / (metrics.prediction_hits + metrics.prediction_misses) \
                       if (metrics.prediction_hits + metrics.prediction_misses) > 0 else 0
                       
        results = {
            'test_config': {
                'duration': duration,
                'latency_ms': latency_ms,
                'jitter_ms': latency_jitter_ms,
                'packet_loss_rate': packet_loss_rate,
                'input_pattern': input_pattern
            },
            'metrics': {
                'average_position_error': metrics.average_position_error,
                'max_position_error': metrics.max_position_error,
                'rollback_count': metrics.rollback_count,
                'rollback_rate': metrics.rollback_count / self.sequence_number if self.sequence_number > 0 else 0,
                'prediction_accuracy': accuracy_rate,
                'desync_events': metrics.desync_events,
                'total_inputs': self.sequence_number
            }
        }
        
        self.test_results.append(results)
        return results
        
    def _generate_input(self, elapsed_time: float, pattern: str) -> PlayerInput:
        """Generate movement input based on pattern"""
        self.sequence_number += 1
        
        if pattern == "circle":
            # Circular movement
            angle = elapsed_time * 2.0  # 2 radians per second
            movement = Vector3(
                x=math.cos(angle),
                y=0,
                z=math.sin(angle)
            )
        elif pattern == "zigzag":
            # Zigzag movement
            movement = Vector3(
                x=math.sin(elapsed_time * 3),
                y=0,
                z=1.0
            )
        elif pattern == "random":
            # Random movement
            movement = Vector3(
                x=np.random.uniform(-1, 1),
                y=0,
                z=np.random.uniform(-1, 1)
            )
        else:
            # Static
            movement = Vector3()
            
        return PlayerInput(
            timestamp=time.time(),
            movement=movement,
            sequence_number=self.sequence_number
        )
        
    async def _simulate_network(self, input: PlayerInput, latency_ms: float, 
                               jitter_ms: float, packet_loss_rate: float) -> bool:
        """Simulate network conditions"""
        # Packet loss
        if np.random.random() < packet_loss_rate:
            return False
            
        # Latency with jitter
        actual_latency = latency_ms + np.random.uniform(-jitter_ms, jitter_ms)
        actual_latency = max(0, actual_latency)  # Ensure non-negative
        
        await asyncio.sleep(actual_latency / 1000.0)
        return True
        
    def generate_report(self) -> str:
        """Generate test report"""
        report = "=== Client-Side Prediction Test Report ===\n\n"
        
        for i, result in enumerate(self.test_results):
            config = result['test_config']
            metrics = result['metrics']
            
            report += f"Test {i+1}:\n"
            report += f"  Configuration:\n"
            report += f"    - Latency: {config['latency_ms']}ms (±{config['jitter_ms']}ms)\n"
            report += f"    - Packet Loss: {config['packet_loss_rate']*100:.1f}%\n"
            report += f"    - Pattern: {config['input_pattern']}\n"
            report += f"  Results:\n"
            report += f"    - Avg Position Error: {metrics['average_position_error']:.3f} units\n"
            report += f"    - Max Position Error: {metrics['max_position_error']:.3f} units\n"
            report += f"    - Rollback Rate: {metrics['rollback_rate']*100:.1f}%\n"
            report += f"    - Prediction Accuracy: {metrics['prediction_accuracy']*100:.1f}%\n"
            report += f"    - Desync Events: {metrics['desync_events']}\n"
            
            # Quality assessment
            if metrics['average_position_error'] < 0.1 and metrics['rollback_rate'] < 0.05:
                report += "    - Quality: ✅ EXCELLENT\n"
            elif metrics['average_position_error'] < 0.5 and metrics['rollback_rate'] < 0.1:
                report += "    - Quality: ⚠️  GOOD\n"
            else:
                report += "    - Quality: ❌ POOR\n"
                
            report += "\n"
            
        return report


# Visualization helper
def create_prediction_visualization(test_framework: PredictionTestFramework):
    """Create visualization of prediction accuracy"""
    try:
        import matplotlib.pyplot as plt
        
        # Extract data
        latencies = [r['test_config']['latency_ms'] for r in test_framework.test_results]
        avg_errors = [r['metrics']['average_position_error'] for r in test_framework.test_results]
        rollback_rates = [r['metrics']['rollback_rate'] * 100 for r in test_framework.test_results]
        
        # Create plots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Position error vs latency
        ax1.plot(latencies, avg_errors, 'b-o', label='Avg Position Error')
        ax1.set_xlabel('Latency (ms)')
        ax1.set_ylabel('Position Error (units)')
        ax1.set_title('Prediction Error vs Network Latency')
        ax1.grid(True)
        ax1.legend()
        
        # Rollback rate vs latency
        ax2.plot(latencies, rollback_rates, 'r-s', label='Rollback Rate')
        ax2.set_xlabel('Latency (ms)')
        ax2.set_ylabel('Rollback Rate (%)')
        ax2.set_title('Rollback Frequency vs Network Latency')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('prediction_analysis.png')
        logger.info("Visualization saved to prediction_analysis.png")
        
    except ImportError:
        logger.warning("Matplotlib not available for visualization")


# Demo and testing
async def demo():
    """Demonstrate prediction testing capabilities"""
    print("=== Epic Games Client-Side Prediction Tester ===\n")
    
    framework = PredictionTestFramework()
    
    # Test scenarios
    test_scenarios = [
        # (latency_ms, jitter_ms, packet_loss_rate, pattern)
        (20, 5, 0.0, "circle"),      # Good connection
        (50, 10, 0.01, "circle"),    # Average connection
        (100, 20, 0.02, "circle"),   # Poor connection
        (200, 50, 0.05, "circle"),   # Bad connection
        (50, 10, 0.01, "zigzag"),    # Different movement pattern
        (50, 10, 0.01, "random"),    # Random movement
    ]
    
    print("Running prediction accuracy tests...\n")
    
    for latency, jitter, loss, pattern in test_scenarios:
        result = await framework.run_test_scenario(
            duration=10.0,  # 10 second test
            latency_ms=latency,
            latency_jitter_ms=jitter,
            packet_loss_rate=loss,
            input_pattern=pattern
        )
        
        print(f"Test completed: {latency}ms latency, {pattern} pattern")
        print(f"  Average error: {result['metrics']['average_position_error']:.3f} units")
        print(f"  Rollback rate: {result['metrics']['rollback_rate']*100:.1f}%")
        print()
        
    # Generate report
    report = framework.generate_report()
    print("\n" + report)
    
    # Save detailed results
    with open('prediction_test_results.json', 'w') as f:
        json.dump(framework.test_results, f, indent=2)
    print("Detailed results saved to prediction_test_results.json")
    
    # Create visualization
    create_prediction_visualization(framework)


if __name__ == "__main__":
    asyncio.run(demo())