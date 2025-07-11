#!/usr/bin/env python3
"""
Chaos Testing Framework for Multiplayer Game Infrastructure
Epic Games QA Toolkit
"""

import asyncio
import random
import time
import yaml
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChaosExperiment(Enum):
    """Types of chaos experiments"""
    SERVICE_FAILURE = "service_failure"
    NETWORK_PARTITION = "network_partition"
    LATENCY_INJECTION = "latency_injection"
    PACKET_LOSS = "packet_loss"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CLOCK_SKEW = "clock_skew"
    CERTIFICATE_EXPIRY = "certificate_expiry"
    DATABASE_SLOWDOWN = "database_slowdown"
    CACHE_INVALIDATION = "cache_invalidation"
    REGION_FAILURE = "region_failure"


class ServiceType(Enum):
    """Game service types"""
    MATCHMAKING = "matchmaking"
    GAME_SERVER = "game_server"
    AUTH_SERVICE = "auth_service"
    PLAYER_DATA = "player_data"
    LEADERBOARD = "leaderboard"
    CHAT_SERVICE = "chat_service"
    STORE_SERVICE = "store_service"
    TELEMETRY = "telemetry"
    CDN = "cdn"
    DATABASE = "database"


@dataclass
class ServiceHealth:
    """Health status of a service"""
    service_name: str
    service_type: ServiceType
    is_healthy: bool
    response_time_ms: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class ChaosEvent:
    """Represents a chaos event"""
    experiment_type: ChaosExperiment
    target_service: str
    start_time: datetime
    duration: timedelta
    severity: float  # 0.0 to 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    impact_assessment: Optional[Dict[str, Any]] = None


@dataclass
class GameHealthMetrics:
    """Overall game health metrics during chaos"""
    timestamp: datetime
    players_online: int
    matchmaking_success_rate: float
    average_match_time: float
    api_success_rate: float
    average_api_latency: float
    error_count: int
    revenue_per_minute: float
    player_reports: int
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'players_online': self.players_online,
            'matchmaking_success_rate': self.matchmaking_success_rate,
            'average_match_time': self.average_match_time,
            'api_success_rate': self.api_success_rate,
            'average_api_latency': self.average_api_latency,
            'error_count': self.error_count,
            'revenue_per_minute': self.revenue_per_minute,
            'player_reports': self.player_reports
        }


