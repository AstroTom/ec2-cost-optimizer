# EC2 Cost Optimization Recommendation scripts

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Shell Script](https://img.shields.io/badge/Shell-Bash-green.svg)](https://www.gnu.org/software/bash/)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)

Analyze your AWS EC2 instances and get actionable cost optimization recommendations by identifying cheaper alternative instance types.

> [!CAUTION]
> This project was created as a Kiro experiment and has only been tested on trivial examples
> 

> [!Note]
> The scripts do not use the AWS Cost Optimization Hub or AWS Compute Optimizer. If those features are enabled, it could make use of CloudWatch data to see if any instances are over or under provisioned. Both features in AWS are disabled by default. The Cost Optimization Hub can only be enabled from the Management (Payer) account.
> 


## Features

✅ **Multiple Implementations** - Choose between Bash, Python, or Enhanced Python scripts  
✅ **Real-Time Pricing** - Enhanced version uses AWS Pricing API for accurate costs  
✅ **CloudWatch Integration** - Analyzes actual CPU utilization for rightsizing  
✅ **Graviton Analysis** - Identify savings from ARM-based Graviton instances  
✅ **x86 Alternatives** - Find AMD-based alternatives for drop-in replacements  
✅ **Detailed Breakdown** - Per-instance and aggregate savings analysis  
✅ **Easy Integration** - Works with AWS CLI and boto3  

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/ec2-cost-optimizer.git
cd ec2-cost-optimizer

# Authenticate with AWS
aws login

# Run the bash script (no setup needed)
./ec2-cost-optimizer.sh

# Or use the enhanced Python version (recommended)
pip install -r requirements.txt
python3 ec2-cost-optimizer-enhanced.py --profile your-profile --region us-east-1

# Or use the original Python version
./get-temp-credentials.sh temp-profile
python3 ec2-cost-optimizer.py temp-profile
```

## Table of Contents

- [Created Files](#created-files)
- [Version Comparison](#version-comparison)
- [Workflow](#workflow)
- [Sample Output](#sample-output)
- [Understanding the Summary](#understanding-the-summary)
- [Recommendations Explained](#recommendations-explained)
- [Algorithm Details](#algorithm-details)
- [How to Change Instance Types](#how-to-change-instance-types)
- [Prerequisites](#prerequisites)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Created Files

### 1. `ec2-cost-optimizer-enhanced.py` (Enhanced Python Version) ⭐ **RECOMMENDED**
Advanced Python script with real-time pricing and utilization analysis.

**Features:**
- ✅ Real-time pricing from AWS Pricing API (no hardcoded rates)
- ✅ CloudWatch metrics integration for CPU utilization
- ✅ Intelligent downsizing recommendations based on actual usage
- ✅ Broader instance family coverage (T, M, C, R series)
- ✅ Region-aware pricing
- ✅ Multiple processor architecture recommendations (Graviton, AMD, Intel)

**Usage:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with metrics analysis (recommended)
python3 ec2-cost-optimizer-enhanced.py --profile your-profile --region us-east-1

# Run without metrics (faster)
python3 ec2-cost-optimizer-enhanced.py --profile your-profile --no-metrics

# Use environment variable for profile
export AWS_PROFILE=your-profile
python3 ec2-cost-optimizer-enhanced.py --region us-west-2
```

### 2. `ec2-cost-optimizer.sh` (Bash Version)
A standalone bash script that uses AWS CLI to analyze EC2 instances and recommend cost-effective alternatives.

**Features:**
- Works directly with AWS CLI credentials
- No additional dependencies required
- Provides detailed cost comparisons
- Shows monthly savings potential

**Usage:**
```bash
chmod +x ec2-cost-optimizer.sh
./ec2-cost-optimizer.sh
```

### 3. `ec2-cost-optimizer.py` (Original Python Version)
A Python script using boto3 that provides the same functionality with more extensibility.

**Features:**
- Uses boto3 AWS SDK
- Supports AWS profiles
- More detailed analysis capabilities
- Easier to extend and customize

**Usage:**
```bash
python3 ec2-cost-optimizer.py [profile-name]
```

### 4. `get-temp-credentials.sh`
Helper script to export your current AWS CLI credentials to a profile that boto3 can use.

**Features:**
- Extracts credentials from AWS CLI session
- Creates boto3-compatible profile
- Handles SSO and standard IAM authentication
- Configures credential_process for seamless integration

**Usage:**
```bash
chmod +x get-temp-credentials.sh
./get-temp-credentials.sh [profile-name]
```

Default profile name is `temp-profile` if not specified.

## Version Comparison

| Feature | Bash Script | Original Python | Enhanced Python ⭐ |
|---------|-------------|-----------------|-------------------|
| Real-time AWS Pricing | ❌ | ❌ | ✅ |
| CloudWatch Metrics | ❌ | ❌ | ✅ |
| Utilization-based Rightsizing | ❌ | ❌ | ✅ |
| Region-aware Pricing | ❌ | ❌ | ✅ |
| Instance Coverage | Limited | Limited | Extensive (T/M/C/R) |
| Setup Required | None | Minimal | pip install |
| Speed | Fast | Fast | Moderate (API calls) |
| Accuracy | Approximate | Approximate | Real-time |

**Recommendation:** Use the Enhanced Python version for production cost analysis. Use Bash/Original Python for quick checks.

## Workflow

### Quick Start (Bash Script)
```bash
# 1. Authenticate with AWS
aws login

# 2. Run the bash script (no setup needed)
./ec2-cost-optimizer.sh
```

### Python Script Workflow
```bash
# 1. Authenticate with AWS
aws login

# 2. Export credentials to a profile for Python/boto3
./get-temp-credentials.sh temp-profile

# 3. Run the Python script with the profile
python3 ec2-cost-optimizer.py temp-profile

# Alternative: Set profile as environment variable
export AWS_PROFILE=temp-profile
python3 ec2-cost-optimizer.py
```

## Sample Output

```
================================================================================
EC2 COST OPTIMIZATION RECOMMENDATIONS
================================================================================

Instance: test daily-auto-off
  ID: i-09a804d4968bbb549
  State: stopped
  Current Type: t3.micro
  Current Cost: $0.0104/hour ($7.59/month)

  Recommendations:
    → t4g.micro (Graviton2 ARM (~20% cheaper))
      Cost: $0.0084/hour ($6.13/month)
      Savings: $0.0020/hour ($1.46/month) - 19.2% cheaper

    → t3a.micro (AMD (~10% cheaper))
      Cost: $0.0094/hour ($6.86/month)
      Savings: $0.0010/hour ($0.73/month) - 9.6% cheaper

--------------------------------------------------------------------------------

Instance: mysql
  ID: i-09f096965bc4e0724
  State: stopped
  Current Type: t3.small
  Current Cost: $0.0208/hour ($15.18/month)

  Recommendations:
    → t4g.small (Graviton2 ARM (~20% cheaper))
      Cost: $0.0168/hour ($12.26/month)
      Savings: $0.0040/hour ($2.92/month) - 19.2% cheaper

    → t3a.small (AMD (~10% cheaper))
      Cost: $0.0188/hour ($13.72/month)
      Savings: $0.0020/hour ($1.46/month) - 9.6% cheaper

--------------------------------------------------------------------------------

Instance: RI israel-office-hours
  ID: i-0724bf477e796176e
  State: running
  Current Type: t4g.nano
  Current Cost: $0.0042/hour ($3.07/month)

  Status: ✓ OPTIMIZED - Already using cost-effective instance type
--------------------------------------------------------------------------------

================================================================================
SUMMARY
================================================================================
Instances analyzed: 4
Current monthly cost: $45.55

Potential savings with Graviton (ARM) migration:
  Monthly: $8.76 (19.2% reduction)
  New monthly cost: $36.79

Potential savings without Graviton (x86 only):
  Monthly: $4.38 (9.6% reduction)
  New monthly cost: $41.17

Notes:
  • Prices are approximate US East (N. Virginia) on-demand rates
  • Actual savings depend on region, usage patterns, and Reserved Instances
  • Graviton (ARM) instances require ARM-compatible software
  • Test compatibility before migrating production workloads
```

## Understanding the Summary

The summary section provides two optimization scenarios:

**1. Graviton (ARM) Migration** - Maximum savings by migrating to ARM-based Graviton instances
- Best cost savings (~20% for T3→T4g)
- Requires ARM-compatible software
- May need application testing/recompilation

**2. Non-Graviton (x86 only)** - Conservative savings staying with x86 architecture
- Moderate savings (~10% for T3→T3a)
- Drop-in replacement, no software changes
- Uses AMD processors instead of Intel

**Note:** Only instances with available recommendations are counted in the analysis. Already optimized instances (like t4g instances) are shown but not included in cost totals.

## Recommendations Explained

### Instance Type Alternatives

**T3 → T4g (Graviton2 ARM)**
- ~20% cost savings
- Better performance per dollar
- Requires ARM-compatible software
- Best for: Web servers, development environments, microservices

**T3 → T3a (AMD)**
- ~10% cost savings
- Drop-in replacement (x86 compatible)
- No software changes needed
- Best for: Applications requiring x86 compatibility

**M5 → M7g (Graviton3)**
- ~15% cost savings
- Latest generation ARM processors
- Significant performance improvements
- Best for: Compute-intensive workloads

## Algorithm Details

The enhanced script uses a multi-stage analysis approach combining real-time AWS pricing, CloudWatch metrics, and rule-based recommendations. For a detailed explanation of how the algorithm works, see [ALGORITHM.md](ALGORITHM.md).

**Key Features:**
- Real-time pricing from AWS Pricing API (region-specific)
- CloudWatch CPU utilization analysis (14-day window)
- Rule-based alternative generation (Graviton, AMD, Intel, downsizing)
- Best-per-category savings tracking

**Decision Logic:**
- CPU < 20% → Suggest downsizing (50% savings potential)
- Current generation → Suggest Graviton (~20% savings)
- Older generation → Suggest latest generation upgrade

**Comparison with AWS Services:**
- Uses CloudWatch data (like Compute Optimizer) but simpler logic
- Does NOT use AWS Cost Optimization Hub or Compute Optimizer APIs
- Complementary to AWS native tools, not a replacement

See [ALGORITHM.md](ALGORITHM.md) for complete details, decision trees, and comparisons with AWS Compute Optimizer.

## How to Change Instance Types

```bash
# 1. Stop the instance
aws ec2 stop-instances --instance-ids <instance-id>

# 2. Wait for instance to stop
aws ec2 wait instance-stopped --instance-ids <instance-id>

# 3. Modify instance type
aws ec2 modify-instance-attribute \
  --instance-id <instance-id> \
  --instance-type <new-type>

# 4. Start the instance
aws ec2 start-instances --instance-ids <instance-id>
```

## Prerequisites

### For Bash Script
- AWS CLI installed and configured
- Valid AWS credentials (`aws login`)
- `bc` command (for calculations)

### For Python Script
- Python 3.x
- boto3 library: `sudo apt install python3-boto3`
- AWS CLI installed and configured
- Valid AWS credentials

## Notes

- **Pricing**: All prices are approximate US East (N. Virginia) on-demand rates
- **Savings**: Actual savings depend on your region, usage patterns, and whether you use Reserved Instances or Savings Plans
- **Graviton Compatibility**: ARM-based instances (t4g, m7g) require ARM-compatible software. Test thoroughly before migrating production workloads
- **Stopped Instances**: The script analyzes all instances, but recommendations are most relevant for instances you plan to run
- **Reserved Instances**: If you have RIs, the cost comparison may differ from on-demand pricing shown

## Troubleshooting

### Python script can't find credentials
```bash
# Re-run the credential export script
./get-temp-credentials.sh temp-profile

# Verify profile exists
cat ~/.aws/config | grep -A 3 "profile temp-profile"
```

### AWS CLI not authenticated
```bash
# Authenticate with AWS
aws login

# Verify authentication
aws sts get-caller-identity
```

### boto3 not installed
```bash
# Install via apt (Ubuntu/Debian)
sudo apt install python3-boto3

# Or use pip in a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install boto3
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Pricing data is approximate and based on US East (N. Virginia) on-demand rates
- Always verify current pricing in your specific AWS region
- Test thoroughly before making changes to production instances

## Disclaimer

These scripts are provided as-is for cost optimization analysis. Always test instance type changes in non-production environments first. The authors are not responsible for any issues arising from instance type modifications.


