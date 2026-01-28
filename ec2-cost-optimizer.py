#!/usr/bin/env python3
"""
EC2 Cost Optimization Recommendations Script
Analyzes EC2 instances and suggests cheaper alternatives
"""

import boto3
import json
import os
import sys
from collections import defaultdict

def get_instance_pricing_estimate(instance_type, region='us-east-1'):
    """
    Rough pricing estimates for common instance types (Linux, on-demand)
    These are approximate - actual pricing varies by region
    """
    pricing_map = {
        # T3 instances (Intel)
        't3.nano': 0.0052, 't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
        't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
        # T3a instances (AMD - ~10% cheaper)
        't3a.nano': 0.0047, 't3a.micro': 0.0094, 't3a.small': 0.0188, 't3a.medium': 0.0376,
        't3a.large': 0.0752, 't3a.xlarge': 0.1504, 't3a.2xlarge': 0.3008,
        # T4g instances (Graviton2 - ~20% cheaper)
        't4g.nano': 0.0042, 't4g.micro': 0.0084, 't4g.small': 0.0168, 't4g.medium': 0.0336,
        't4g.large': 0.0672, 't4g.xlarge': 0.1344, 't4g.2xlarge': 0.2688,
        # M5 instances
        'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
        # M6i instances (newer generation)
        'm6i.large': 0.096, 'm6i.xlarge': 0.192, 'm6i.2xlarge': 0.384,
        # M6a instances (AMD)
        'm6a.large': 0.0864, 'm6a.xlarge': 0.1728, 'm6a.2xlarge': 0.3456,
        # M7g instances (Graviton3)
        'm7g.medium': 0.0408, 'm7g.large': 0.0816, 'm7g.xlarge': 0.1632,
    }
    return pricing_map.get(instance_type, 0)

def get_alternative_instances(current_type):
    """Generate alternative instance type recommendations"""
    alternatives = []
    
    # T3 to T4g/T3a mapping
    t3_to_alternatives = {
        't3.nano': [('t4g.nano', 'Graviton2 ARM'), ('t3a.nano', 'AMD')],
        't3.micro': [('t4g.micro', 'Graviton2 ARM'), ('t3a.micro', 'AMD')],
        't3.small': [('t4g.small', 'Graviton2 ARM'), ('t3a.small', 'AMD')],
        't3.medium': [('t4g.medium', 'Graviton2 ARM'), ('t3a.medium', 'AMD')],
        't3.large': [('t4g.large', 'Graviton2 ARM'), ('t3a.large', 'AMD')],
        't3.xlarge': [('t4g.xlarge', 'Graviton2 ARM'), ('t3a.xlarge', 'AMD')],
        't3.2xlarge': [('t4g.2xlarge', 'Graviton2 ARM'), ('t3a.2xlarge', 'AMD')],
    }
    
    # M5 to newer generations
    m5_to_alternatives = {
        'm5.large': [('m7g.large', 'Graviton3'), ('m6a.large', 'AMD'), ('m6i.large', 'Intel 6th gen')],
        'm5.xlarge': [('m7g.xlarge', 'Graviton3'), ('m6a.xlarge', 'AMD'), ('m6i.xlarge', 'Intel 6th gen')],
        'm5.2xlarge': [('m7g.2xlarge', 'Graviton3'), ('m6a.2xlarge', 'AMD'), ('m6i.2xlarge', 'Intel 6th gen')],
    }
    
    if current_type in t3_to_alternatives:
        return t3_to_alternatives[current_type]
    elif current_type in m5_to_alternatives:
        return m5_to_alternatives[current_type]
    
    return []

