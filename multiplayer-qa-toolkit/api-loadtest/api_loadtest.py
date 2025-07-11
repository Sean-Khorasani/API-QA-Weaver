#!/usr/bin/env python3
"""
Game Services API Load Testing Framework
Epic Games QA Toolkit
"""

import asyncio
import aiohttp
import time
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque
import logging
from datetime import datetime
import yaml
import psutil
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadProfile(Enum):
    """Predefined load testing profiles"""
    RAMP_UP = "ramp_up"
    STEADY = "steady"
    SPIKE = "spike"
    WAVE = "wave"
    GAME_LAUNCH = "game_launch"
    TOURNAMENT = "tournament"
    SEASONAL_EVENT = "seasonal_event"


@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    name: str
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict] = None
    params: Optional[Dict] = None
    weight: float = 1.0  # Relative frequency
    timeout: float = 30.0
    expected_status: List[int] = field(default_factory=lambda: [200])
    
    def get_full_url(self, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/{self.path.lstrip('/')}"


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    endpoint: str
    status_code: int
    response_time: float
    timestamp: float
    success: bool
    error: Optional[str] = None
    response_size: int = 0


@dataclass 
class LoadTestMetrics:
    """Aggregated metrics for load test"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    response_times: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    requests_per_second: List[float] = field(default_factory=list)
    active_users: List[int] = field(default_factory=list)
    
    start_time: float = 0.0
    end_time: float = 0.0
    
    # System metrics
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    
    def calculate_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not self.response_times:
            return {"p50": 0, "p95": 0, "p99": 0}
            
        sorted_times = sorted(self.response_times)
        return {
            "p50": np.percentile(sorted_times, 50),
            "p95": np.percentile(sorted_times, 95),
            "p99": np.percentile(sorted_times, 99)
        }
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return np.mean(self.response_times)
    
    @property
    def throughput(self) -> float:
        """Requests per second"""
        if self.start_time == 0 or self.end_time == 0:
            return 0.0
        duration = self.end_time - self.start_time
        return self.total_requests / duration if duration > 0 else 0.0


class GameAPIEndpoints:
    """Common game service API endpoints"""
    
    MATCHMAKING = APIEndpoint(
        name="matchmaking_queue",
        method="POST",
        path="/api/matchmaking/queue",
        body={"game_mode": "battle_royale", "region": "NA", "skill_rating": 1500},
        weight=3.0,
        expected_status=[200, 202]
    )
    
    GET_PLAYER_STATS = APIEndpoint(
        name="player_stats",
        method="GET",
        path="/api/players/{player_id}/stats",
        weight=5.0,
        expected_status=[200]
    )
    
    UPDATE_PLAYER_POSITION = APIEndpoint(
        name="update_position",
        method="POST",
        path="/api/game/{session_id}/position",
        body={"x": 100.0, "y": 50.0, "z": 200.0, "timestamp": 0},
        weight=10.0,
        timeout=5.0,
        expected_status=[200, 204]
    )
    
    GET_LEADERBOARD = APIEndpoint(
        name="leaderboard",
        method="GET",
        path="/api/leaderboard",
        params={"limit": 100, "offset": 0},
        weight=2.0,
        expected_status=[200]
    )
    
    PURCHASE_ITEM = APIEndpoint(
        name="purchase_item",
        method="POST",
        path="/api/store/purchase",
        body={"item_id": "skin_001", "currency": "v_bucks", "amount": 1000},
        weight=0.5,
        expected_status=[200, 201]
    )
    
    SEND_TELEMETRY = APIEndpoint(
        name="telemetry",
        method="POST",
        path="/api/telemetry/events",
        body={"events": [{"type": "player_action", "data": {}}]},
        weight=8.0,
        timeout=10.0,
        expected_status=[200, 202, 204]
    )


class VirtualUser:
    """Simulates a game client making API calls"""
    
    def __init__(self, user_id: int, endpoints: List[APIEndpoint], base_url: str):
        self.user_id = user_id
        self.endpoints = endpoints
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_active = True
        self.request_count = 0
        
        # Calculate endpoint weights
        total_weight = sum(e.weight for e in endpoints)
        self.endpoint_probabilities = [e.weight / total_weight for e in endpoints]
        
    async def start(self, duration: float, think_time: float = 1.0) -> List[RequestMetrics]:
        """Start making requests for specified duration"""
        self.session = aiohttp.ClientSession()
        metrics = []
        start_time = time.time()
        
        try:
            while self.is_active and (time.time() - start_time) < duration:
                # Select endpoint based on weights
                endpoint = np.random.choice(self.endpoints, p=self.endpoint_probabilities)
                
                # Make request
                metric = await self._make_request(endpoint)
                metrics.append(metric)
                self.request_count += 1
                
                # Think time between requests
                await asyncio.sleep(think_time + np.random.uniform(-0.5, 0.5))
                
        finally:
            await self.session.close()
            
        return metrics
    
    async def _make_request(self, endpoint: APIEndpoint) -> RequestMetrics:
        """Make a single API request"""
        url = endpoint.get_full_url(self.base_url)
        
        # Substitute path parameters
        url = url.replace("{player_id}", f"player_{self.user_id}")
        url = url.replace("{session_id}", f"session_{self.user_id % 100}")
        
        # Add timestamp to body if needed
        body = endpoint.body.copy() if endpoint.body else None
        if body and "timestamp" in body:
            body["timestamp"] = int(time.time() * 1000)
        
        start_time = time.time()
        metric = RequestMetrics(
            endpoint=endpoint.name,
            status_code=0,
            response_time=0,
            timestamp=start_time,
            success=False
        )
        
        try:
            async with self.session.request(
                method=endpoint.method,
                url=url,
                headers=endpoint.headers,
                json=body,
                params=endpoint.params,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout)
            ) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                metric.status_code = response.status
                metric.response_time = response_time
                metric.success = response.status in endpoint.expected_status
                metric.response_size = len(await response.read())
                
                if not metric.success:
                    metric.error = f"Unexpected status: {response.status}"
                    
        except asyncio.TimeoutError:
            metric.error = "Request timeout"
            metric.response_time = endpoint.timeout * 1000
        except Exception as e:
            metric.error = str(e)
            metric.response_time = (time.time() - start_time) * 1000
            
        return metric
    
    def stop(self):
        """Stop the virtual user"""
        self.is_active = False


class LoadTestRunner:
    """Main load testing orchestrator"""
    
    def __init__(self, base_url: str, endpoints: List[APIEndpoint]):
        self.base_url = base_url
        self.endpoints = endpoints
        self.metrics = LoadTestMetrics()
        self.virtual_users: List[VirtualUser] = []
        self.is_running = False
        
    async def run_load_test(self,
                           profile: LoadProfile,
                           duration: float,
                           max_users: int,
                           ramp_up_time: float = 60.0,
                           think_time: float = 1.0) -> LoadTestMetrics:
        """Run load test with specified profile"""
        
        logger.info(f"Starting load test: {profile.value}, {max_users} users, {duration}s")
        
        self.metrics = LoadTestMetrics()
        self.metrics.start_time = time.time()
        self.is_running = True
        
        # Start metrics collection
        metrics_task = asyncio.create_task(self._collect_metrics())
        
        # Generate user load based on profile
        if profile == LoadProfile.STEADY:
            await self._run_steady_load(max_users, duration, think_time)
        elif profile == LoadProfile.RAMP_UP:
            await self._run_ramp_up_load(max_users, duration, ramp_up_time, think_time)
        elif profile == LoadProfile.SPIKE:
            await self._run_spike_load(max_users, duration, think_time)
        elif profile == LoadProfile.WAVE:
            await self._run_wave_load(max_users, duration, think_time)
        elif profile == LoadProfile.GAME_LAUNCH:
            await self._run_game_launch_load(max_users, duration, think_time)
        elif profile == LoadProfile.TOURNAMENT:
            await self._run_tournament_load(max_users, duration, think_time)
            
        self.is_running = False
        await metrics_task
        
        self.metrics.end_time = time.time()
        return self.metrics
        
    async def _run_steady_load(self, num_users: int, duration: float, think_time: float):
        """Steady load with constant number of users"""
        tasks = []
        
        # Start all users at once
        for i in range(num_users):
            user = VirtualUser(i, self.endpoints, self.base_url)
            self.virtual_users.append(user)
            task = asyncio.create_task(self._run_user(user, duration, think_time))
            tasks.append(task)
            
        # Wait for all users to complete
        results = await asyncio.gather(*tasks)
        
        # Aggregate metrics
        for user_metrics in results:
            self._process_user_metrics(user_metrics)
            
    async def _run_ramp_up_load(self, max_users: int, duration: float, 
                                ramp_up_time: float, think_time: float):
        """Gradually increase load"""
        tasks = []
        users_per_second = max_users / ramp_up_time
        start_time = time.time()
        
        for i in range(max_users):
            # Calculate when this user should start
            start_delay = i / users_per_second
            
            user = VirtualUser(i, self.endpoints, self.base_url)
            self.virtual_users.append(user)
            
            remaining_duration = max(0, duration - start_delay)
            task = asyncio.create_task(
                self._delayed_user_start(user, start_delay, remaining_duration, think_time)
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        
        for user_metrics in results:
            self._process_user_metrics(user_metrics)
            
    async def _run_spike_load(self, max_users: int, duration: float, think_time: float):
        """Sudden spike in traffic"""
        # Normal load for first third
        normal_users = max_users // 3
        spike_duration = duration / 3
        
        # Start normal load
        await self._run_steady_load(normal_users, spike_duration, think_time)
        
        # Spike to max users
        await self._run_steady_load(max_users, spike_duration, think_time)
        
        # Return to normal
        await self._run_steady_load(normal_users, spike_duration, think_time)
        
    async def _run_wave_load(self, max_users: int, duration: float, think_time: float):
        """Sinusoidal wave pattern"""
        wave_period = 60.0  # 1 minute waves
        tasks = []
        start_time = time.time()
        
        async def wave_user(user_id: int):
            user = VirtualUser(user_id, self.endpoints, self.base_url)
            metrics = []
            
            while (time.time() - start_time) < duration:
                # Calculate if user should be active based on wave
                elapsed = time.time() - start_time
                wave_value = (math.sin(2 * math.pi * elapsed / wave_period) + 1) / 2
                active_users = int(max_users * wave_value)
                
                if user_id < active_users:
                    # Make a request
                    endpoint = np.random.choice(self.endpoints, p=user.endpoint_probabilities)
                    metric = await user._make_request(endpoint)
                    metrics.append(metric)
                    
                await asyncio.sleep(think_time)
                
            return metrics
            
        for i in range(max_users):
            task = asyncio.create_task(wave_user(i))
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        for user_metrics in results:
            self._process_user_metrics(user_metrics)
            
    async def _run_game_launch_load(self, max_users: int, duration: float, think_time: float):
        """Simulate game launch traffic pattern"""
        # Massive initial spike (login rush)
        logger.info("Simulating game launch - login rush")
        await self._run_steady_load(max_users, duration * 0.1, think_time * 0.5)
        
        # Gradual decrease as players get into matches
        logger.info("Players entering matches")
        for i in range(3):
            active_users = int(max_users * (0.7 - i * 0.2))
            await self._run_steady_load(active_users, duration * 0.2, think_time)
            
        # Steady state
        logger.info("Steady state gameplay")
        await self._run_steady_load(max_users // 3, duration * 0.3, think_time)
        
    async def _run_tournament_load(self, max_users: int, duration: float, think_time: float):
        """Simulate tournament traffic pattern"""
        # Pre-tournament (players checking in)
        logger.info("Tournament check-in phase")
        await self._run_ramp_up_load(max_users // 2, duration * 0.2, duration * 0.1, think_time)
        
        # Tournament start (all players joining)
        logger.info("Tournament start - all players joining")
        await self._run_steady_load(max_users, duration * 0.1, think_time * 0.3)
        
        # During tournament (decreasing as players are eliminated)
        logger.info("Tournament in progress")
        for round_num in range(4):
            active_players = max_users // (2 ** round_num)
            await self._run_steady_load(active_players, duration * 0.15, think_time)
            
        # Post-tournament (checking results)
        logger.info("Post-tournament phase")
        await self._run_steady_load(max_users // 2, duration * 0.05, think_time * 0.5)
        
    async def _delayed_user_start(self, user: VirtualUser, delay: float, 
                                 duration: float, think_time: float):
        """Start user after delay"""
        await asyncio.sleep(delay)
        return await user.start(duration, think_time)
        
    async def _run_user(self, user: VirtualUser, duration: float, think_time: float):
        """Run a single virtual user"""
        return await user.start(duration, think_time)
        
    def _process_user_metrics(self, user_metrics: List[RequestMetrics]):
        """Process metrics from a virtual user"""
        for metric in user_metrics:
            self.metrics.total_requests += 1
            
            if metric.success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
                if metric.error:
                    self.metrics.errors[metric.error] += 1
                    
            self.metrics.response_times.append(metric.response_time)
            self.metrics.status_codes[metric.status_code] += 1
            
    async def _collect_metrics(self):
        """Collect system and test metrics periodically"""
        interval = 1.0  # Collect every second
        rps_window = deque(maxlen=10)  # 10 second window for RPS
        last_request_count = 0
        
        while self.is_running:
            # Calculate requests per second
            current_requests = self.metrics.total_requests
            rps = (current_requests - last_request_count) / interval
            rps_window.append(rps)
            self.metrics.requests_per_second.append(np.mean(rps_window))
            last_request_count = current_requests
            
            # Count active users
            active_users = sum(1 for u in self.virtual_users if u.is_active)
            self.metrics.active_users.append(active_users)
            
            # Collect system metrics
            self.metrics.cpu_usage.append(psutil.cpu_percent())
            self.metrics.memory_usage.append(psutil.virtual_memory().percent)
            
            await asyncio.sleep(interval)
            
    def generate_report(self) -> str:
        """Generate load test report"""
        percentiles = self.metrics.calculate_percentiles()
        
        report = f"""
=== Game Services API Load Test Report ===

Test Summary:
- Duration: {self.metrics.end_time - self.metrics.start_time:.1f} seconds
- Total Requests: {self.metrics.total_requests:,}
- Successful Requests: {self.metrics.successful_requests:,}
- Failed Requests: {self.metrics.failed_requests:,}
- Success Rate: {self.metrics.success_rate * 100:.2f}%

Performance Metrics:
- Throughput: {self.metrics.throughput:.2f} req/s
- Average Response Time: {self.metrics.average_response_time:.2f} ms
- P50 Response Time: {percentiles['p50']:.2f} ms
- P95 Response Time: {percentiles['p95']:.2f} ms
- P99 Response Time: {percentiles['p99']:.2f} ms

Status Code Distribution:
"""
        for status, count in sorted(self.metrics.status_codes.items()):
            percentage = (count / self.metrics.total_requests) * 100
            report += f"  - {status}: {count:,} ({percentage:.1f}%)\n"
            
        if self.metrics.errors:
            report += "\nError Distribution:\n"
            for error, count in sorted(self.metrics.errors.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / self.metrics.failed_requests) * 100
                report += f"  - {error}: {count:,} ({percentage:.1f}%)\n"
                
        report += f"\nSystem Metrics:\n"
        report += f"- Average CPU Usage: {np.mean(self.metrics.cpu_usage):.1f}%\n"
        report += f"- Average Memory Usage: {np.mean(self.metrics.memory_usage):.1f}%\n"
        
        return report


# Demo scenarios
async def demo():
    """Demonstrate API load testing capabilities"""
    print("=== Epic Games API Load Testing Framework ===\n")
    
    # Setup endpoints
    endpoints = [
        GameAPIEndpoints.MATCHMAKING,
        GameAPIEndpoints.GET_PLAYER_STATS,
        GameAPIEndpoints.UPDATE_PLAYER_POSITION,
        GameAPIEndpoints.GET_LEADERBOARD,
        GameAPIEndpoints.SEND_TELEMETRY
    ]
    
    # For demo, use a mock server URL
    base_url = "http://localhost:8080"
    
    # Run different load profiles
    profiles_to_test = [
        (LoadProfile.STEADY, 50, 30),      # 50 users, 30 seconds
        (LoadProfile.RAMP_UP, 100, 60),    # Ramp to 100 users, 60 seconds
        (LoadProfile.SPIKE, 200, 60),      # Spike to 200 users
        (LoadProfile.GAME_LAUNCH, 500, 120)  # Game launch simulation
    ]
    
    for profile, max_users, duration in profiles_to_test:
        print(f"\n--- Testing {profile.value} profile ---")
        print(f"Max users: {max_users}, Duration: {duration}s\n")
        
        runner = LoadTestRunner(base_url, endpoints)
        
        try:
            metrics = await runner.run_load_test(
                profile=profile,
                duration=duration,
                max_users=max_users,
                ramp_up_time=30.0,
                think_time=1.0
            )
            
            # Print summary
            print(f"Completed: {metrics.total_requests:,} requests")
            print(f"Success rate: {metrics.success_rate * 100:.1f}%")
            print(f"Avg response time: {metrics.average_response_time:.0f}ms")
            print(f"Throughput: {metrics.throughput:.1f} req/s")
            
            # Save detailed report
            report = runner.generate_report()
            filename = f"loadtest_{profile.value}_{int(time.time())}.txt"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"Detailed report saved to {filename}")
            
            # Save metrics data
            metrics_data = {
                'profile': profile.value,
                'max_users': max_users,
                'duration': duration,
                'total_requests': metrics.total_requests,
                'success_rate': metrics.success_rate,
                'percentiles': metrics.calculate_percentiles(),
                'throughput': metrics.throughput
            }
            
            json_filename = f"loadtest_metrics_{profile.value}_{int(time.time())}.json"
            with open(json_filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            print(f"Error during load test: {e}")
            

if __name__ == "__main__":
    # Note: For actual testing, ensure your API server is running
    print("Note: This demo requires an API server running on http://localhost:8080")
    print("You can use the included mock_game_server.py for testing\n")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--skip-demo":
        print("Skipping demo. Use the LoadTestRunner class in your code.")
    else:
        asyncio.run(demo())