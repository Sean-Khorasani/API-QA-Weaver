#!/usr/bin/env python3
"""
Lag Compensation Testing Framework
Epic Games QA Toolkit
"""

import asyncio
import time
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Deque
from collections import deque
import logging
import math
import json
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HitResult(Enum):
    """Hit detection results"""
    HIT = "hit"
    MISS = "miss"
    REJECTED = "rejected"  # Server rejected due to invalid lag compensation
    INVALID = "invalid"    # Invalid shot (e.g., through wall)


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
    
    def normalize(self):
        length = self.distance(Vector3(0, 0, 0))
        if length > 0:
            return Vector3(self.x/length, self.y/length, self.z/length)
        return Vector3(0, 0, 0)


@dataclass
class Player:
    """Player state for hit detection"""
    id: str
    position: Vector3
    velocity: Vector3
    hitbox_radius: float = 0.5  # meters
    health: float = 100.0
    
    def get_hitbox_bounds(self) -> Tuple[Vector3, Vector3]:
        """Get axis-aligned bounding box"""
        min_bound = Vector3(
            self.position.x - self.hitbox_radius,
            self.position.y - self.hitbox_radius * 2,  # Player height
            self.position.z - self.hitbox_radius
        )
        max_bound = Vector3(
            self.position.x + self.hitbox_radius,
            self.position.y + self.hitbox_radius * 0.5,  # Head
            self.position.z + self.hitbox_radius
        )
        return min_bound, max_bound


@dataclass 
class Shot:
    """Represents a shot/projectile"""
    shooter_id: str
    timestamp: float
    origin: Vector3
    direction: Vector3
    target_position: Vector3  # Where shooter aimed (visual position)
    shooter_latency: float
    shot_id: int
    weapon_type: str = "rifle"
    damage: float = 25.0


@dataclass
class PositionSnapshot:
    """Player position at a specific time"""
    timestamp: float
    player_id: str
    position: Vector3
    velocity: Vector3
    health: float


@dataclass
class LagCompensationMetrics:
    """Metrics for lag compensation accuracy"""
    total_shots: int = 0
    hits: int = 0
    misses: int = 0
    rejected: int = 0
    false_positives: int = 0  # Hit when shouldn't
    false_negatives: int = 0  # Miss when should hit
    
    avg_compensation_time: float = 0.0
    max_compensation_time: float = 0.0
    compensation_times: List[float] = field(default_factory=list)
    
    hit_registration_delays: List[float] = field(default_factory=list)
    
    def calculate_metrics(self) -> Dict:
        """Calculate derived metrics"""
        hit_rate = self.hits / self.total_shots if self.total_shots > 0 else 0
        rejection_rate = self.rejected / self.total_shots if self.total_shots > 0 else 0
        
        if self.compensation_times:
            self.avg_compensation_time = np.mean(self.compensation_times)
            self.max_compensation_time = max(self.compensation_times)
            
        avg_hit_delay = np.mean(self.hit_registration_delays) if self.hit_registration_delays else 0
        
        return {
            'hit_rate': hit_rate,
            'rejection_rate': rejection_rate,
            'false_positive_rate': self.false_positives / self.total_shots if self.total_shots > 0 else 0,
            'false_negative_rate': self.false_negatives / self.total_shots if self.total_shots > 0 else 0,
            'avg_compensation_time': self.avg_compensation_time,
            'max_compensation_time': self.max_compensation_time,
            'avg_hit_registration_delay': avg_hit_delay
        }


