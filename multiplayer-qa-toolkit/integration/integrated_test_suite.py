#!/usr/bin/env python3
"""
Integrated Multiplayer Testing Suite
Epic Games QA Toolkit

Demonstrates how to combine all tools for comprehensive multiplayer game testing
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from network_simulator.network_simulator import NetworkConditionSimulator, NetworkCondition
from prediction_tester.prediction_tester import PredictionTestFramework
from lag_compensation.lag_compensation_tester import LagCompensationTester
from api_loadtest.api_loadtest import LoadTestRunner, LoadProfile
from packet_analyzer.packet_analyzer import PacketFlowAnalyzer, NetworkMetrics, GameProtocolParser
from chaos_testing.chaos_testing import ChaosTestRunner, ChaosEvent, ChaosExperiment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegratedTestSuite:
    """Orchestrates comprehensive multiplayer game testing"""
    
    def __init__(self, game_name: str = "Epic Multiplayer Game"):
        self.game_name = game_name
        self.test_results = {
            'game': game_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
    async def run_pre_launch_validation(self) -> Dict[str, Any]:
        """Complete pre-launch validation suite"""
        logger.info(f"Starting pre-launch validation for {self.game_name}")
        
        # Phase 1: Network condition testing across regions
        network_results = await self._test_global_network_conditions()
        self.test_results['tests']['network_conditions'] = network_results
        
        # Phase 2: Prediction accuracy under various conditions
        prediction_results = await self._test_prediction_accuracy()
        self.test_results['tests']['prediction_accuracy'] = prediction_results
        
        # Phase 3: Lag compensation fairness
        lag_comp_results = await self._test_lag_compensation_fairness()
        self.test_results['tests']['lag_compensation'] = lag_comp_results
        
        # Phase 4: API load testing with launch day simulation
        load_results = await self._test_launch_day_load()
        self.test_results['tests']['load_testing'] = load_results
        
        # Phase 5: Chaos testing for resilience
        chaos_results = await self._test_infrastructure_resilience()
        self.test_results['tests']['chaos_engineering'] = chaos_results
        
        # Generate comprehensive report
        report = self._generate_launch_readiness_report()
        
        return {
            'results': self.test_results,
            'report': report,
            'launch_ready': self._evaluate_launch_readiness()
        }
        
    async def run_competitive_integrity_test(self) -> Dict[str, Any]:
        """Test competitive fairness across different network conditions"""
        logger.info("Running competitive integrity tests")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'scenarios': []
        }
        
        # Test scenarios with different player conditions
        scenarios = [
            {
                'name': 'Low vs High Latency',
                'player1': {'latency': 10, 'jitter': 2, 'loss': 0},
                'player2': {'latency': 150, 'jitter': 20, 'loss': 0.02}
            },
            {
                'name': 'Stable vs Unstable',
                'player1': {'latency': 50, 'jitter': 5, 'loss': 0},
                'player2': {'latency': 50, 'jitter': 30, 'loss': 0.05}
            },
            {
                'name': 'Regional Differences',
                'player1': {'latency': 20, 'jitter': 3, 'loss': 0},  # NA East
                'player2': {'latency': 180, 'jitter': 15, 'loss': 0.01}  # SEA
            }
        ]
        
        for scenario in scenarios:
            logger.info(f"Testing scenario: {scenario['name']}")
            
            # Run lag compensation test
            lag_tester = LagCompensationTester()
            lag_result = await lag_tester.run_competitive_scenario(
                player1_conditions=scenario['player1'],
                player2_conditions=scenario['player2'],
                duration=60.0,
                engagement_rate=0.3
            )
            
            # Run prediction test
            prediction_framework = PredictionTestFramework()
            prediction_result = await prediction_framework.run_competitive_scenario(
                player1_conditions=scenario['player1'],
                player2_conditions=scenario['player2'],
                duration=60.0
            )
            
            results['scenarios'].append({
                'name': scenario['name'],
                'conditions': scenario,
                'lag_compensation': lag_result,
                'prediction': prediction_result,
                'fairness_score': self._calculate_fairness_score(lag_result, prediction_result)
            })
            
        return results
        
    async def run_tournament_readiness_test(self) -> Dict[str, Any]:
        """Test system readiness for tournament conditions"""
        logger.info("Running tournament readiness tests")
        
        # Simulate tournament load pattern
        load_runner = LoadTestRunner(
            base_url="http://api.game.com",
            endpoints=[
                "/match/create",
                "/match/join",
                "/match/status",
                "/leaderboard",
                "/player/stats"
            ]
        )
        
        # Run escalating load test
        tournament_phases = [
            {'name': 'Registration', 'users': 10000, 'duration': 300},
            {'name': 'Warmup', 'users': 50000, 'duration': 600},
            {'name': 'Round 1', 'users': 100000, 'duration': 1800},
            {'name': 'Finals', 'users': 20000, 'duration': 900}
        ]
        
        results = {'phases': []}
        
        for phase in tournament_phases:
            logger.info(f"Testing {phase['name']} phase")
            
            metrics = await load_runner.run_load_test(
                profile=LoadProfile.TOURNAMENT,
                duration=phase['duration'],
                max_users=phase['users']
            )
            
            results['phases'].append({
                'phase': phase['name'],
                'metrics': metrics.to_dict(),
                'sla_violations': self._check_tournament_slas(metrics)
            })
            
        return results
        
    async def _test_global_network_conditions(self) -> Dict[str, Any]:
        """Test game performance across global network conditions"""
        network_sim = NetworkConditionSimulator()
        
        regions = {
            'NA_EAST': NetworkCondition(20, 3, 0.001, 1000),
            'EU_WEST': NetworkCondition(35, 5, 0.001, 1000),
            'ASIA_PACIFIC': NetworkCondition(150, 20, 0.02, 100),
            'SOUTH_AMERICA': NetworkCondition(180, 25, 0.03, 50),
            'MIDDLE_EAST': NetworkCondition(200, 30, 0.04, 30),
            'SATELLITE': NetworkCondition(600, 50, 0.05, 10)
        }
        
        results = {}
        
        for region, condition in regions.items():
            network_sim.current_condition = condition
            
            # Simulate game session
            packet_sim = network_sim.create_game_packet_simulator()
            
            for _ in range(1000):  # 1000 packets
                packet_sim.send_position_update(1, 100.0, 50.0, 200.0)
                packet_sim.send_player_action(1, "shoot")
                
            metrics = network_sim.get_metrics()
            
            results[region] = {
                'condition': {
                    'latency': condition.latency_ms,
                    'jitter': condition.jitter_ms,
                    'loss': condition.packet_loss_rate
                },
                'metrics': metrics,
                'playability_score': self._calculate_playability_score(metrics)
            }
            
        return results
        
    async def _test_prediction_accuracy(self) -> Dict[str, Any]:
        """Test client-side prediction under various conditions"""
        framework = PredictionTestFramework()
        
        test_conditions = [
            {'name': 'Ideal', 'latency': 20, 'jitter': 2, 'loss': 0},
            {'name': 'Good', 'latency': 50, 'jitter': 10, 'loss': 0.01},
            {'name': 'Acceptable', 'latency': 100, 'jitter': 20, 'loss': 0.02},
            {'name': 'Poor', 'latency': 200, 'jitter': 50, 'loss': 0.05}
        ]
        
        results = {}
        
        for condition in test_conditions:
            result = await framework.run_test_scenario(
                duration=60.0,
                latency_ms=condition['latency'],
                latency_jitter_ms=condition['jitter'],
                packet_loss_rate=condition['loss'],
                input_pattern="combat"  # Realistic combat movement
            )
            
            results[condition['name']] = {
                'condition': condition,
                'metrics': result['metrics'],
                'acceptable': result['metrics']['prediction_accuracy'] > 0.9
            }
            
        return results
        
    async def _test_lag_compensation_fairness(self) -> Dict[str, Any]:
        """Test lag compensation fairness across player conditions"""
        tester = LagCompensationTester()
        
        result = await tester.run_test_scenario(
            num_players=50,
            duration=120.0,
            latency_range=(10, 200),
            movement_pattern="combat",
            shots_per_second=1.0
        )
        
        # Analyze fairness
        hit_rates_by_latency = {}
        for shot in result['shot_log']:
            latency_bucket = (shot['shooter_latency'] // 50) * 50
            if latency_bucket not in hit_rates_by_latency:
                hit_rates_by_latency[latency_bucket] = {'hits': 0, 'total': 0}
            
            hit_rates_by_latency[latency_bucket]['total'] += 1
            if shot['hit']:
                hit_rates_by_latency[latency_bucket]['hits'] += 1
                
        fairness_analysis = {
            'overall_hit_rate': result['results']['hit_rate'],
            'hit_rates_by_latency': {
                k: v['hits'] / v['total'] if v['total'] > 0 else 0
                for k, v in hit_rates_by_latency.items()
            },
            'false_positive_rate': result['results']['false_positive_rate'],
            'false_negative_rate': result['results']['false_negative_rate']
        }
        
        return fairness_analysis
        
    async def _test_launch_day_load(self) -> Dict[str, Any]:
        """Simulate launch day load patterns"""
        load_runner = LoadTestRunner(
            base_url="http://api.game.com",
            endpoints=[
                "/auth/login",
                "/match/find",
                "/match/join",
                "/player/profile",
                "/store/items",
                "/leaderboard/global"
            ]
        )
        
        # Simulate 6-hour launch window
        phases = [
            {'hour': 1, 'users': 100000, 'profile': LoadProfile.GAME_LAUNCH},
            {'hour': 2, 'users': 500000, 'profile': LoadProfile.SPIKE},
            {'hour': 3, 'users': 1000000, 'profile': LoadProfile.SPIKE},
            {'hour': 4, 'users': 800000, 'profile': LoadProfile.SUSTAINED},
            {'hour': 5, 'users': 600000, 'profile': LoadProfile.SUSTAINED},
            {'hour': 6, 'users': 500000, 'profile': LoadProfile.SUSTAINED}
        ]
        
        results = {'phases': [], 'peak_metrics': None}
        peak_throughput = 0
        
        for phase in phases:
            logger.info(f"Simulating hour {phase['hour']} with {phase['users']:,} users")
            
            metrics = await load_runner.run_load_test(
                profile=phase['profile'],
                duration=300,  # 5 minutes per phase for demo
                max_users=phase['users']
            )
            
            phase_result = {
                'hour': phase['hour'],
                'users': phase['users'],
                'metrics': metrics.to_dict(),
                'errors': metrics.error_count,
                'throughput': metrics.throughput
            }
            
            results['phases'].append(phase_result)
            
            if metrics.throughput > peak_throughput:
                peak_throughput = metrics.throughput
                results['peak_metrics'] = metrics.to_dict()
                
        return results
        
    async def _test_infrastructure_resilience(self) -> Dict[str, Any]:
        """Test infrastructure resilience with chaos engineering"""
        chaos_runner = ChaosTestRunner()
        
        # Run game day scenario
        chaos_results = await chaos_runner.run_game_day_scenario()
        
        # Analyze impact
        resilience_score = 100.0
        
        for experiment in chaos_results['experiments']:
            impact = experiment['actual_impact']
            
            # Deduct points based on impact
            if impact['player_impact']:
                players_affected = impact['player_impact'][-1]['players_affected']
                resilience_score -= (players_affected / 1000000) * 10  # -10 points per million affected
                
            recovery_time = experiment['recovery_time']
            if recovery_time > 300:  # More than 5 minutes
                resilience_score -= 5
                
        return {
            'chaos_results': chaos_results,
            'resilience_score': max(0, resilience_score),
            'critical_vulnerabilities': self._identify_critical_vulnerabilities(chaos_results)
        }
        
    def _calculate_playability_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate playability score based on network metrics"""
        score = 100.0
        
        # Latency impact
        avg_latency = metrics.get('average_latency', 0)
        if avg_latency > 50:
            score -= min((avg_latency - 50) / 10, 30)  # Max -30 points
            
        # Jitter impact
        avg_jitter = metrics.get('average_jitter', 0)
        if avg_jitter > 10:
            score -= min((avg_jitter - 10) / 5, 20)  # Max -20 points
            
        # Loss impact
        loss_rate = metrics.get('loss_rate', 0)
        if loss_rate > 0.01:
            score -= min(loss_rate * 1000, 50)  # Max -50 points
            
        return max(0, score)
        
    def _calculate_fairness_score(self, lag_result: Dict, prediction_result: Dict) -> float:
        """Calculate competitive fairness score"""
        score = 100.0
        
        # Check hit rate difference between players
        if 'player_hit_rates' in lag_result:
            hit_rates = list(lag_result['player_hit_rates'].values())
            if hit_rates:
                hit_rate_variance = max(hit_rates) - min(hit_rates)
                score -= hit_rate_variance * 100  # Penalize variance
                
        # Check prediction accuracy difference
        if 'player_accuracies' in prediction_result:
            accuracies = list(prediction_result['player_accuracies'].values())
            if accuracies:
                accuracy_variance = max(accuracies) - min(accuracies)
                score -= accuracy_variance * 50
                
        return max(0, score)
        
    def _check_tournament_slas(self, metrics) -> List[str]:
        """Check if metrics meet tournament SLAs"""
        violations = []
        
        percentiles = metrics.calculate_percentiles()
        
        if percentiles['p99'] > 1000:  # 1 second
            violations.append(f"P99 latency {percentiles['p99']:.0f}ms exceeds 1000ms SLA")
            
        if metrics.error_rate > 0.001:  # 0.1%
            violations.append(f"Error rate {metrics.error_rate*100:.2f}% exceeds 0.1% SLA")
            
        if metrics.throughput < 1000:  # 1000 req/s minimum
            violations.append(f"Throughput {metrics.throughput:.0f} req/s below 1000 req/s SLA")
            
        return violations
        
    def _identify_critical_vulnerabilities(self, chaos_results: Dict) -> List[str]:
        """Identify critical vulnerabilities from chaos testing"""
        vulnerabilities = []
        
        for experiment in chaos_results['experiments']:
            exp_type = experiment['experiment'].experiment_type.value
            impact = experiment['actual_impact']
            
            if impact['player_impact']:
                affected = impact['player_impact'][-1]['players_affected']
                if affected > 500000:
                    vulnerabilities.append(
                        f"{exp_type} can affect {affected:,} players"
                    )
                    
            if experiment['recovery_time'] > 600:  # 10 minutes
                vulnerabilities.append(
                    f"{exp_type} has {experiment['recovery_time']/60:.1f} minute recovery time"
                )
                
        return vulnerabilities
        
    def _evaluate_launch_readiness(self) -> Dict[str, Any]:
        """Evaluate overall launch readiness"""
        criteria = {
            'network_performance': True,
            'prediction_accuracy': True,
            'lag_compensation_fairness': True,
            'load_capacity': True,
            'infrastructure_resilience': True
        }
        
        # Check network performance
        if 'network_conditions' in self.test_results['tests']:
            for region, data in self.test_results['tests']['network_conditions'].items():
                if data['playability_score'] < 70:
                    criteria['network_performance'] = False
                    break
                    
        # Check prediction accuracy
        if 'prediction_accuracy' in self.test_results['tests']:
            for condition, data in self.test_results['tests']['prediction_accuracy'].items():
                if not data['acceptable']:
                    criteria['prediction_accuracy'] = False
                    break
                    
        # Check lag compensation
        if 'lag_compensation' in self.test_results['tests']:
            lag_data = self.test_results['tests']['lag_compensation']
            if lag_data['false_positive_rate'] > 0.05 or lag_data['false_negative_rate'] > 0.1:
                criteria['lag_compensation_fairness'] = False
                
        # Check load capacity
        if 'load_testing' in self.test_results['tests']:
            load_data = self.test_results['tests']['load_testing']
            if load_data['peak_metrics'] and load_data['peak_metrics']['error_rate'] > 0.01:
                criteria['load_capacity'] = False
                
        # Check resilience
        if 'chaos_engineering' in self.test_results['tests']:
            chaos_data = self.test_results['tests']['chaos_engineering']
            if chaos_data['resilience_score'] < 80:
                criteria['infrastructure_resilience'] = False
                
        all_passed = all(criteria.values())
        
        return {
            'ready': all_passed,
            'criteria': criteria,
            'recommendation': 'LAUNCH' if all_passed else 'DELAY_LAUNCH',
            'confidence': sum(criteria.values()) / len(criteria) * 100
        }
        
    def _generate_launch_readiness_report(self) -> str:
        """Generate comprehensive launch readiness report"""
        readiness = self._evaluate_launch_readiness()
        
        report = f"""
=== {self.game_name} Launch Readiness Report ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
-----------------
Launch Recommendation: {readiness['recommendation']}
Confidence Level: {readiness['confidence']:.0f}%

DETAILED RESULTS
----------------

1. Network Performance Testing
"""
        
        if 'network_conditions' in self.test_results['tests']:
            for region, data in self.test_results['tests']['network_conditions'].items():
                report += f"   {region}: Playability Score {data['playability_score']:.0f}/100\n"
                
        report += "\n2. Client-Side Prediction\n"
        
        if 'prediction_accuracy' in self.test_results['tests']:
            for condition, data in self.test_results['tests']['prediction_accuracy'].items():
                accuracy = data['metrics']['prediction_accuracy'] * 100
                report += f"   {condition}: {accuracy:.1f}% accuracy\n"
                
        report += "\n3. Lag Compensation Fairness\n"
        
        if 'lag_compensation' in self.test_results['tests']:
            lag_data = self.test_results['tests']['lag_compensation']
            report += f"   Overall Hit Rate: {lag_data['overall_hit_rate']*100:.1f}%\n"
            report += f"   False Positives: {lag_data['false_positive_rate']*100:.1f}%\n"
            report += f"   False Negatives: {lag_data['false_negative_rate']*100:.1f}%\n"
            
        report += "\n4. Load Testing Results\n"
        
        if 'load_testing' in self.test_results['tests']:
            load_data = self.test_results['tests']['load_testing']
            if load_data['peak_metrics']:
                peak = load_data['peak_metrics']
                report += f"   Peak Throughput: {peak['throughput']:.0f} req/s\n"
                report += f"   Peak Error Rate: {peak['error_rate']*100:.2f}%\n"
                
        report += "\n5. Infrastructure Resilience\n"
        
        if 'chaos_engineering' in self.test_results['tests']:
            chaos_data = self.test_results['tests']['chaos_engineering']
            report += f"   Resilience Score: {chaos_data['resilience_score']:.0f}/100\n"
            
            if chaos_data['critical_vulnerabilities']:
                report += "   Critical Vulnerabilities:\n"
                for vuln in chaos_data['critical_vulnerabilities']:
                    report += f"   - {vuln}\n"
                    
        report += "\nRECOMMENDATIONS\n"
        report += "---------------\n"
        
        if not readiness['ready']:
            report += "⚠️  Address the following before launch:\n"
            for criterion, passed in readiness['criteria'].items():
                if not passed:
                    report += f"   - Fix {criterion.replace('_', ' ').title()}\n"
        else:
            report += "✅ All systems are GO for launch!\n"
            
        return report