def main():
    # Check for profile name argument or environment variable
    profile_name = None
    if len(sys.argv) > 1:
        profile_name = sys.argv[1]
    elif os.environ.get('AWS_PROFILE'):
        profile_name = os.environ.get('AWS_PROFILE')
    
    # Create session with profile if specified
    try:
        if profile_name:
            print(f"Using AWS profile: {profile_name}")
            session = boto3.Session(profile_name=profile_name)
        else:
            print("Using default AWS credentials")
            session = boto3.Session()
        
        ec2 = session.client('ec2')
        
        # Test credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"Authenticated as: {identity['Arn']}")
        print()
    except Exception as e:
        print(f"Error: Unable to authenticate with AWS: {e}")
        print()
        print("Please ensure you have valid AWS credentials.")
        print("You can:")
        print("  1. Run: ./export-aws-credentials.sh temp-profile")
        print("  2. Then: python3 ec2-cost-optimizer.py temp-profile")
        print("  Or: export AWS_PROFILE=temp-profile && python3 ec2-cost-optimizer.py")
        sys.exit(1)
    
    # Get all instances
    response = ec2.describe_instances()
    
    print("=" * 80)
    print("EC2 COST OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    instances_analyzed = 0
    total_current_cost = 0
    total_graviton_savings = 0
    total_non_graviton_savings = 0
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            state = instance['State']['Name']
            
            # Get instance name from tags
            instance_name = 'N/A'
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        break
            
            current_price = get_instance_pricing_estimate(instance_type)
            current_monthly = current_price * 730
            alternatives = get_alternative_instances(instance_type)
            
            if not alternatives:
                continue
            
            instances_analyzed += 1
            total_current_cost += current_monthly
            
            print(f"Instance: {instance_name}")
            print(f"  ID: {instance_id}")
            print(f"  State: {state}")
            print(f"  Current Type: {instance_type}")
            print(f"  Current Cost: ${current_price:.4f}/hour (${current_monthly:.2f}/month)")
            print()
            print("  Recommendations:")
            
            best_graviton_savings = 0
            best_non_graviton_savings = 0
            
            for alt_type, description in alternatives:
                alt_price = get_instance_pricing_estimate(alt_type)
                if alt_price == 0:
                    continue
                    
                savings_per_hour = current_price - alt_price
                savings_per_month = savings_per_hour * 730
                savings_percent = (savings_per_hour / current_price * 100) if current_price > 0 else 0
                
                # Track best savings for each category
                if 'graviton' in description.lower() or 'arm' in description.lower():
                    if savings_per_month > best_graviton_savings:
                        best_graviton_savings = savings_per_month
                else:
                    if savings_per_month > best_non_graviton_savings:
                        best_non_graviton_savings = savings_per_month
                
                if savings_per_hour > 0:
                    print(f"    → {alt_type} ({description})")
                    print(f"      Cost: ${alt_price:.4f}/hour (${alt_price * 730:.2f}/month)")
                    print(f"      Savings: ${savings_per_hour:.4f}/hour (${savings_per_month:.2f}/month) - {savings_percent:.1f}% cheaper")
                elif savings_per_hour < 0:
                    print(f"    → {alt_type} ({description})")
                    print(f"      Cost: ${alt_price:.4f}/hour (${alt_price * 730:.2f}/month)")
                    print(f"      Note: {abs(savings_percent):.1f}% more expensive but newer generation")
                else:
                    print(f"    → {alt_type} ({description})")
                    print(f"      Cost: ${alt_price:.4f}/hour (${alt_price * 730:.2f}/month)")
                    print(f"      Note: Similar pricing")
            
            total_graviton_savings += best_graviton_savings
            total_non_graviton_savings += best_non_graviton_savings
            print()
            print("-" * 80)
            print()
    
    if instances_analyzed == 0:
        print("No optimization recommendations available.")
        print("Your instances are either already optimized or using instance types")
        print("not covered by this script's recommendation database.")
    else:
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Instances analyzed: {instances_analyzed}")
        print(f"Current monthly cost: ${total_current_cost:.2f}")
        print()
        
        if total_graviton_savings > 0:
            graviton_pct = (total_graviton_savings / total_current_cost * 100) if total_current_cost > 0 else 0
            new_cost = total_current_cost - total_graviton_savings
            print("Potential savings with Graviton (ARM) migration:")
            print(f"  Monthly: ${total_graviton_savings:.2f} ({graviton_pct:.1f}% reduction)")
            print(f"  New monthly cost: ${new_cost:.2f}")
            print()
        
        if total_non_graviton_savings > 0:
            non_graviton_pct = (total_non_graviton_savings / total_current_cost * 100) if total_current_cost > 0 else 0
            new_cost = total_current_cost - total_non_graviton_savings
            print("Potential savings without Graviton (x86 only):")
            print(f"  Monthly: ${total_non_graviton_savings:.2f} ({non_graviton_pct:.1f}% reduction)")
            print(f"  New monthly cost: ${new_cost:.2f}")
            print()
        
        print("Notes:")
        print("  • Prices are approximate US East (N. Virginia) on-demand rates")
        print("  • Actual savings depend on region, usage patterns, and Reserved Instances")
        print("  • Graviton (ARM) instances require ARM-compatible software")
        print("  • Test compatibility before migrating production workloads")

if __name__ == '__main__':
    main()