class PositionHistory:
    """Maintains history of player positions for rewinding"""
    
    def __init__(self, max_history_time: float = 1.0):
        self.max_history_time = max_history_time
        self.history: Dict[str, Deque[PositionSnapshot]] = {}
        
    def add_snapshot(self, player_id: str, snapshot: PositionSnapshot):
        """Add position snapshot for a player"""
        if player_id not in self.history:
            self.history[player_id] = deque()
            
        self.history[player_id].append(snapshot)
        
        # Remove old snapshots
        current_time = snapshot.timestamp
        while (self.history[player_id] and 
               current_time - self.history[player_id][0].timestamp > self.max_history_time):
            self.history[player_id].popleft()
            
    def get_position_at_time(self, player_id: str, timestamp: float) -> Optional[PositionSnapshot]:
        """Get interpolated position at specific time"""
        if player_id not in self.history or not self.history[player_id]:
            return None
            
        snapshots = self.history[player_id]
        
        # Find surrounding snapshots
        before = None
        after = None
        
        for snapshot in snapshots:
            if snapshot.timestamp <= timestamp:
                before = snapshot
            elif snapshot.timestamp > timestamp and after is None:
                after = snapshot
                break
                
        if not before:
            return None  # Time too far in past
            
        if not after:
            # Extrapolate forward from last known position
            dt = timestamp - before.timestamp
            if dt > 0.1:  # Don't extrapolate too far
                return None
                
            extrapolated_pos = before.position + before.velocity * dt
            return PositionSnapshot(
                timestamp=timestamp,
                player_id=player_id,
                position=extrapolated_pos,
                velocity=before.velocity,
                health=before.health
            )
            
        # Interpolate between snapshots
        t = (timestamp - before.timestamp) / (after.timestamp - before.timestamp)
        interpolated_pos = Vector3(
            before.position.x + (after.position.x - before.position.x) * t,
            before.position.y + (after.position.y - before.position.y) * t,
            before.position.z + (after.position.z - before.position.z) * t
        )
        
        return PositionSnapshot(
            timestamp=timestamp,
            player_id=player_id,
            position=interpolated_pos,
            velocity=before.velocity,  # Simple velocity, could interpolate
            health=before.health
        )


class LagCompensationSystem:
    """Server-side lag compensation system"""
    
    def __init__(self, max_compensation_time: float = 0.2, tick_rate: int = 60):
        self.max_compensation_time = max_compensation_time
        self.tick_rate = tick_rate
        self.position_history = PositionHistory(max_history_time=1.0)
        self.metrics = LagCompensationMetrics()
        self.current_server_time = 0.0
        
    def update_player_position(self, player: Player, timestamp: float):
        """Record player position for history"""
        snapshot = PositionSnapshot(
            timestamp=timestamp,
            player_id=player.id,
            position=player.position,
            velocity=player.velocity,
            health=player.health
        )
        self.position_history.add_snapshot(player.id, snapshot)
        self.current_server_time = timestamp
        
    def process_shot(self, shot: Shot, current_players: Dict[str, Player]) -> Tuple[HitResult, Optional[str]]:
        """Process shot with lag compensation"""
        self.metrics.total_shots += 1
        
        # Calculate when the shot actually happened from shooter's perspective
        shot_time = shot.timestamp - shot.shooter_latency
        compensation_time = self.current_server_time - shot_time
        
        self.metrics.compensation_times.append(compensation_time)
        
        # Check if compensation time is valid
        if compensation_time < 0:
            logger.warning(f"Shot from future: compensation_time={compensation_time}")
            self.metrics.rejected += 1
            return HitResult.REJECTED, None
            
        if compensation_time > self.max_compensation_time:
            logger.warning(f"Compensation time too large: {compensation_time}s")
            self.metrics.rejected += 1
            return HitResult.REJECTED, None
            
        # Rewind all players to shot time
        rewound_players = {}
        for player_id, player in current_players.items():
            if player_id == shot.shooter_id:
                continue  # Don't rewind shooter
                
            historical_pos = self.position_history.get_position_at_time(player_id, shot_time)
            if historical_pos:
                rewound_players[player_id] = Player(
                    id=player_id,
                    position=historical_pos.position,
                    velocity=historical_pos.velocity,
                    health=historical_pos.health
                )
            else:
                # No history, use current position (less accurate)
                rewound_players[player_id] = player
                
        # Perform hit detection with rewound positions
        hit_player_id = self._check_hit(shot, rewound_players)
        
        if hit_player_id:
            self.metrics.hits += 1
            self.metrics.hit_registration_delays.append(compensation_time)
            
            # Validate hit (check if player was actually there)
            if self._validate_hit(shot, hit_player_id, shot_time):
                return HitResult.HIT, hit_player_id
            else:
                self.metrics.false_positives += 1
                return HitResult.INVALID, None
        else:
            self.metrics.misses += 1
            
            # Check if this was a false negative
            if self._should_have_hit(shot, current_players):
                self.metrics.false_negatives += 1
                
            return HitResult.MISS, None
            
    def _check_hit(self, shot: Shot, players: Dict[str, Player]) -> Optional[str]:
        """Perform ray-cast hit detection"""
        best_hit_distance = float('inf')
        hit_player_id = None
        
        for player_id, player in players.items():
            # Ray-sphere intersection for simple hitbox
            ray_origin = shot.origin
            ray_dir = shot.direction.normalize()
            
            # Vector from ray origin to sphere center
            to_center = player.position - ray_origin
            
            # Project to_center onto ray direction
            projection_length = (
                to_center.x * ray_dir.x + 
                to_center.y * ray_dir.y + 
                to_center.z * ray_dir.z
            )
            
            if projection_length < 0:
                continue  # Player is behind shooter
                
            # Find closest point on ray to sphere center
            closest_point = ray_origin + ray_dir * projection_length
            
            # Check distance from closest point to sphere center
            distance_to_center = closest_point.distance(player.position)
            
            if distance_to_center <= player.hitbox_radius:
                # Hit detected
                if projection_length < best_hit_distance:
                    best_hit_distance = projection_length
                    hit_player_id = player_id
                    
        return hit_player_id
        
    def _validate_hit(self, shot: Shot, hit_player_id: str, shot_time: float) -> bool:
        """Validate that hit is legitimate (anti-cheat)"""
        # Check if player existed at that time
        historical_pos = self.position_history.get_position_at_time(hit_player_id, shot_time)
        if not historical_pos:
            return False
            
        # Check if player was alive
        if historical_pos.health <= 0:
            return False
            
        # Could add more validation:
        # - Line of sight checks
        # - Maximum shot distance
        # - Rate of fire limits
        
        return True
        
    def _should_have_hit(self, shot: Shot, current_players: Dict[str, Player]) -> bool:
        """Check if shot should have hit based on visual position"""
        # Simple check: was any player very close to where shooter aimed?
        for player in current_players.values():
            if player.id == shot.shooter_id:
                continue
                
            distance = shot.target_position.distance(player.position)
            if distance < player.hitbox_radius * 2:  # Generous check
                return True
                
        return False