class ServiceMesh:
    """Simulates game service mesh"""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self._initialize_services()
        
    def _initialize_services(self):
        """Initialize service topology"""
        # Core services
        services = [
            ("auth-service", ServiceType.AUTH_SERVICE),
            ("matchmaking-service", ServiceType.MATCHMAKING),
            ("game-server-fleet", ServiceType.GAME_SERVER),
            ("player-data-service", ServiceType.PLAYER_DATA),
            ("leaderboard-service", ServiceType.LEADERBOARD),
            ("chat-service", ServiceType.CHAT_SERVICE),
            ("store-service", ServiceType.STORE_SERVICE),
            ("telemetry-service", ServiceType.TELEMETRY),
            ("cdn-service", ServiceType.CDN),
            ("main-database", ServiceType.DATABASE),
            ("cache-layer", ServiceType.DATABASE),
        ]
        
        for name, service_type in services:
            self.services[name] = ServiceHealth(
                service_name=name,
                service_type=service_type,
                is_healthy=True,
                response_time_ms=random.uniform(10, 50),
                error_rate=0.001,
                cpu_usage=random.uniform(30, 50),
                memory_usage=random.uniform(40, 60),
                active_connections=random.randint(100, 1000)
            )
            
        # Define dependencies
        self.dependencies = {
            "matchmaking-service": ["auth-service", "player-data-service", "game-server-fleet"],
            "game-server-fleet": ["player-data-service", "main-database"],
            "leaderboard-service": ["player-data-service", "cache-layer"],
            "store-service": ["auth-service", "player-data-service", "main-database"],
            "player-data-service": ["main-database", "cache-layer"],
            "chat-service": ["auth-service", "cache-layer"],
        }
        
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get current health of a service"""
        return self.services.get(service_name)
        
    def update_service_health(self, service_name: str, health_update: Dict[str, Any]):
        """Update service health metrics"""
        if service_name in self.services:
            service = self.services[service_name]
            for key, value in health_update.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            service.last_check = datetime.now()
            
    def get_dependent_services(self, service_name: str) -> List[str]:
        """Get services that depend on the given service"""
        dependent_services = []
        for service, deps in self.dependencies.items():
            if service_name in deps:
                dependent_services.append(service)
        return dependent_services
        
    def calculate_cascading_impact(self, failed_service: str) -> Dict[str, float]:
        """Calculate cascading failure impact"""
        impact = {failed_service: 1.0}  # Direct failure
        
        # BFS to find all affected services
        queue = [(failed_service, 1.0)]
        visited = {failed_service}
        
        while queue:
            current_service, current_impact = queue.pop(0)
            dependents = self.get_dependent_services(current_service)
            
            for dependent in dependents:
                if dependent not in visited:
                    visited.add(dependent)
                    # Impact decreases with distance
                    dependent_impact = current_impact * 0.7
                    impact[dependent] = max(impact.get(dependent, 0), dependent_impact)
                    queue.append((dependent, dependent_impact))
                    
        return impact


class ChaosOrchestrator:
    """Orchestrates chaos experiments"""
    
    def __init__(self, service_mesh: ServiceMesh):
        self.service_mesh = service_mesh
        self.active_experiments: List[ChaosEvent] = []
        self.experiment_history: List[ChaosEvent] = []
        self.health_metrics_history: List[GameHealthMetrics] = []
        self.blast_radius_predictor = BlastRadiusPredictor()
        
    async def run_experiment(self, experiment: ChaosEvent) -> Dict[str, Any]:
        """Run a chaos experiment"""
        logger.info(f"Starting chaos experiment: {experiment.experiment_type.value} on {experiment.target_service}")
        
        # Predict blast radius
        predicted_impact = self.blast_radius_predictor.predict_impact(
            experiment, 
            self.service_mesh
        )
        
        experiment.impact_assessment = predicted_impact
        self.active_experiments.append(experiment)
        
        # Execute experiment based on type
        if experiment.experiment_type == ChaosExperiment.SERVICE_FAILURE:
            await self._simulate_service_failure(experiment)
        elif experiment.experiment_type == ChaosExperiment.NETWORK_PARTITION:
            await self._simulate_network_partition(experiment)
        elif experiment.experiment_type == ChaosExperiment.LATENCY_INJECTION:
            await self._simulate_latency_injection(experiment)
        elif experiment.experiment_type == ChaosExperiment.RESOURCE_EXHAUSTION:
            await self._simulate_resource_exhaustion(experiment)
        elif experiment.experiment_type == ChaosExperiment.DATABASE_SLOWDOWN:
            await self._simulate_database_slowdown(experiment)
            
        # Monitor impact during experiment
        impact_metrics = await self._monitor_impact(experiment)
        
        # Cleanup
        self.active_experiments.remove(experiment)
        self.experiment_history.append(experiment)
        
        return {
            'experiment': experiment,
            'predicted_impact': predicted_impact,
            'actual_impact': impact_metrics,
            'recovery_time': self._calculate_recovery_time(impact_metrics)
        }
        
    async def _simulate_service_failure(self, experiment: ChaosEvent):
        """Simulate complete service failure"""
        service = self.service_mesh.get_service_health(experiment.target_service)
        if not service:
            return
            
        # Save original state
        original_state = {
            'is_healthy': service.is_healthy,
            'error_rate': service.error_rate,
            'response_time_ms': service.response_time_ms
        }
        
        # Apply failure
        self.service_mesh.update_service_health(experiment.target_service, {
            'is_healthy': False,
            'error_rate': 1.0,
            'response_time_ms': 30000  # Timeout
        })
        
        # Wait for experiment duration
        await asyncio.sleep(experiment.duration.total_seconds())
        
        # Restore service
        self.service_mesh.update_service_health(experiment.target_service, original_state)
        
    async def _simulate_network_partition(self, experiment: ChaosEvent):
        """Simulate network partition between services"""
        affected_services = experiment.parameters.get('affected_services', [])
        partition_rate = experiment.severity
        
        for service_name in affected_services:
            service = self.service_mesh.get_service_health(service_name)
            if service:
                original_error_rate = service.error_rate
                # Increase error rate based on partition severity
                self.service_mesh.update_service_health(service_name, {
                    'error_rate': min(1.0, original_error_rate + partition_rate)
                })
                
        await asyncio.sleep(experiment.duration.total_seconds())
        
        # Restore
        for service_name in affected_services:
            service = self.service_mesh.get_service_health(service_name)
            if service:
                self.service_mesh.update_service_health(service_name, {
                    'error_rate': 0.001  # Normal error rate
                })
                
    async def _simulate_latency_injection(self, experiment: ChaosEvent):
        """Inject latency into service responses"""
        service = self.service_mesh.get_service_health(experiment.target_service)
        if not service:
            return
            
        original_latency = service.response_time_ms
        added_latency = experiment.parameters.get('added_latency_ms', 1000)
        
        self.service_mesh.update_service_health(experiment.target_service, {
            'response_time_ms': original_latency + added_latency
        })
        
        await asyncio.sleep(experiment.duration.total_seconds())
        
        self.service_mesh.update_service_health(experiment.target_service, {
            'response_time_ms': original_latency
        })
        
    async def _simulate_resource_exhaustion(self, experiment: ChaosEvent):
        """Simulate CPU/Memory exhaustion"""
        service = self.service_mesh.get_service_health(experiment.target_service)
        if not service:
            return
            
        resource_type = experiment.parameters.get('resource_type', 'cpu')
        
        if resource_type == 'cpu':
            self.service_mesh.update_service_health(experiment.target_service, {
                'cpu_usage': 95 + random.uniform(0, 5),
                'response_time_ms': service.response_time_ms * 3
            })
        else:  # memory
            self.service_mesh.update_service_health(experiment.target_service, {
                'memory_usage': 95 + random.uniform(0, 5),
                'error_rate': 0.1  # OOM errors
            })
            
        await asyncio.sleep(experiment.duration.total_seconds())
        
        # Restore
        self.service_mesh.update_service_health(experiment.target_service, {
            'cpu_usage': random.uniform(30, 50),
            'memory_usage': random.uniform(40, 60),
            'response_time_ms': random.uniform(10, 50),
            'error_rate': 0.001
        })
        
    async def _simulate_database_slowdown(self, experiment: ChaosEvent):
        """Simulate database performance degradation"""
        slowdown_factor = experiment.parameters.get('slowdown_factor', 10)
        
        # Affect all database-dependent services
        for service_name, service in self.service_mesh.services.items():
            deps = self.service_mesh.dependencies.get(service_name, [])
            if 'main-database' in deps or service.service_type == ServiceType.DATABASE:
                original_latency = service.response_time_ms
                self.service_mesh.update_service_health(service_name, {
                    'response_time_ms': original_latency * slowdown_factor
                })
                
        await asyncio.sleep(experiment.duration.total_seconds())
        
        # Restore
        for service_name, service in self.service_mesh.services.items():
            deps = self.service_mesh.dependencies.get(service_name, [])
            if 'main-database' in deps or service.service_type == ServiceType.DATABASE:
                self.service_mesh.update_service_health(service_name, {
                    'response_time_ms': random.uniform(10, 50)
                })
                
    async def _monitor_impact(self, experiment: ChaosEvent) -> Dict[str, Any]:
        """Monitor impact during experiment"""
        impact_metrics = {
            'service_health': [],
            'player_impact': [],
            'revenue_impact': [],
            'error_rates': []
        }
        
        monitor_interval = 5  # seconds
        elapsed_time = 0
        
        while elapsed_time < experiment.duration.total_seconds():
            # Collect current metrics
            current_health = self._collect_game_health_metrics()
            self.health_metrics_history.append(current_health)
            
            impact_metrics['service_health'].append({
                'timestamp': datetime.now().isoformat(),
                'unhealthy_services': sum(1 for s in self.service_mesh.services.values() if not s.is_healthy),
                'average_latency': np.mean([s.response_time_ms for s in self.service_mesh.services.values()]),
                'average_error_rate': np.mean([s.error_rate for s in self.service_mesh.services.values()])
            })
            
            impact_metrics['player_impact'].append({
                'players_affected': self._estimate_affected_players(experiment),
                'matchmaking_degradation': self._calculate_matchmaking_impact(),
                'game_quality_score': self._calculate_game_quality_score()
            })
            
            await asyncio.sleep(monitor_interval)
            elapsed_time += monitor_interval
            
        return impact_metrics
        
    def _collect_game_health_metrics(self) -> GameHealthMetrics:
        """Collect current game health metrics"""
        # Simulate metric collection
        healthy_services = sum(1 for s in self.service_mesh.services.values() if s.is_healthy)
        total_services = len(self.service_mesh.services)
        
        return GameHealthMetrics(
            timestamp=datetime.now(),
            players_online=random.randint(1000000, 2000000),
            matchmaking_success_rate=0.95 * (healthy_services / total_services),
            average_match_time=30 + random.uniform(-5, 5),
            api_success_rate=1.0 - np.mean([s.error_rate for s in self.service_mesh.services.values()]),
            average_api_latency=np.mean([s.response_time_ms for s in self.service_mesh.services.values()]),
            error_count=random.randint(100, 1000),
            revenue_per_minute=random.uniform(5000, 10000) * (healthy_services / total_services),
            player_reports=random.randint(0, 50)
        )
        
    def _estimate_affected_players(self, experiment: ChaosEvent) -> int:
        """Estimate number of players affected by experiment"""
        service = self.service_mesh.get_service_health(experiment.target_service)
        if not service:
            return 0
            
        # Base estimation on service type and health
        base_impact = {
            ServiceType.AUTH_SERVICE: 1000000,  # Affects all players
            ServiceType.MATCHMAKING: 500000,    # Affects players looking for matches
            ServiceType.GAME_SERVER: 100000,    # Affects active games
            ServiceType.STORE_SERVICE: 200000,  # Affects purchasing players
            ServiceType.CHAT_SERVICE: 300000,   # Affects social features
        }
        
        base = base_impact.get(service.service_type, 50000)
        
        # Adjust based on cascading impact
        cascading = self.service_mesh.calculate_cascading_impact(experiment.target_service)
        impact_factor = sum(cascading.values()) / len(cascading)
        
        return int(base * impact_factor * experiment.severity)
        
    def _calculate_matchmaking_impact(self) -> float:
        """Calculate impact on matchmaking"""
        mm_service = self.service_mesh.get_service_health("matchmaking-service")
        if not mm_service or not mm_service.is_healthy:
            return 1.0  # Complete failure
            
        # Consider dependencies
        auth_service = self.service_mesh.get_service_health("auth-service")
        game_servers = self.service_mesh.get_service_health("game-server-fleet")
        
        if not auth_service or not auth_service.is_healthy:
            return 0.8  # Can't authenticate
            
        if not game_servers or not game_servers.is_healthy:
            return 0.9  # Can't start matches
            
        # Calculate based on latency
        if mm_service.response_time_ms > 5000:
            return 0.5  # Severe degradation
        elif mm_service.response_time_ms > 1000:
            return 0.3  # Moderate degradation
        else:
            return 0.1  # Minor degradation
            
    def _calculate_game_quality_score(self) -> float:
        """Calculate overall game quality score (0-100)"""
        scores = []
        
        # Service availability score
        healthy_services = sum(1 for s in self.service_mesh.services.values() if s.is_healthy)
        availability_score = (healthy_services / len(self.service_mesh.services)) * 100
        scores.append(availability_score)
        
        # Latency score
        avg_latency = np.mean([s.response_time_ms for s in self.service_mesh.services.values()])
        latency_score = max(0, 100 - (avg_latency / 10))  # 1000ms = 0 score
        scores.append(latency_score)
        
        # Error rate score
        avg_error_rate = np.mean([s.error_rate for s in self.service_mesh.services.values()])
        error_score = (1 - avg_error_rate) * 100
        scores.append(error_score)
        
        return np.mean(scores)
        
    def _calculate_recovery_time(self, impact_metrics: Dict[str, Any]) -> float:
        """Calculate time to recover from experiment"""
        # Find when metrics returned to normal
        service_health = impact_metrics.get('service_health', [])
        if not service_health:
            return 0.0
            
        # Look for when all services became healthy again
        for i in range(len(service_health) - 1, -1, -1):
            if service_health[i]['unhealthy_services'] > 0:
                # Found last unhealthy state
                recovery_index = min(i + 1, len(service_health) - 1)
                return recovery_index * 5.0  # 5 seconds per measurement
                
        return 0.0


class BlastRadiusPredictor:
    """Predicts the impact radius of chaos experiments"""
    
    def predict_impact(self, experiment: ChaosEvent, service_mesh: ServiceMesh) -> Dict[str, Any]:
        """Predict impact of chaos experiment"""
        prediction = {
            'affected_services': [],
            'player_impact_estimate': 0,
            'revenue_impact_estimate': 0,
            'recovery_time_estimate': 0,
            'risk_level': 'low'
        }
        
        # Get cascading impact
        cascading_impact = service_mesh.calculate_cascading_impact(experiment.target_service)
        prediction['affected_services'] = list(cascading_impact.keys())
        
        # Estimate player impact
        service = service_mesh.get_service_health(experiment.target_service)
        if service:
            if service.service_type == ServiceType.AUTH_SERVICE:
                prediction['player_impact_estimate'] = 1000000  # All players
                prediction['risk_level'] = 'critical'
            elif service.service_type == ServiceType.MATCHMAKING:
                prediction['player_impact_estimate'] = 500000
                prediction['risk_level'] = 'high'
            elif service.service_type == ServiceType.GAME_SERVER:
                prediction['player_impact_estimate'] = 100000
                prediction['risk_level'] = 'medium'
            else:
                prediction['player_impact_estimate'] = 50000
                prediction['risk_level'] = 'low'
                
        # Estimate revenue impact
        prediction['revenue_impact_estimate'] = prediction['player_impact_estimate'] * 0.01  # $0.01 per affected player
        
        # Estimate recovery time
        if experiment.experiment_type == ChaosExperiment.SERVICE_FAILURE:
            prediction['recovery_time_estimate'] = 300  # 5 minutes
        elif experiment.experiment_type == ChaosExperiment.DATABASE_SLOWDOWN:
            prediction['recovery_time_estimate'] = 600  # 10 minutes
        else:
            prediction['recovery_time_estimate'] = 120  # 2 minutes
            
        return prediction


class ChaosTestRunner:
    """Runs chaos test scenarios"""
    
    def __init__(self):
        self.service_mesh = ServiceMesh()
        self.orchestrator = ChaosOrchestrator(self.service_mesh)
        
    async def run_game_day_scenario(self) -> Dict[str, Any]:
        """Run a complete game day chaos scenario"""
        logger.info("Starting Game Day Chaos Scenario")
        
        results = {
            'experiments': [],
            'overall_impact': {},
            'lessons_learned': []
        }
        
        # Scenario: Cascading failure during peak hours
        experiments = [
            # Phase 1: Database slowdown
            ChaosEvent(
                experiment_type=ChaosExperiment.DATABASE_SLOWDOWN,
                target_service="main-database",
                start_time=datetime.now(),
                duration=timedelta(minutes=5),
                severity=0.7,
                parameters={'slowdown_factor': 5}
            ),
            
            # Phase 2: Cache layer failure
            ChaosEvent(
                experiment_type=ChaosExperiment.SERVICE_FAILURE,
                target_service="cache-layer",
                start_time=datetime.now() + timedelta(minutes=3),
                duration=timedelta(minutes=3),
                severity=1.0
            ),
            
            # Phase 3: Matchmaking degradation
            ChaosEvent(
                experiment_type=ChaosExperiment.LATENCY_INJECTION,
                target_service="matchmaking-service",
                start_time=datetime.now() + timedelta(minutes=5),
                duration=timedelta(minutes=5),
                severity=0.5,
                parameters={'added_latency_ms': 3000}
            )
        ]
        
        # Run experiments
        for experiment in experiments:
            logger.info(f"Running experiment: {experiment.experiment_type.value}")
            result = await self.orchestrator.run_experiment(experiment)
            results['experiments'].append(result)
            
            # Wait between experiments
            await asyncio.sleep(30)
            
        # Analyze overall impact
        results['overall_impact'] = self._analyze_scenario_impact(results['experiments'])
        
        # Generate lessons learned
        results['lessons_learned'] = self._generate_lessons_learned(results)
        
        return results
        
    def _analyze_scenario_impact(self, experiment_results: List[Dict]) -> Dict[str, Any]:
        """Analyze overall impact of scenario"""
        total_players_affected = sum(
            r['actual_impact']['player_impact'][-1]['players_affected'] 
            for r in experiment_results
            if r['actual_impact']['player_impact']
        )
        
        max_services_affected = max(
            len(r['predicted_impact']['affected_services']) 
            for r in experiment_results
        )
        
        total_recovery_time = sum(
            r['recovery_time'] 
            for r in experiment_results
        )
        
        return {
            'total_players_affected': total_players_affected,
            'max_services_affected': max_services_affected,
            'total_recovery_time': total_recovery_time,
            'scenario_duration': sum(
                r['experiment'].duration.total_seconds() 
                for r in experiment_results
            )
        }
        
    def _generate_lessons_learned(self, results: Dict) -> List[str]:
        """Generate lessons learned from chaos testing"""
        lessons = []
        
        # Check for cascading failures
        if results['overall_impact']['max_services_affected'] > 3:
            lessons.append(
                "Cascading failures detected: Consider implementing circuit breakers "
                "and bulkheads between services"
            )
            
        # Check recovery time
        if results['overall_impact']['total_recovery_time'] > 600:
            lessons.append(
                "Long recovery time detected: Implement faster failover mechanisms "
                "and automated recovery procedures"
            )
            
        # Check specific experiments
        for exp_result in results['experiments']:
            exp = exp_result['experiment']
            if exp.experiment_type == ChaosExperiment.DATABASE_SLOWDOWN:
                lessons.append(
                    "Database is a critical bottleneck: Consider read replicas, "
                    "caching strategies, and database connection pooling"
                )
            elif exp.experiment_type == ChaosExperiment.SERVICE_FAILURE:
                if exp.target_service == "cache-layer":
                    lessons.append(
                        "Cache layer is critical: Implement cache warming strategies "
                        "and fallback to database with rate limiting"
                    )
                    
        return lessons
        
    def generate_report(self, results: Dict) -> str:
        """Generate chaos testing report"""
        report = """
