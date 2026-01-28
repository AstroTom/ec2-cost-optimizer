#!/usr/bin/env python3 

"""
Enhanced EC2 Cost Optimization Recommendations Script
- Uses AWS Pricing API for real-time pricing
- Integrates CloudWatch metrics for utilization analysis
- Broader instance type coverage
- Region-aware pricing
"""

import boto3
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

class EC2CostOptimizer:
    def __init__(self, session, region=None):
        self.session = session
        
        # Determine region - boto3 session already handles this properly
        if region:
            self.region = region
        else:
            # Let boto3 determine the region from the session
            # It will check: profile config, environment vars, default region
            self.region = session.region_name
            
            # If still no region, try environment variable or fallback
            if not self.region:
                self.region = os.environ.get('AWS_DEFAULT_REGION') or os.environ.get('AWS_REGION') or 'us-east-1'
        
        print(f"Using region: {self.region}")
        
        self.ec2 = session.client('ec2', region_name=self.region)
        self.cloudwatch = session.client('cloudwatch', region_name=self.region)
        self.pricing = session.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
        self.pricing_cache = {}
        
    def get_instance_price(self, instance_type, region=None):
        """Get real-time pricing from AWS Pricing API"""
        if region is None:
            region = self.region
            
        cache_key = f"{instance_type}_{region}"
        if cache_key in self.pricing_cache:
            return self.pricing_cache[cache_key]
        
        # Map region codes to pricing API region names
        region_map = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-central-1': 'EU (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
        }
        
        region_name = region_map.get(region, region)
        
        try:
            response = self.pricing.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                ],
                MaxResults=1
            )
            
            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                on_demand = price_item['terms']['OnDemand']
                price_dimensions = list(on_demand.values())[0]['priceDimensions']
                price_per_hour = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
                self.pricing_cache[cache_key] = price_per_hour
                return price_per_hour
        except Exception as e:
            print(f"Warning: Could not fetch price for {instance_type}: {e}")
        
        return 0
    
    def get_instance_metrics(self, instance_id, days=14):
        """Get CloudWatch metrics for CPU and network utilization"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        try:
            # Get CPU utilization
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average', 'Maximum']
            )
            
            if cpu_response['Datapoints']:
                cpu_avg = sum(d['Average'] for d in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
                cpu_max = max(d['Maximum'] for d in cpu_response['Datapoints'])
            else:
                cpu_avg = cpu_max = None
            
            return {
                'cpu_avg': cpu_avg,
                'cpu_max': cpu_max,
                'has_data': len(cpu_response['Datapoints']) > 0
            }
        except Exception as e:
            print(f"Warning: Could not fetch metrics for {instance_id}: {e}")
            return {'cpu_avg': None, 'cpu_max': None, 'has_data': False}
    
    def get_alternative_instances(self, current_type, cpu_avg=None):
        """Generate alternative instance type recommendations"""
        alternatives = []
        
        # Parse current instance family and size
        parts = current_type.split('.')
        if len(parts) != 2:
            return alternatives
        
        family, size = parts
        
        # T-series alternatives
        if family.startswith('t3'):
            alternatives.extend([
                (f't4g.{size}', 'Graviton2 ARM - 20% cheaper', 'graviton'),
                (f't3a.{size}', 'AMD - 10% cheaper', 'amd'),
            ])
        elif family.startswith('t2'):
            alternatives.extend([
                (f't3.{size}', 'Newer generation', 'intel'),
                (f't4g.{size}', 'Graviton2 ARM - 20% cheaper', 'graviton'),
            ])
        
        # M-series alternatives
        elif family == 'm5':
            alternatives.extend([
                (f'm7g.{size}', 'Graviton3 - Latest gen', 'graviton'),
                (f'm6a.{size}', 'AMD - 10% cheaper', 'amd'),
                (f'm6i.{size}', 'Intel 6th gen', 'intel'),
            ])
        elif family == 'm6i':
            alternatives.extend([
                (f'm7g.{size}', 'Graviton3 - Better price/perf', 'graviton'),
                (f'm6a.{size}', 'AMD - 10% cheaper', 'amd'),
            ])
        elif family == 'm4':
            alternatives.extend([
                (f'm7g.{size}', 'Graviton3 - Latest', 'graviton'),
                (f'm6i.{size}', 'Intel 6th gen', 'intel'),
                (f'm5.{size}', 'Intel 5th gen', 'intel'),
            ])
        
        # C-series (compute optimized)
        elif family == 'c5':
            alternatives.extend([
                (f'c7g.{size}', 'Graviton3 - Best price/perf', 'graviton'),
                (f'c6a.{size}', 'AMD', 'amd'),
                (f'c6i.{size}', 'Intel 6th gen', 'intel'),
            ])
        elif family == 'c4':
            alternatives.extend([
                (f'c7g.{size}', 'Graviton3', 'graviton'),
                (f'c6i.{size}', 'Intel 6th gen', 'intel'),
            ])
        
        # R-series (memory optimized)
        elif family == 'r5':
            alternatives.extend([
                (f'r7g.{size}', 'Graviton3', 'graviton'),
                (f'r6a.{size}', 'AMD', 'amd'),
                (f'r6i.{size}', 'Intel 6th gen', 'intel'),
            ])
        elif family == 'r4':
            alternatives.extend([
                (f'r7g.{size}', 'Graviton3', 'graviton'),
                (f'r6i.{size}', 'Intel 6th gen', 'intel'),
            ])
        
        # Consider downsizing if CPU utilization is low
        if cpu_avg is not None and cpu_avg < 20:
            downsize_map = {
                'xlarge': 'large',
                'large': 'medium',
                'medium': 'small',
                'small': 'micro',
                '2xlarge': 'xlarge',
                '4xlarge': '2xlarge',
            }
            if size in downsize_map:
                smaller_size = downsize_map[size]
                alternatives.append(
                    (f'{family}.{smaller_size}', f'Downsize (low CPU: {cpu_avg:.1f}%)', 'downsize')
                )
        
        return alternatives
    
    def analyze_instances(self, check_metrics=True):
        """Main analysis function"""
        response = self.ec2.describe_instances()
        
        print("=" * 100)
        print("ENHANCED EC2 COST OPTIMIZATION RECOMMENDATIONS")
        print("=" * 100)
        print(f"Region: {self.region}")
        print(f"Metrics Analysis: {'Enabled' if check_metrics else 'Disabled'}")
        print()
        
        instances_analyzed = 0
        total_current_cost = 0
        total_potential_savings = {
            'graviton': 0,
            'amd': 0,
            'intel': 0,
            'downsize': 0
        }
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                state = instance['State']['Name']
                
                # Skip terminated instances
                if state == 'terminated':
                    continue
                
                # Get instance name
                instance_name = 'N/A'
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            instance_name = tag['Value']
                            break
                
                # Get pricing
                current_price = self.get_instance_price(instance_type, self.region)
                if current_price == 0:
                    continue
                
                current_monthly = current_price * 730
                
                # Get metrics if enabled
                metrics = {'cpu_avg': None, 'cpu_max': None, 'has_data': False}
                if check_metrics and state == 'running':
                    metrics = self.get_instance_metrics(instance_id)
                
                # Get alternatives
                alternatives = self.get_alternative_instances(instance_type, metrics['cpu_avg'])
                if not alternatives:
                    continue
                
                instances_analyzed += 1
                total_current_cost += current_monthly
                
                print(f"Instance: {instance_name}")
                print(f"  ID: {instance_id}")
                print(f"  State: {state}")
                print(f"  Type: {instance_type}")
                print(f"  Cost: ${current_price:.4f}/hour (${current_monthly:.2f}/month)")
                
                if metrics['has_data']:
                    print(f"  CPU Utilization: Avg {metrics['cpu_avg']:.1f}%, Max {metrics['cpu_max']:.1f}%")
                    if metrics['cpu_avg'] < 20:
                        print(f"  ⚠️  Low utilization - consider downsizing")
                    elif metrics['cpu_avg'] > 80:
                        print(f"  ⚠️  High utilization - verify capacity before changing")
                
                print()
                print("  Recommendations:")
                
                best_savings_by_type = defaultdict(float)
                
                for alt_type, description, category in alternatives:
                    alt_price = self.get_instance_price(alt_type, self.region)
                    if alt_price == 0:
                        continue
                    
                    savings_per_hour = current_price - alt_price
                    savings_per_month = savings_per_hour * 730
                    savings_percent = (savings_per_hour / current_price * 100) if current_price > 0 else 0
                    
                    # Track best savings per category
                    if savings_per_month > best_savings_by_type[category]:
                        best_savings_by_type[category] = savings_per_month
                    
                    if savings_per_hour > 0:
                        print(f"    ✓ {alt_type} ({description})")
                        print(f"      ${alt_price:.4f}/hr (${alt_price * 730:.2f}/mo) - Save ${savings_per_month:.2f}/mo ({savings_percent:.1f}%)")
                    elif savings_per_hour < 0:
                        print(f"    → {alt_type} ({description})")
                        print(f"      ${alt_price:.4f}/hr (${alt_price * 730:.2f}/mo) - {abs(savings_percent):.1f}% more but newer")
                    else:
                        print(f"    → {alt_type} ({description})")
                        print(f"      ${alt_price:.4f}/hr - Similar pricing")
                
                # Add to totals
                for category, savings in best_savings_by_type.items():
                    total_potential_savings[category] += savings
                
                print()
                print("-" * 100)
                print()
        
        # Summary
        if instances_analyzed == 0:
            print("No optimization recommendations available.")
        else:
            self.print_summary(instances_analyzed, total_current_cost, total_potential_savings)
    
    def print_summary(self, count, current_cost, savings):
        """Print summary report"""
        print("=" * 100)
        print("SUMMARY")
        print("=" * 100)
        print(f"Instances analyzed: {count}")
        print(f"Current monthly cost: ${current_cost:.2f}")
        print()
        
        if savings['graviton'] > 0:
            pct = (savings['graviton'] / current_cost * 100)
            print(f"💰 Graviton (ARM) Migration Savings: ${savings['graviton']:.2f}/mo ({pct:.1f}%)")
            print(f"   New cost: ${current_cost - savings['graviton']:.2f}/mo")
            print()
        
        if savings['amd'] > 0:
            pct = (savings['amd'] / current_cost * 100)
            print(f"💰 AMD Migration Savings: ${savings['amd']:.2f}/mo ({pct:.1f}%)")
            print(f"   New cost: ${current_cost - savings['amd']:.2f}/mo")
            print()
        
        if savings['downsize'] > 0:
            pct = (savings['downsize'] / current_cost * 100)
            print(f"💰 Downsizing Savings: ${savings['downsize']:.2f}/mo ({pct:.1f}%)")
            print(f"   New cost: ${current_cost - savings['downsize']:.2f}/mo")
            print()
        
        max_savings = max(savings.values())
        if max_savings > 0:
            max_pct = (max_savings / current_cost * 100)
            print(f"🎯 Maximum Potential Savings: ${max_savings:.2f}/mo ({max_pct:.1f}%)")
            print()
        
        print("Notes:")
        print("  • Prices are real-time from AWS Pricing API")
        print("  • Graviton (ARM) requires ARM-compatible software/containers")
        print("  • Test thoroughly in non-production before migrating")
        print("  • Consider Reserved Instances for additional 30-70% savings")
        print("  • Savings Plans offer flexibility with similar discounts")


def main():
    parser = argparse.ArgumentParser(description='Enhanced EC2 Cost Optimizer')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--region', help='AWS region (default: from profile config or us-east-1)')
    parser.add_argument('--no-metrics', action='store_true', help='Skip CloudWatch metrics analysis')
    args = parser.parse_args()
    
    # Create session
    try:
        if args.profile:
            print(f"Using AWS profile: {args.profile}")
            session = boto3.Session(profile_name=args.profile)
        elif os.environ.get('AWS_PROFILE'):
            profile = os.environ.get('AWS_PROFILE')
            print(f"Using AWS profile from environment: {profile}")
            session = boto3.Session(profile_name=profile)
        else:
            print("Using default AWS credentials")
            session = boto3.Session()
        
        # Verify credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"Authenticated as: {identity['Arn']}")
        print()
    except Exception as e:
        print(f"❌ Error: Unable to authenticate with AWS: {e}")
        print()
        print("Please ensure you have valid AWS credentials.")
        sys.exit(1)
    
    # Run optimizer
    optimizer = EC2CostOptimizer(session, region=args.region)
    optimizer.analyze_instances(check_metrics=not args.no_metrics)


if __name__ == '__main__':
    main()
