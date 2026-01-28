# EC2 Cost Optimizer - Usage Guide

## Quick Start

### Option 1: Enhanced Version (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run analysis
python3 ec2-cost-optimizer-enhanced.py --profile your-profile --region us-east-1
```

### Option 2: Original Python Version

```bash
# Export credentials
./get-temp-credentials.sh temp-profile

# Run analysis
python3 ec2-cost-optimizer.py temp-profile
```

### Option 3: Bash Version

```bash
# Just run it (uses AWS CLI credentials)
./ec2-cost-optimizer.sh
```

## Enhanced Version Examples

### Basic Usage

```bash
# Analyze with metrics (recommended)
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1

# Fast analysis without metrics
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1 --no-metrics

# Use environment variable for profile
export AWS_PROFILE=prod
python3 ec2-cost-optimizer-enhanced.py --region us-west-2
```

### Multi-Region Analysis

```bash
#!/bin/bash
# analyze-all-regions.sh

REGIONS=("us-east-1" "us-west-2" "eu-west-1" "ap-southeast-1")

for region in "${REGIONS[@]}"; do
    echo "========================================"
    echo "Analyzing region: $region"
    echo "========================================"
    python3 ec2-cost-optimizer-enhanced.py --profile prod --region $region --no-metrics
    echo ""
done
```

### Save Results to File

```bash
# With timestamp
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1 \
  > cost-analysis-$(date +%Y%m%d-%H%M%S).txt

# View later
cat cost-analysis-20260128-143022.txt
```

### Scheduled Analysis (Cron)

```bash
# Add to crontab (run weekly on Monday at 9 AM)
0 9 * * 1 cd /path/to/ec2-cost-optimizer && \
  python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1 \
  > /var/log/ec2-cost-analysis-$(date +\%Y\%m\%d).txt 2>&1
```

## Understanding the Output

### Instance Analysis

```
Instance: production-web-server
  ID: i-0123456789abcdef0
  State: running
  Type: t3.large
  Cost: $0.0832/hour ($60.74/month)
  CPU Utilization: Avg 15.2%, Max 38.7%
  ⚠️  Low utilization - consider downsizing
```

**Key Metrics:**
- **State:** running/stopped (only running instances incur charges)
- **Cost:** Hourly and monthly on-demand pricing
- **CPU Utilization:** Average and peak over last 14 days
- **Warning:** Flags for low (<20%) or high (>80%) utilization

### Recommendations

```
  Recommendations:
    ✓ t4g.large (Graviton2 ARM - 20% cheaper)
      $0.0672/hr ($49.06/mo) - Save $11.68/mo (19.2%)
    
    ✓ t3a.large (AMD - 10% cheaper)
      $0.0752/hr ($54.90/mo) - Save $5.84/mo (9.6%)
    
    ✓ t3.medium (Downsize - low CPU: 15.2%)
      $0.0416/hr ($30.37/mo) - Save $30.37/mo (50.0%)
```

**Recommendation Types:**

1. **Graviton (ARM)** - Best savings, requires ARM compatibility
2. **AMD** - Good savings, x86 compatible
3. **Intel (newer gen)** - Similar price, better performance
4. **Downsize** - Based on actual utilization

### Summary Section

```
SUMMARY
Instances analyzed: 12
Current monthly cost: $1,245.67

💰 Graviton (ARM) Migration Savings: $234.56/mo (18.8%)
   New cost: $1,011.11/mo

💰 AMD Migration Savings: $124.32/mo (10.0%)
   New cost: $1,121.35/mo

💰 Downsizing Savings: $456.78/mo (36.7%)
   New cost: $788.89/mo

🎯 Maximum Potential Savings: $456.78/mo (36.7%)
```

**Savings Categories:**
- **Graviton:** Maximum savings with ARM migration
- **AMD:** Conservative savings, x86 compatible
- **Downsize:** Based on actual utilization
- **Maximum:** Best single option (usually downsizing)

## Decision Guide

### When to Choose Graviton (ARM)

✅ **Good for:**
- Containerized applications (Docker)
- Modern languages (Python, Node.js, Go, Rust, Java 11+)
- Web servers (Nginx, Apache)
- Microservices
- CI/CD runners

❌ **Not suitable for:**
- Legacy x86-only software
- Proprietary binaries without ARM builds
- Windows workloads
- Applications with x86 assembly code

**Testing Checklist:**
1. Check if Docker images have ARM variants
2. Verify language runtime supports ARM
3. Test in non-production first
4. Monitor performance metrics
5. Validate all dependencies

### When to Choose AMD

✅ **Good for:**
- Drop-in x86 replacement
- Applications with unknown ARM compatibility
- Quick wins without testing
- Mixed workloads

**Benefits:**
- No software changes needed
- ~10% cost savings
- Same performance characteristics

### When to Downsize

✅ **Consider if:**
- CPU utilization consistently <20%
- No traffic spikes expected
- Development/staging environments
- Over-provisioned from initial estimates

⚠️ **Caution:**
- Test under peak load first
- Consider burst capacity needs
- Monitor after change
- Have rollback plan

## Migration Workflow

### 1. Analysis Phase

```bash
# Run analysis
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1 \
  > analysis-$(date +%Y%m%d).txt

# Review recommendations
cat analysis-20260128.txt

# Identify quick wins (AMD, downsizing)
grep -A 5 "AMD\|Downsize" analysis-20260128.txt
```

### 2. Planning Phase

Create a migration plan:

```markdown
## Migration Plan