class LagCompensationTester:
    """Framework for testing lag compensation"""
    
    def __init__(self):
        self.lag_comp = LagCompensationSystem()
        self.players: Dict[str, Player] = {}
        self.shot_id_counter = 0
        
    async def run_test_scenario(self,
                               num_players: int,
                               duration: float,
                               latency_range: Tuple[float, float],
                               movement_pattern: str = "random",
                               shots_per_second: float = 2.0) -> Dict:
        """Run a complete lag compensation test scenario"""
        
        logger.info(f"Starting test: {num_players} players, {duration}s, latency {latency_range}ms")
        
        # Initialize players
        self.players = {}
        for i in range(num_players):
            player = Player(
                id=f"player_{i}",
                position=Vector3(
                    x=np.random.uniform(-50, 50),
                    y=0,
                    z=np.random.uniform(-50, 50)
                ),
                velocity=Vector3()
            )
            self.players[player.id] = player
            
        # Reset metrics
        self.lag_comp.metrics = LagCompensationMetrics()
        
        # Run simulation
        start_time = time.time()
        last_update = start_time
        last_shot_time = start_time
        
        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_update
            
            # Update player positions
            if dt >= 1.0 / self.lag_comp.tick_rate:
                self._update_players(dt, movement_pattern)
                
                # Record positions in history
                for player in self.players.values():
                    self.lag_comp.update_player_position(player, current_time)
                    
                last_update = current_time
                
            # Generate shots
            if current_time - last_shot_time >= 1.0 / shots_per_second:
                await self._generate_shot(latency_range)
                last_shot_time = current_time
                
            await asyncio.sleep(0.001)  # Prevent CPU spinning
            
        # Calculate final metrics
        metrics = self.lag_comp.metrics.calculate_metrics()
        
        return {
            'test_config': {
                'num_players': num_players,
                'duration': duration,
                'latency_range': latency_range,
                'movement_pattern': movement_pattern,
                'shots_per_second': shots_per_second
            },
            'results': {
                'total_shots': self.lag_comp.metrics.total_shots,
                'hits': self.lag_comp.metrics.hits,
                'misses': self.lag_comp.metrics.misses,
                'rejected': self.lag_comp.metrics.rejected,
                **metrics
            }
        }
        
    def _update_players(self, dt: float, movement_pattern: str):
        """Update player positions based on movement pattern"""
        for player in self.players.values():
            if movement_pattern == "random":
                # Random walk
                player.velocity = Vector3(
                    x=np.random.uniform(-5, 5),
                    y=0,
                    z=np.random.uniform(-5, 5)
                )
            elif movement_pattern == "circle":
                # Circular movement
                angle = time.time() * 0.5
                radius = 20
                center_x = 0
                center_z = 0
                
                target_x = center_x + radius * math.cos(angle + hash(player.id) % 360)
                target_z = center_z + radius * math.sin(angle + hash(player.id) % 360)
                
                # Move towards target
                to_target = Vector3(target_x - player.position.x, 0, target_z - player.position.z)
                player.velocity = to_target * 0.1
                
            elif movement_pattern == "static":
                player.velocity = Vector3(0, 0, 0)
                
            # Update position
            player.position = player.position + player.velocity * dt
            
            # Keep players in bounds
            player.position.x = max(-100, min(100, player.position.x))
            player.position.z = max(-100, min(100, player.position.z))
            
    async def _generate_shot(self, latency_range: Tuple[float, float]):
        """Generate a shot from random player to random target"""
        if len(self.players) < 2:
            return
            
        # Select shooter and target
        player_ids = list(self.players.keys())
        shooter_id = np.random.choice(player_ids)
        target_id = np.random.choice([pid for pid in player_ids if pid != shooter_id])
        
        shooter = self.players[shooter_id]
        target = self.players[target_id]
        
        # Simulate network latency
        shooter_latency = np.random.uniform(latency_range[0], latency_range[1]) / 1000.0
        
        # Calculate shot direction (with some aiming error)
        direction = target.position - shooter.position
        direction = direction.normalize()
        
        # Add small aiming error
        aim_error = 0.05  # 5% error
        direction.x += np.random.uniform(-aim_error, aim_error)
        direction.z += np.random.uniform(-aim_error, aim_error)
        direction = direction.normalize()
        
        # Create shot
        shot = Shot(
            shooter_id=shooter_id,
            timestamp=time.time(),
            origin=shooter.position,
            direction=direction,
            target_position=target.position,
            shooter_latency=shooter_latency,
            shot_id=self.shot_id_counter
        )
        self.shot_id_counter += 1
        
        # Process shot with lag compensation
        result, hit_player_id = self.lag_comp.process_shot(shot, self.players)
        
        if result == HitResult.HIT:
            logger.debug(f"Hit! {shooter_id} -> {hit_player_id} (latency: {shooter_latency*1000:.0f}ms)")
        
    def generate_report(self, test_results: List[Dict]) -> str:
        """Generate comprehensive test report"""
        report = "=== Lag Compensation Test Report ===\n\n"
        
        for i, result in enumerate(test_results):
            config = result['test_config']
            metrics = result['results']
            
            report += f"Test {i+1}:\n"
            report += f"  Configuration:\n"
            report += f"    - Players: {config['num_players']}\n"
            report += f"    - Latency: {config['latency_range'][0]}-{config['latency_range'][1]}ms\n"
            report += f"    - Movement: {config['movement_pattern']}\n"
            report += f"    - Fire Rate: {config['shots_per_second']} shots/sec\n"
            
            report += f"  Results:\n"
            report += f"    - Total Shots: {metrics['total_shots']}\n"
            report += f"    - Hit Rate: {metrics['hit_rate']*100:.1f}%\n"
            report += f"    - Rejection Rate: {metrics['rejection_rate']*100:.1f}%\n"
            report += f"    - False Positives: {metrics['false_positive_rate']*100:.1f}%\n"
            report += f"    - False Negatives: {metrics['false_negative_rate']*100:.1f}%\n"
            report += f"    - Avg Compensation: {metrics['avg_compensation_time']*1000:.1f}ms\n"
            report += f"    - Max Compensation: {metrics['max_compensation_time']*1000:.1f}ms\n"
            
            # Quality assessment
            if metrics['hit_rate'] > 0.8 and metrics['rejection_rate'] < 0.05:
                report += "    - Quality: ✅ EXCELLENT\n"
            elif metrics['hit_rate'] > 0.6 and metrics['rejection_rate'] < 0.1:
                report += "    - Quality: ⚠️  GOOD\n"
            else:
                report += "    - Quality: ❌ POOR\n"
                
            report += "\n"
            
        return report


