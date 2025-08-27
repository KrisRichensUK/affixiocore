#!/usr/bin/env python3

import requests
import time
import threading
import statistics
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import argparse
import sys

class SimpleStressTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.lock = threading.Lock()
        
        # Test data for verification requests
        self.test_codes = [
            "SEC001", "SEC002", "SEC003", "SEC004", "SEC005", "SEC006",
            "TEST123", "DEMO001", "DEMO002", "DEMO003", "DEMO004", "DEMO005"
        ]
        
        self.jurisdictions = ["UK", "US", "EU", "CA", "AU"]
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SimpleStressTester/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def make_request(self, request_type: str) -> Dict[str, Any]:
        """Make a single request and return timing data"""
        start_time = time.time()
        success = False
        error = None
        status_code = 0
        response_time = 0
        
        try:
            if request_type == "health":
                response = self.session.get(f"{self.base_url}/health", timeout=10)
                status_code = response.status_code
                response_time = time.time() - start_time
                if response.status_code == 200:
                    success = True
            
            elif request_type == "verify":
                payload = {
                    "secure_code": random.choice(self.test_codes),
                    "jurisdiction": random.choice(self.jurisdictions)
                }
                
                response = self.session.post(f"{self.base_url}/api/v1/verify", 
                                           json=payload, timeout=10)
                status_code = response.status_code
                response_time = time.time() - start_time
                if response.status_code in [200, 201]:
                    success = True
            
            elif request_type == "rules":
                response = self.session.get(f"{self.base_url}/api/v1/rules", timeout=10)
                status_code = response.status_code
                response_time = time.time() - start_time
                if response.status_code == 200:
                    success = True
            
            elif request_type == "endpoints":
                response = self.session.get(f"{self.base_url}/api/v1/endpoints", timeout=10)
                status_code = response.status_code
                response_time = time.time() - start_time
                if response.status_code == 200:
                    success = True
            
        except Exception as e:
            error = str(e)
            response_time = time.time() - start_time
        
        result = {
            "type": request_type,
            "success": success,
            "status_code": status_code,
            "response_time": response_time,
            "error": error,
            "timestamp": start_time
        }
        
        with self.lock:
            self.results.append(result)
        
        return result
    
    def worker(self, request_type: str, duration: int, rps: int):
        """Worker function that makes requests at specified RPS"""
        start_time = time.time()
        request_count = 0
        interval = 1.0 / rps
        
        while time.time() - start_time < duration:
            request_start = time.time()
            
            # Make the request
            self.make_request(request_type)
            request_count += 1
            
            # Calculate sleep time to maintain RPS
            elapsed = time.time() - request_start
            sleep_time = max(0, interval - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def run_stress_test(self, 
                       total_duration: int = 60,
                       rps: int = 1000,
                       concurrent_workers: int = 50,
                       request_types: List[str] = None):
        """Run the massive stress test"""
        
        if request_types is None:
            request_types = ["health", "verify", "rules", "endpoints"]
        
        print(f"🚀 Starting MASSIVE Stress Test")
        print(f"📊 Configuration:")
        print(f"   • Duration: {total_duration} seconds")
        print(f"   • Target RPS: {rps:,} requests/second")
        print(f"   • Concurrent Workers: {concurrent_workers}")
        print(f"   • Request Types: {', '.join(request_types)}")
        print(f"   • Base URL: {self.base_url}")
        print()
        
        # Start workers
        start_time = time.time()
        threads = []
        
        # Distribute workers across request types
        workers_per_type = concurrent_workers // len(request_types)
        remaining_workers = concurrent_workers % len(request_types)
        
        for i, request_type in enumerate(request_types):
            workers_for_type = workers_per_type + (1 if i < remaining_workers else 0)
            rps_per_worker = rps // concurrent_workers
            
            for _ in range(workers_for_type):
                thread = threading.Thread(
                    target=self.worker,
                    args=(request_type, total_duration, rps_per_worker)
                )
                thread.start()
                threads.append(thread)
        
        # Wait for all workers to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate statistics
        self.print_results(actual_duration)
    
    def print_results(self, actual_duration: float):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("📈 MASSIVE STRESS TEST RESULTS")
        print("="*80)
        
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r["success"])
        failed_requests = total_requests - successful_requests
        
        # Calculate RPS
        actual_rps = total_requests / actual_duration if actual_duration > 0 else 0
        
        # Response time statistics
        response_times = [r["response_time"] for r in self.results if r["success"]]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_response_time
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max_response_time
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        # Status code distribution
        status_codes = {}
        for result in self.results:
            status = result["status_code"]
            status_codes[status] = status_codes.get(status, 0) + 1
        
        # Request type distribution
        request_types = {}
        for result in self.results:
            req_type = result["type"]
            request_types[req_type] = request_types.get(req_type, 0) + 1
        
        # Print summary
        print(f"⏱️  Test Duration: {actual_duration:.2f} seconds")
        print(f"📊 Total Requests: {total_requests:,}")
        print(f"✅ Successful Requests: {successful_requests:,} ({successful_requests/total_requests*100:.1f}%)")
        print(f"❌ Failed Requests: {failed_requests:,} ({failed_requests/total_requests*100:.1f}%)")
        print(f"🚀 Actual RPS: {actual_rps:.1f}")
        print()
        
        # Response time statistics
        print("⏱️  Response Time Statistics:")
        print(f"   • Average: {avg_response_time*1000:.2f} ms")
        print(f"   • Median: {median_response_time*1000:.2f} ms")
        print(f"   • Min: {min_response_time*1000:.2f} ms")
        print(f"   • Max: {max_response_time*1000:.2f} ms")
        print(f"   • 95th Percentile: {p95_response_time*1000:.2f} ms")
        print(f"   • 99th Percentile: {p99_response_time*1000:.2f} ms")
        print()
        
        # Status code distribution
        print("📊 Status Code Distribution:")
        for status, count in sorted(status_codes.items()):
            percentage = count / total_requests * 100
            print(f"   • {status}: {count:,} ({percentage:.1f}%)")
        print()
        
        # Request type distribution
        print("🔍 Request Type Distribution:")
        for req_type, count in sorted(request_types.items()):
            percentage = count / total_requests * 100
            print(f"   • {req_type}: {count:,} ({percentage:.1f}%)")
        print()
        
        # Performance assessment
        print("🎯 Performance Assessment:")
        if actual_rps >= 1000:
            print("   🟢 EXCELLENT: Achieved 1000+ RPS")
        elif actual_rps >= 500:
            print("   🟡 GOOD: Achieved 500+ RPS")
        elif actual_rps >= 100:
            print("   🟠 FAIR: Achieved 100+ RPS")
        else:
            print("   🔴 POOR: Below 100 RPS")
        
        if avg_response_time < 0.1:
            print("   🟢 EXCELLENT: Average response time < 100ms")
        elif avg_response_time < 0.5:
            print("   🟡 GOOD: Average response time < 500ms")
        elif avg_response_time < 1.0:
            print("   🟠 FAIR: Average response time < 1s")
        else:
            print("   🔴 POOR: Average response time > 1s")
        
        if successful_requests / total_requests > 0.95:
            print("   🟢 EXCELLENT: Success rate > 95%")
        elif successful_requests / total_requests > 0.90:
            print("   🟡 GOOD: Success rate > 90%")
        elif successful_requests / total_requests > 0.80:
            print("   🟠 FAIR: Success rate > 80%")
        else:
            print("   🔴 POOR: Success rate < 80%")
        
        print("\n" + "="*80)
        
        # Save detailed results to file
        results_file = f"stress_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "duration": actual_duration,
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "actual_rps": actual_rps,
                    "avg_response_time": avg_response_time,
                    "median_response_time": median_response_time,
                    "p95_response_time": p95_response_time,
                    "p99_response_time": p99_response_time
                },
                "status_codes": status_codes,
                "request_types": request_types,
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: {results_file}")

def main():
    parser = argparse.ArgumentParser(description="Simple Stress Test for Affixio Engine")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--rps", type=int, default=500, help="Target requests per second")
    parser.add_argument("--workers", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to test")
    parser.add_argument("--types", nargs="+", default=["health", "verify", "rules", "endpoints"], 
                       help="Request types to test")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.rps < 1:
        print("❌ Error: RPS must be at least 1")
        sys.exit(1)
    
    if args.duration < 1:
        print("❌ Error: Duration must be at least 1 second")
        sys.exit(1)
    
    if args.workers < 1:
        print("❌ Error: Workers must be at least 1")
        sys.exit(1)
    
    # Create and run stress tester
    tester = SimpleStressTester(args.url)
    
    try:
        tester.run_stress_test(
            total_duration=args.duration,
            rps=args.rps,
            concurrent_workers=args.workers,
            request_types=args.types
        )
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