# Demo functions
async def demo_pre_launch_validation():
    """Demo pre-launch validation suite"""
    print("=== Epic Games Pre-Launch Validation Demo ===\n")
    
    suite = IntegratedTestSuite("Fortnite Chapter 5")
    
    print("Running comprehensive pre-launch validation...")
    print("This simulates all critical tests before a major game launch\n")
    
    # Note: This is a demo with reduced durations
    # Real tests would run for hours/days
    
    results = await suite.run_pre_launch_validation()
    
    print(results['report'])
    
    # Save detailed results
    with open('pre_launch_validation_results.json', 'w') as f:
        json.dump(results['results'], f, indent=2, default=str)
        
    print("\nDetailed results saved to pre_launch_validation_results.json")
    
    return results


async def demo_competitive_integrity():
    """Demo competitive integrity testing"""
    print("=== Competitive Integrity Testing Demo ===\n")
    
    suite = IntegratedTestSuite("Competitive Shooter")
    
    print("Testing fairness across different network conditions...")
    print("Ensuring competitive integrity for esports\n")
    
    results = await suite.run_competitive_integrity_test()
    
    print("Competitive Fairness Results:")
    print("-" * 50)
    
    for scenario in results['scenarios']:
        print(f"\n{scenario['name']}:")
        print(f"  Fairness Score: {scenario['fairness_score']:.0f}/100")
        
        if scenario['fairness_score'] < 80:
            print("  ⚠️  Fairness concerns detected!")
        else:
            print("  ✅ Acceptable fairness level")
            
    # Save results
    with open('competitive_integrity_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    print("\nDetailed results saved to competitive_integrity_results.json")
    
    return results


async def demo_tournament_readiness():
    """Demo tournament infrastructure testing"""
    print("=== Tournament Readiness Testing Demo ===\n")
    
    suite = IntegratedTestSuite("Battle Royale Tournament")
    
    print("Testing infrastructure for major tournament event...")
    print("Simulating 100,000 concurrent players\n")
    
    results = await suite.run_tournament_readiness_test()
    
    print("Tournament Infrastructure Results:")
    print("-" * 50)
    
    for phase in results['phases']:
        print(f"\n{phase['phase']}:")
        print(f"  Players: {phase['users']:,}")
        print(f"  Throughput: {phase['throughput']:.0f} req/s")
        print(f"  Errors: {phase['errors']}")
        
        if phase['sla_violations']:
            print("  ⚠️  SLA Violations:")
            for violation in phase['sla_violations']:
                print(f"    - {violation}")
        else:
            print("  ✅ All SLAs met")
            
    # Save results
    with open('tournament_readiness_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    print("\nDetailed results saved to tournament_readiness_results.json")
    
    return results


# Main demo selector
async def main():
    """Run integrated test suite demos"""
    print("=== Epic Games Integrated Testing Suite ===\n")
    print("Select a demo:")
    print("1. Pre-Launch Validation (Comprehensive)")
    print("2. Competitive Integrity Testing")
    print("3. Tournament Readiness Testing")
    print("4. Run All Demos")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice == '1':
        await demo_pre_launch_validation()
    elif choice == '2':
        await demo_competitive_integrity()
    elif choice == '3':
        await demo_tournament_readiness()
    elif choice == '4':
        print("\nRunning all demos...\n")
        await demo_pre_launch_validation()
        print("\n" + "="*70 + "\n")
        await demo_competitive_integrity()
        print("\n" + "="*70 + "\n")
        await demo_tournament_readiness()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    # Note: These are demo functions with reduced durations
    # Production tests would run much longer
    asyncio.run(main())