# Visualization helper
def create_lag_compensation_visualization(test_results: List[Dict]):
    """Create visualization of lag compensation performance"""
    try:
        import matplotlib.pyplot as plt
        
        # Extract data
        latencies = []
        hit_rates = []
        rejection_rates = []
        
        for result in test_results:
            avg_latency = np.mean(result['test_config']['latency_range'])
            latencies.append(avg_latency)
            hit_rates.append(result['results']['hit_rate'] * 100)
            rejection_rates.append(result['results']['rejection_rate'] * 100)
            
        # Create plots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Hit rate vs latency
        ax1.plot(latencies, hit_rates, 'g-o', label='Hit Rate', linewidth=2)
        ax1.set_xlabel('Average Latency (ms)')
        ax1.set_ylabel('Hit Rate (%)')
        ax1.set_title('Hit Registration vs Network Latency')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        ax1.legend()
        
        # Rejection rate vs latency
        ax2.plot(latencies, rejection_rates, 'r-s', label='Rejection Rate', linewidth=2)
        ax2.set_xlabel('Average Latency (ms)')
        ax2.set_ylabel('Rejection Rate (%)')
        ax2.set_title('Shot Rejection vs Network Latency')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('lag_compensation_analysis.png', dpi=150)
        logger.info("Visualization saved to lag_compensation_analysis.png")
        
    except ImportError:
        logger.warning("Matplotlib not available for visualization")