### Phase 1: Low-Risk (Week 1)
- [ ] Dev/staging environments → AMD instances
- [ ] Over-provisioned instances → Downsize
- Expected savings: $150/mo

### Phase 2: Medium-Risk (Week 2-3)
- [ ] Stateless web servers → Graviton
- [ ] Background workers → Graviton
- Expected savings: $300/mo

### Phase 3: High-Risk (Week 4+)
- [ ] Databases → Test Graviton compatibility
- [ ] Legacy apps → Evaluate case-by-case
- Expected savings: $200/mo

Total potential: $650/mo (35% reduction)
```

### 3. Testing Phase

```bash
# Launch test instance
aws ec2 run-instances \
  --image-id ami-xxxxxxxxx \
  --instance-type t4g.medium \
  --key-name your-key \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=test-graviton}]'

# Deploy application
# Run tests
# Monitor performance

# Compare metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-xxxxxxxxx \
  --start-time 2026-01-27T00:00:00Z \
  --end-time 2026-01-28T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum
```

### 4. Migration Phase

```bash
# Stop instance
aws ec2 stop-instances --instance-ids i-xxxxxxxxx

# Wait for stopped state
aws ec2 wait instance-stopped --instance-ids i-xxxxxxxxx

# Change instance type
aws ec2 modify-instance-attribute \
  --instance-id i-xxxxxxxxx \
  --instance-type t4g.medium

# Start instance
aws ec2 start-instances --instance-ids i-xxxxxxxxx

# Verify
aws ec2 describe-instances --instance-ids i-xxxxxxxxx \
  --query 'Reservations[0].Instances[0].InstanceType'
```

### 5. Monitoring Phase

```bash
# Monitor for 24-48 hours
# Check application logs
# Verify performance metrics
# Confirm cost reduction

# Re-run analysis to verify
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1
```

## Advanced Usage

### Filter by Tag

```python
# Modify script to filter by environment
if 'Tags' in instance:
    env_tag = next((tag['Value'] for tag in instance['Tags'] 
                   if tag['Key'] == 'Environment'), None)
    if env_tag != 'production':
        continue  # Skip non-production
```

### Custom Thresholds

```python
# Adjust CPU threshold for downsizing
if cpu_avg is not None and cpu_avg < 15:  # More aggressive
    # Suggest downsizing
```

### Export to CSV

```python
import csv

with open('recommendations.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Instance', 'Current Type', 'Current Cost', 
                     'Recommended Type', 'New Cost', 'Savings'])
    # ... write data
```

## Troubleshooting

### No Recommendations

**Possible causes:**
- Instances already optimized
- Instance types not in recommendation database
- Pricing API unavailable

**Solutions:**
- Check instance types are common (T, M, C, R series)
- Verify AWS Pricing API access
- Review script output for errors

### Metrics Not Available

**Possible causes:**
- Instance recently launched
- CloudWatch monitoring disabled
- Insufficient permissions

**Solutions:**
- Use `--no-metrics` flag
- Enable detailed monitoring
- Wait 1+ hours after launch
- Check IAM permissions

### Pricing API Errors

**Error:** `Could not fetch price for t3.micro`

**Solutions:**
- Check instance type exists in region
- Verify IAM permissions: `pricing:GetProducts`
- Try `--no-metrics` to reduce API calls

### Authentication Issues

**Error:** `Unable to authenticate with AWS`

**Solutions:**
```bash
# Verify credentials
aws sts get-caller-identity

# Re-authenticate
aws login

# Check profile
aws configure list --profile your-profile

# Export credentials
export AWS_PROFILE=your-profile
```

## Best Practices

### 1. Regular Analysis

Run monthly to catch new optimization opportunities:

```bash
# Monthly cron job
0 9 1 * * /path/to/analyze-and-email.sh
```

### 2. Track Savings

Keep historical reports:

```bash
mkdir -p reports/$(date +%Y)
python3 ec2-cost-optimizer-enhanced.py --profile prod \
  > reports/$(date +%Y)/analysis-$(date +%Y%m%d).txt
```

### 3. Test Before Production

Always test in non-production first:

```bash
# Dev environment
python3 ec2-cost-optimizer-enhanced.py --profile dev --region us-east-1

# Staging environment  
python3 ec2-cost-optimizer-enhanced.py --profile staging --region us-east-1

# Production (after successful testing)
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1
```

### 4. Document Changes

Keep a migration log:

```markdown
## Migration Log

### 2026-01-28
- Migrated web-server-01 from t3.large to t4g.large
- Savings: $11.68/mo
- Status: ✅ Successful, no issues
- Rollback plan: Stop, change to t3.large, start

### 2026-01-29
- Downsized db-replica-02 from m5.xlarge to m5.large
- Savings: $70.08/mo
- Status: ✅ Successful, CPU still <30%
```

### 5. Consider Reserved Instances

After optimizing instance types, consider RIs:

```bash
# Calculate RI savings (additional 30-70%)
# Current optimized cost: $1,000/mo
# 1-year RI (no upfront): $700/mo (30% savings)
# 3-year RI (all upfront): $500/mo (50% savings)
```

## Support

For issues or questions:

1. Check [ENHANCEMENTS.md](ENHANCEMENTS.md) for detailed feature documentation
2. Review [README.md](README.md) for general information
3. Open an issue on GitHub
4. Contribute improvements via pull request

## Additional Resources

- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Compute Optimizer](https://aws.amazon.com/compute-optimizer/)
- [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)
- [Graviton Migration Guide](https://github.com/aws/aws-graviton-getting-started)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
