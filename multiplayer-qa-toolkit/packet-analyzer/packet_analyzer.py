#!/usr/bin/env python3
"""
Game Packet Analyzer for Multiplayer Network Protocols
Epic Games QA Toolkit
"""

import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
import logging
from enum import IntEnum
import numpy as np
from bitstring import BitArray, BitStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PacketType(IntEnum):
    """Common game packet types"""
    PLAYER_POSITION = 0x01
    PLAYER_ACTION = 0x02
    WORLD_STATE = 0x03
    OBJECT_SPAWN = 0x04
    OBJECT_DESTROY = 0x05
    CHAT_MESSAGE = 0x06
    VOICE_DATA = 0x07
    SERVER_TICK = 0x08
    CLIENT_INPUT = 0x09
    DAMAGE_EVENT = 0x0A
    INVENTORY_UPDATE = 0x0B
    MATCH_STATE = 0x0C
    TELEMETRY = 0x0D
    HEARTBEAT = 0x0E
    ACKNOWLEDGMENT = 0x0F


@dataclass
class PacketHeader:
    """Standard game packet header"""
    packet_type: PacketType
    sequence_number: int
    timestamp: int
    size: int
    flags: int = 0
    checksum: Optional[int] = None


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    total_packets: int = 0
    total_bytes: int = 0
    packets_by_type: Dict[PacketType, int] = field(default_factory=lambda: defaultdict(int))
    bytes_by_type: Dict[PacketType, int] = field(default_factory=lambda: defaultdict(int))
    
    packet_sizes: List[int] = field(default_factory=list)
    inter_packet_delays: List[float] = field(default_factory=list)
    
    compression_ratio: float = 0.0
    bandwidth_usage: List[float] = field(default_factory=list)
    
    packet_loss_sequences: List[int] = field(default_factory=list)
    out_of_order_count: int = 0
    duplicate_count: int = 0
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate network statistics"""
        if not self.packet_sizes:
            return {}
            
        return {
            'avg_packet_size': np.mean(self.packet_sizes),
            'median_packet_size': np.median(self.packet_sizes),
            'max_packet_size': max(self.packet_sizes),
            'min_packet_size': min(self.packet_sizes),
            'total_bandwidth': self.total_bytes,
            'packet_type_distribution': dict(self.packets_by_type),
            'avg_inter_packet_delay': np.mean(self.inter_packet_delays) if self.inter_packet_delays else 0,
            'bandwidth_efficiency': self.compression_ratio,
            'packet_loss_rate': len(self.packet_loss_sequences) / max(self.total_packets, 1)
        }


class GameProtocolParser:
    """Parser for game-specific network protocols"""
    
    def __init__(self):
        self.header_size = 16  # bytes
        self.max_packet_size = 1400  # MTU friendly
        
    def parse_header(self, data: bytes) -> Optional[PacketHeader]:
        """Parse packet header"""
        if len(data) < self.header_size:
            return None
            
        # Unpack header: type(1), seq(4), timestamp(4), size(2), flags(1), checksum(4)
        header_format = '!BIIHBI'
        unpacked = struct.unpack(header_format, data[:self.header_size])
        
        return PacketHeader(
            packet_type=PacketType(unpacked[0]),
            sequence_number=unpacked[1],
            timestamp=unpacked[2],
            size=unpacked[3],
            flags=unpacked[4],
            checksum=unpacked[5]
        )
        
    def parse_player_position(self, data: bytes) -> Dict[str, Any]:
        """Parse player position packet"""
        # Format: player_id(4), x(4), y(4), z(4), yaw(2), pitch(2), velocity(12), state(1)
        if len(data) < 33:
            return {}
            
        unpacked = struct.unpack('!IfffhhfffB', data[:33])
        
        return {
            'player_id': unpacked[0],
            'position': {
                'x': unpacked[1],
                'y': unpacked[2], 
                'z': unpacked[3]
            },
            'rotation': {
                'yaw': unpacked[4] / 100.0,  # Compressed angles
                'pitch': unpacked[5] / 100.0
            },
            'velocity': {
                'x': unpacked[6],
                'y': unpacked[7],
                'z': unpacked[8]
            },
            'state': unpacked[9]
        }
        
    def parse_world_state(self, data: bytes) -> Dict[str, Any]:
        """Parse world state update packet"""
        stream = BitStream(data)
        
        world_state = {
            'tick': stream.read('uint:32'),
            'player_count': stream.read('uint:8'),
            'players': []
        }
        
        # Delta compressed player states
        for i in range(world_state['player_count']):
            player = {
                'id': stream.read('uint:16'),
                'flags': stream.read('uint:8')
            }
            
            # Check which fields are included based on flags
            if player['flags'] & 0x01:  # Position changed
                player['position'] = {
                    'x': stream.read('float:32'),
                    'y': stream.read('float:32'),
                    'z': stream.read('float:32')
                }
                
            if player['flags'] & 0x02:  # Rotation changed
                player['rotation'] = {
                    'yaw': stream.read('int:16') / 100.0,
                    'pitch': stream.read('int:16') / 100.0
                }
                
            if player['flags'] & 0x04:  # Health changed
                player['health'] = stream.read('uint:8')
                
            world_state['players'].append(player)
            
        return world_state
        
    def encode_player_position(self, player_data: Dict[str, Any]) -> bytes:
        """Encode player position packet"""
        return struct.pack(
            '!IfffhhfffB',
            player_data['player_id'],
            player_data['position']['x'],
            player_data['position']['y'],
            player_data['position']['z'],
            int(player_data['rotation']['yaw'] * 100),
            int(player_data['rotation']['pitch'] * 100),
            player_data['velocity']['x'],
            player_data['velocity']['y'],
            player_data['velocity']['z'],
            player_data['state']
        )


class PacketOptimizer:
    """Analyzes packets for optimization opportunities"""
    
    def __init__(self):
        self.field_frequencies = defaultdict(lambda: defaultdict(int))
        self.field_ranges = defaultdict(lambda: {'min': float('inf'), 'max': float('-inf')})
        
    def analyze_packet_stream(self, packets: List[Tuple[PacketHeader, bytes]]) -> Dict[str, Any]:
        """Analyze packet stream for optimization opportunities"""
        optimization_report = {
            'redundant_data': [],
            'compressible_fields': [],
            'suggested_encodings': {},
            'potential_savings': 0
        }
        
        # Analyze each packet type
        packet_groups = defaultdict(list)
        for header, data in packets:
            packet_groups[header.packet_type].append((header, data))
            
        for packet_type, group in packet_groups.items():
            if packet_type == PacketType.PLAYER_POSITION:
                self._analyze_position_packets(group, optimization_report)
            elif packet_type == PacketType.WORLD_STATE:
                self._analyze_world_state_packets(group, optimization_report)
                
        return optimization_report
        
    def _analyze_position_packets(self, packets: List[Tuple[PacketHeader, bytes]], 
                                 report: Dict[str, Any]):
        """Analyze player position packets for optimization"""
        parser = GameProtocolParser()
        positions = []
        
        for header, data in packets:
            parsed = parser.parse_player_position(data)
            if parsed:
                positions.append(parsed)
                
        if len(positions) < 2:
            return
            
        # Check for redundant updates (position didn't change)
        redundant_count = 0
        for i in range(1, len(positions)):
            if (positions[i]['position'] == positions[i-1]['position'] and
                positions[i]['velocity']['x'] == 0 and
                positions[i]['velocity']['y'] == 0 and
                positions[i]['velocity']['z'] == 0):
                redundant_count += 1
                
        if redundant_count > len(positions) * 0.1:  # >10% redundant
            report['redundant_data'].append({
                'packet_type': 'PLAYER_POSITION',
                'redundancy_rate': redundant_count / len(positions),
                'suggestion': 'Implement delta compression or skip unchanged positions'
            })
            
        # Analyze position value ranges for better encoding
        x_values = [p['position']['x'] for p in positions]
        y_values = [p['position']['y'] for p in positions]
        z_values = [p['position']['z'] for p in positions]
        
        # If positions are within a small range, we can use smaller data types
        x_range = max(x_values) - min(x_values)
        z_range = max(z_values) - min(z_values)
        
        if x_range < 65536 and z_range < 65536:  # Fits in 16-bit
            current_size = 4 * 3  # 3 floats
            optimized_size = 2 * 3  # 3 shorts with offset
            savings = (current_size - optimized_size) * len(positions)
            
            report['compressible_fields'].append({
                'field': 'position',
                'current_encoding': 'float32',
                'suggested_encoding': 'int16 with offset',
                'savings_per_packet': current_size - optimized_size,
                'total_savings': savings
            })
            report['potential_savings'] += savings
            
    def _analyze_world_state_packets(self, packets: List[Tuple[PacketHeader, bytes]], 
                                   report: Dict[str, Any]):
        """Analyze world state packets for optimization"""
        # Track which fields change frequently
        change_frequencies = defaultdict(int)
        total_updates = 0
        
        parser = GameProtocolParser()
        
        for header, data in packets:
            state = parser.parse_world_state(data)
            for player in state.get('players', []):
                total_updates += 1
                if 'position' in player:
                    change_frequencies['position'] += 1
                if 'rotation' in player:
                    change_frequencies['rotation'] += 1
                if 'health' in player:
                    change_frequencies['health'] += 1
                    
        # Suggest priority-based encoding
        if total_updates > 0:
            sorted_fields = sorted(
                change_frequencies.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            report['suggested_encodings']['world_state'] = {
                'field_priorities': [f[0] for f in sorted_fields],
                'change_rates': {f[0]: f[1]/total_updates for f in sorted_fields},
                'suggestion': 'Encode high-frequency fields first for better compression'
            }


class BandwidthAnalyzer:
    """Analyzes bandwidth usage patterns"""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size  # seconds
        self.packet_timestamps = deque(maxlen=1000)
        self.packet_sizes = deque(maxlen=1000)
        self.bandwidth_history = deque(maxlen=window_size)
        
    def add_packet(self, timestamp: float, size: int):
        """Add packet to bandwidth calculation"""
        self.packet_timestamps.append(timestamp)
        self.packet_sizes.append(size)
        
    def calculate_current_bandwidth(self) -> float:
        """Calculate current bandwidth usage in bytes/second"""
        if len(self.packet_timestamps) < 2:
            return 0.0
            
        current_time = self.packet_timestamps[-1]
        window_start = current_time - 1.0  # 1 second window
        
        # Sum packets within window
        bytes_in_window = 0
        for i in range(len(self.packet_timestamps) - 1, -1, -1):
            if self.packet_timestamps[i] < window_start:
                break
            bytes_in_window += self.packet_sizes[i]
            
        return bytes_in_window
        
    def get_bandwidth_statistics(self) -> Dict[str, float]:
        """Get bandwidth usage statistics"""
        if not self.bandwidth_history:
            return {}
            
        bandwidth_list = list(self.bandwidth_history)
        return {
            'current_bps': self.calculate_current_bandwidth(),
            'average_bps': np.mean(bandwidth_list),
            'peak_bps': max(bandwidth_list),
            'min_bps': min(bandwidth_list),
            'std_dev': np.std(bandwidth_list)
        }


class PacketFlowAnalyzer:
    """Analyzes packet flow patterns and detects anomalies"""
    
    def __init__(self):
        self.sequence_tracker = defaultdict(int)
        self.last_timestamps = defaultdict(float)
        self.flow_patterns = defaultdict(list)
        
    def analyze_packet_flow(self, packets: List[Tuple[PacketHeader, bytes]]) -> Dict[str, Any]:
        """Analyze packet flow for patterns and anomalies"""
        analysis = {
            'flow_patterns': {},
            'anomalies': [],
            'sequence_gaps': [],
            'timing_irregularities': []
        }
        
        # Group by packet type
        by_type = defaultdict(list)
        for header, data in packets:
            by_type[header.packet_type].append(header)
            
        # Analyze each type's flow
        for packet_type, headers in by_type.items():
            if len(headers) < 2:
                continue
                
            # Check sequence numbers
            sequences = [h.sequence_number for h in headers]
            expected_seq = sequences[0]
            
            for i, seq in enumerate(sequences):
                if seq != expected_seq:
                    gap = seq - expected_seq
                    analysis['sequence_gaps'].append({
                        'packet_type': packet_type.name,
                        'expected': expected_seq,
                        'actual': seq,
                        'gap': gap,
                        'position': i
                    })
                expected_seq = seq + 1
                
            # Analyze timing patterns
            timestamps = [h.timestamp for h in headers]
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            
            if intervals:
                avg_interval = np.mean(intervals)
                std_interval = np.std(intervals)
                
                # Detect timing anomalies
                for i, interval in enumerate(intervals):
                    if abs(interval - avg_interval) > 3 * std_interval:  # 3 sigma
                        analysis['timing_irregularities'].append({
                            'packet_type': packet_type.name,
                            'position': i,
                            'interval': interval,
                            'expected': avg_interval,
                            'deviation': (interval - avg_interval) / std_interval
                        })
                        
                analysis['flow_patterns'][packet_type.name] = {
                    'avg_interval': avg_interval,
                    'std_interval': std_interval,
                    'packets_per_second': 1.0 / avg_interval if avg_interval > 0 else 0
                }
                
        return analysis


# Demo and testing
def demo():
    """Demonstrate packet analysis capabilities"""
    print("=== Epic Games Packet Analyzer Demo ===\n")
    
    # Create analyzers
    parser = GameProtocolParser()
    optimizer = PacketOptimizer()
    bandwidth = BandwidthAnalyzer()
    flow_analyzer = PacketFlowAnalyzer()
    metrics = NetworkMetrics()
    
    # Simulate packet stream
    print("Simulating game packet stream...\n")
    
    packets = []
    current_time = time.time()
    sequence = 0
    
    # Generate sample packets
    for i in range(1000):
        # Mix of packet types with realistic frequencies
        packet_type = np.random.choice(
            [PacketType.PLAYER_POSITION, PacketType.WORLD_STATE, 
             PacketType.CLIENT_INPUT, PacketType.DAMAGE_EVENT],
            p=[0.6, 0.2, 0.15, 0.05]
        )
        
        # Create header
        header = PacketHeader(
            packet_type=packet_type,
            sequence_number=sequence,
            timestamp=int(current_time * 1000),
            size=0,  # Will be set later
            flags=0
        )
        
        # Generate packet data based on type
        if packet_type == PacketType.PLAYER_POSITION:
            data = parser.encode_player_position({
                'player_id': 12345,
                'position': {
                    'x': 1000 + np.random.randn() * 10,
                    'y': 50 + np.random.randn() * 2,
                    'z': 2000 + np.random.randn() * 10
                },
                'rotation': {
                    'yaw': np.random.uniform(-180, 180),
                    'pitch': np.random.uniform(-90, 90)
                },
                'velocity': {
                    'x': np.random.randn() * 5,
                    'y': 0,
                    'z': np.random.randn() * 5
                },
                'state': 1
            })
        else:
            # Simple dummy data for other types
            data = bytes(np.random.randint(0, 256, size=50))
            
        header.size = len(data)
        packets.append((header, data))
        
        # Update metrics
        metrics.total_packets += 1
        metrics.total_bytes += len(data)
        metrics.packets_by_type[packet_type] += 1
        metrics.bytes_by_type[packet_type] += len(data)
        metrics.packet_sizes.append(len(data))
        
        # Update bandwidth analyzer
        bandwidth.add_packet(current_time, len(data))
        
        # Simulate realistic timing
        current_time += 0.016 + np.random.exponential(0.002)  # ~60Hz with jitter
        sequence += 1
        
        # Simulate occasional packet loss
        if np.random.random() < 0.01:  # 1% loss
            metrics.packet_loss_sequences.append(sequence)
            sequence += 1  # Skip sequence number
            
    # Analyze packets
    print("Analyzing packet stream...\n")
    
    # Optimization analysis
    optimization_report = optimizer.analyze_packet_stream(packets)
    
    print("=== Optimization Opportunities ===")
    if optimization_report['redundant_data']:
        for redundancy in optimization_report['redundant_data']:
            print(f"- {redundancy['packet_type']}: {redundancy['redundancy_rate']*100:.1f}% redundant")
            print(f"  Suggestion: {redundancy['suggestion']}")
            
    if optimization_report['compressible_fields']:
        for field in optimization_report['compressible_fields']:
            print(f"- {field['field']}: Can save {field['savings_per_packet']} bytes/packet")
            print(f"  Current: {field['current_encoding']}, Suggested: {field['suggested_encoding']}")
            
    print(f"\nTotal potential savings: {optimization_report['potential_savings']} bytes")
    
    # Flow analysis
    flow_analysis = flow_analyzer.analyze_packet_flow(packets)
    
    print("\n=== Packet Flow Analysis ===")
    for packet_type, pattern in flow_analysis['flow_patterns'].items():
        print(f"- {packet_type}:")
        print(f"  Rate: {pattern['packets_per_second']:.1f} packets/sec")
        print(f"  Interval: {pattern['avg_interval']*1000:.1f} ± {pattern['std_interval']*1000:.1f} ms")
        
    if flow_analysis['sequence_gaps']:
        print(f"\nDetected {len(flow_analysis['sequence_gaps'])} sequence gaps")
        
    if flow_analysis['timing_irregularities']:
        print(f"Detected {len(flow_analysis['timing_irregularities'])} timing anomalies")
        
    # Bandwidth statistics
    bandwidth_stats = bandwidth.get_bandwidth_statistics()
    
    print("\n=== Bandwidth Usage ===")
    print(f"Current: {bandwidth_stats.get('current_bps', 0)/1024:.1f} KB/s")
    print(f"Average: {bandwidth_stats.get('average_bps', 0)/1024:.1f} KB/s")
    print(f"Peak: {bandwidth_stats.get('peak_bps', 0)/1024:.1f} KB/s")
    
    # Overall metrics
    stats = metrics.calculate_statistics()
    
    print("\n=== Overall Statistics ===")
    print(f"Total packets: {metrics.total_packets}")
    print(f"Total data: {metrics.total_bytes/1024:.1f} KB")
    print(f"Average packet size: {stats['avg_packet_size']:.1f} bytes")
    print(f"Packet loss rate: {stats['packet_loss_rate']*100:.2f}%")
    
    print("\nPacket type distribution:")
    for ptype, count in metrics.packets_by_type.items():
        percentage = (count / metrics.total_packets) * 100
        print(f"  {ptype.name}: {count} ({percentage:.1f}%)")


if __name__ == "__main__":
    demo()