# Demo and testing
async def demo():
    """Demonstrate lag compensation testing"""
    print("=== Epic Games Lag Compensation Tester ===\n")
    
    tester = LagCompensationTester()
    test_results = []
    
    # Test scenarios
    test_scenarios = [
        # (num_players, latency_min, latency_max, movement, shots_per_sec)
        (10, 20, 50, "circle", 2.0),      # Good conditions
        (10, 50, 100, "circle", 2.0),     # Average conditions  
        (10, 100, 200, "circle", 2.0),    # Poor conditions
        (10, 50, 100, "random", 3.0),     # Random movement
        (10, 50, 100, "static", 5.0),     # Static targets
        (20, 20, 150, "random", 2.0),     # More players
    ]
    
    print("Running lag compensation tests...\n")
    
    for players, lat_min, lat_max, movement, fire_rate in test_scenarios:
        print(f"Testing: {players} players, {lat_min}-{lat_max}ms latency, {movement} movement")
        
        result = await tester.run_test_scenario(
            num_players=players,
            duration=30.0,  # 30 second test
            latency_range=(lat_min, lat_max),
            movement_pattern=movement,
            shots_per_second=fire_rate
        )
        
        test_results.append(result)
        
        print(f"  Hit rate: {result['results']['hit_rate']*100:.1f}%")
        print(f"  Avg compensation: {result['results']['avg_compensation_time']*1000:.1f}ms\n")
        
    # Generate report
    report = tester.generate_report(test_results)
    print("\n" + report)
    
    # Save results
    with open('lag_compensation_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    print("Detailed results saved to lag_compensation_results.json")
    
    # Create visualization
    create_lag_compensation_visualization(test_results)


if __name__ == "__main__":
    asyncio.run(demo())