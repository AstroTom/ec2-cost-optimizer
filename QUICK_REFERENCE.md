# EC2 Cost Optimizer - Quick Reference

## One-Line Commands

```bash
# Enhanced version (recommended)
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1

# Fast mode (no metrics)
python3 ec2-cost-optimizer-enhanced.py --profile prod --no-metrics

# Original Python
python3 ec2-cost-optimizer.py temp-profile

# Bash version
./ec2-cost-optimizer.sh
```

## Installation

```bash
# Clone repo
git clone https://github.com/yourusername/ec2-cost-optimizer.git
cd ec2-cost-optimizer

# Install dependencies (enhanced version only)
pip install -r requirements.txt

# Make scripts executable
chmod +x *.sh *.py
```

## Common Tasks

### Analyze Single Region
```bash
python3 ec2-cost-optimizer-enhanced.py --profile prod --region us-east-1
```

### Analyze All Regions
```bash
for region in us-east-1 us-west-2 eu-west-1; do
  python3 ec2-cost-optimizer-enhanced.py --profile prod --region $region
done
```

### Save to File
```bash
python3 ec2-cost-optimizer-enhanced.py --profile prod > report-$(date +%Y%m%d).txt
```

### Schedule Monthly
```bash
# Add to crontab
0 9 1 * * cd /path/to/ec2-cost-optimizer && python3 ec2-cost-optimizer-enhanced.py --profile prod > /var/log/ec2-cost-$(date +\%Y\%m\%d).txt
```

## Understanding Output

### Instance Info
```
Instance: web-server-01
  ID: i-0123456789abcdef0
  State: running
  Type: t3.large
  Cost: $0.0832/hour ($60.74/month)
  CPU Utilization: Avg 15.2%, Max 38.7%
  ⚠️  Low utilization - consider downsizing
```

### Recommendations
```
✓ = Saves money
→ = Similar/higher cost but newer
⚠️ = Warning/caution
💰 = Savings summary
🎯 = Maximum savings
```

## Decision Matrix

| CPU Usage | Recommendation | Savings |
|-----------|---------------|---------|
| <20% | Downsize | 50%+ |
| 20-80% | Graviton/AMD | 10-20% |
| >80% | Keep or upgrade | N/A |

## Migration Checklist

### Graviton (ARM)
- [ ] Check ARM compatibility
- [ ] Test in non-production
- [ ] Update Docker images
- [ ] Verify dependencies
- [ ] Monitor 48 hours

### AMD
- [ ] No changes needed
- [ ] Stop instance
- [ ] Change type
- [ ] Start instance
- [ ] Verify

### Downsize
- [ ] Check peak usage
- [ ] Test under load
- [ ] Have rollback plan
- [ ] Monitor closely
- [ ] Adjust if needed

## Quick Wins

1. **Dev/Test Environments** → Downsize or stop when not in use
2. **T3 instances** → Migrate to T3a (10% savings, no changes)
3. **Low CPU (<20%)** → Downsize one level
4. **Web servers** → Migrate to Graviton (20% savings)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No recommendations | Instance already optimized or not in database |
| Pricing API error | Check IAM permissions: `pricing:GetProducts` |
| No metrics | Use `--no-metrics` or wait 1+ hours after launch |
| Auth failed | Run `aws sts get-caller-identity` to verify |

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "cloudwatch:GetMetricStatistics",
        "pricing:GetProducts"
      ],
      "Resource": "*"
    }
  ]
}
```

## Savings Estimates

| Migration Type | Typical Savings | Risk Level |
|----------------|-----------------|------------|
| Graviton (ARM) | 15-20% | Medium |
| AMD | 10% | Low |
| Downsize | 30-50% | Medium |
| Newer Gen | 0-5% | Low |

## Instance Type Cheat Sheet

### T-Series (Burstable)
- **T2** → T3 or T4g
- **T3** → T4g (Graviton) or T3a (AMD)
- **T3a** → T4g (Graviton)

### M-Series (General Purpose)
- **M4** → M7g, M6i, or M5
- **M5** → M7g (Graviton) or M6a (AMD)
- **M6i** → M7g (Graviton)

### C-Series (Compute Optimized)
- **C4** → C7g or C6i
- **C5** → C7g (Graviton) or C6a (AMD)

### R-Series (Memory Optimized)
- **R4** → R7g or R6i
- **R5** → R7g (Graviton) or R6a (AMD)

## Command Options

### Enhanced Script
```
--profile PROFILE    AWS profile name
--region REGION      AWS region (default: us-east-1)
--no-metrics         Skip CloudWatch metrics (faster)
```

### Original Script
```
python3 ec2-cost-optimizer.py [profile-name]
```

### Environment Variables
```bash
export AWS_PROFILE=prod
export AWS_DEFAULT_REGION=us-east-1
```

## File Locations

```
ec2-cost-optimizer/
├── ec2-cost-optimizer-enhanced.py  ⭐ Recommended
├── ec2-cost-optimizer.py           Original Python
├── ec2-cost-optimizer.sh           Bash version
├── get-temp-credentials.sh         Credential helper
├── requirements.txt                Dependencies
├── README.md                       Full documentation
├── ENHANCEMENTS.md                 Feature details
├── USAGE_GUIDE.md                  Detailed usage
├── COMPARISON.md                   vs AWS tools
└── QUICK_REFERENCE.md              This file
```

## Support Resources

- **Documentation**: See README.md
- **Detailed Usage**: See USAGE_GUIDE.md
- **Feature Details**: See ENHANCEMENTS.md
- **Tool Comparison**: See COMPARISON.md
- **AWS Docs**: https://aws.amazon.com/ec2/pricing/
- **Graviton Guide**: https://github.com/aws/aws-graviton-getting-started

## Quick Tips

1. **Start small** - Test on 2-3 instances first
2. **Non-prod first** - Always test before production
3. **Monitor closely** - Watch metrics for 48 hours
4. **Document changes** - Keep migration log
5. **Have rollback plan** - Know how to revert
6. **Consider RIs** - After optimizing, buy Reserved Instances
7. **Run monthly** - New optimization opportunities appear
8. **Combine tools** - Use with Compute Optimizer and Cost Explorer

## Example Workflow

```bash
# 1. Analyze
python3 ec2-cost-optimizer-enhanced.py --profile prod > analysis.txt

# 2. Review
cat analysis.txt | grep -A 5 "Downsize\|AMD"

# 3. Test (non-prod)
aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type t3a.medium

# 4. Monitor
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization ...

# 5. Implement (prod)
# Repeat for production instances

# 6. Verify savings
python3 ec2-cost-optimizer-enhanced.py --profile prod > analysis-after.txt
diff analysis.txt analysis-after.txt
```

## Cost Calculation

```
Hourly Rate × 730 hours = Monthly Cost
Monthly Cost × 12 = Annual Cost

Example:
$0.0832/hr × 730 = $60.74/mo
$60.74/mo × 12 = $728.88/yr

20% savings = $145.78/yr per instance
```

## Version Comparison

| Feature | Bash | Original | Enhanced |
|---------|------|----------|----------|
| Setup | None | Minimal | pip install |
| Speed | Fast | Fast | Moderate |
| Accuracy | ~90% | ~90% | 100% |
| Metrics | ❌ | ❌ | ✅ |
| Coverage | Limited | Limited | Extensive |

**Recommendation**: Use Enhanced for production analysis, Bash/Original for quick checks.