=== Game Day Chaos Testing Report ===

Executive Summary:
-----------------
"""
        
        # Add impact summary
        impact = results['overall_impact']
        report += f"Total Players Affected: {impact['total_players_affected']:,}\n"
        report += f"Maximum Services Affected: {impact['max_services_affected']}\n"
        report += f"Total Recovery Time: {impact['total_recovery_time']:.1f} seconds\n"
        report += f"Scenario Duration: {impact['scenario_duration']:.1f} seconds\n"
        
        # Add experiment details
        report += "\nExperiment Results:\n"
        report += "-" * 50 + "\n"
        
        for i, exp_result in enumerate(results['experiments']):
            exp = exp_result['experiment']
            report += f"\nExperiment {i+1}: {exp.experiment_type.value}\n"
            report += f"Target: {exp.target_service}\n"
            report += f"Duration: {exp.duration.total_seconds()}s\n"
            report += f"Severity: {exp.severity}\n"
            
            predicted = exp_result['predicted_impact']
            report += f"Predicted Impact: {predicted['risk_level']} risk, "
            report += f"{predicted['player_impact_estimate']:,} players\n"
            
            actual = exp_result['actual_impact']
            if actual['player_impact']:
                actual_players = actual['player_impact'][-1]['players_affected']
                report += f"Actual Impact: {actual_players:,} players affected\n"
                
        # Add lessons learned
        report += "\nLessons Learned:\n"
        report += "-" * 50 + "\n"
        for lesson in results['lessons_learned']:
            report += f"• {lesson}\n"
            
        # Add recommendations
        report += "\nRecommendations:\n"
        report += "-" * 50 + "\n"
        report += "1. Implement automated chaos testing in staging environment\n"
        report += "2. Create runbooks for each failure scenario\n"
        report += "3. Set up alerts for early detection of cascading failures\n"
        report += "4. Regular game day exercises with the operations team\n"
        
        return report


# Demo
async def demo():
    """Demonstrate chaos testing capabilities"""
    print("=== Epic Games Chaos Testing Framework ===\n")
    
    runner = ChaosTestRunner()
    
    print("Running Game Day Chaos Scenario...")
    print("This simulates cascading failures during peak gaming hours\n")
    
    # Run the scenario
    results = await runner.run_game_day_scenario()
    
    # Generate and print report
    report = runner.generate_report(results)
    print(report)
    
    # Save detailed results
    with open('chaos_test_results.json', 'w') as f:
        # Convert results to JSON-serializable format
        json_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_impact': results['overall_impact'],
            'lessons_learned': results['lessons_learned'],
            'experiments': [
                {
                    'type': exp['experiment'].experiment_type.value,
                    'target': exp['experiment'].target_service,
                    'duration': exp['experiment'].duration.total_seconds(),
                    'severity': exp['experiment'].severity,
                    'recovery_time': exp['recovery_time']
                }
                for exp in results['experiments']
            ]
        }
        json.dump(json_results, f, indent=2)
    
    print("\nDetailed results saved to chaos_test_results.json")


if __name__ == "__main__":
    # For production use, this would integrate with Kubernetes operators,
    # AWS Fault Injection Simulator, or similar tools
    asyncio.run(demo())