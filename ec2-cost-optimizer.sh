#!/bin/bash
# EC2 Cost Optimization Recommendations Script
# Analyzes EC2 instances and suggests cheaper alternatives

echo "================================================================================"
echo "EC2 COST OPTIMIZATION RECOMMENDATIONS"
echo "================================================================================"
echo ""

# Get all instances
instances=$(aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0]]' --output text)

total_analyzed=0
total_current_cost=0
total_graviton_savings=0
total_non_graviton_savings=0

while IFS=$'\t' read -r instance_id instance_type state instance_name; do
    # Skip if no instance type (empty line)
    [ -z "$instance_type" ] && continue
    
    # Set default name if empty
    [ -z "$instance_name" ] && instance_name="N/A"
    
    # Define pricing (approximate US East on-demand rates per hour)
    case "$instance_type" in
        t3.nano) current_price=0.0052 ;;
        t3.micro) current_price=0.0104 ;;
        t3.small) current_price=0.0208 ;;
        t3.medium) current_price=0.0416 ;;
        t3.large) current_price=0.0832 ;;
        t3a.nano) current_price=0.0047 ;;
        t3a.micro) current_price=0.0094 ;;
        t3a.small) current_price=0.0188 ;;
        t3a.medium) current_price=0.0376 ;;
        t4g.nano) current_price=0.0042 ;;
        t4g.micro) current_price=0.0084 ;;
        t4g.small) current_price=0.0168 ;;
        t4g.medium) current_price=0.0336 ;;
        m5.large) current_price=0.096 ;;
        m5.xlarge) current_price=0.192 ;;
        m6a.large) current_price=0.0864 ;;
        m6a.xlarge) current_price=0.1728 ;;
        m7g.large) current_price=0.0816 ;;
        *) current_price=0 ;;
    esac
    
    # Skip if we don't have pricing data
    [ "$current_price" = "0" ] && continue
    
    # Calculate monthly cost
    monthly_cost=$(echo "$current_price * 730" | bc -l)
    
    # Determine recommendations based on instance type
    recommendations=""
    case "$instance_type" in
        t3.nano)
            recommendations="t4g.nano|0.0042|Graviton2 ARM (~20% cheaper)
t3a.nano|0.0047|AMD (~10% cheaper)"
            ;;
        t3.micro)
            recommendations="t4g.micro|0.0084|Graviton2 ARM (~20% cheaper)
t3a.micro|0.0094|AMD (~10% cheaper)"
            ;;
        t3.small)
            recommendations="t4g.small|0.0168|Graviton2 ARM (~20% cheaper)
t3a.small|0.0188|AMD (~10% cheaper)"
            ;;
        t3.medium)
            recommendations="t4g.medium|0.0336|Graviton2 ARM (~20% cheaper)
t3a.medium|0.0376|AMD (~10% cheaper)"
            ;;
        t3.large)
            recommendations="t4g.large|0.0672|Graviton2 ARM (~20% cheaper)
t3a.large|0.0752|AMD (~10% cheaper)"
            ;;
        m5.large)
            recommendations="m7g.large|0.0816|Graviton3 (~15% cheaper)
m6a.large|0.0864|AMD (~10% cheaper)"
            ;;
        t4g.*)
            recommendations="OPTIMIZED|0|Already using cost-effective Graviton2"
            ;;
        *)
            continue
            ;;
    esac
    
    # Skip if no recommendations
    [ -z "$recommendations" ] && continue
    
    echo "Instance: $instance_name"
    echo "  ID: $instance_id"
    echo "  State: $state"
    echo "  Current Type: $instance_type"
    printf "  Current Cost: \$%.4f/hour (\$%.2f/month)\n" "$current_price" "$monthly_cost"
    echo ""
    
    if echo "$recommendations" | grep -q "OPTIMIZED"; then
        echo "  Status: ✓ OPTIMIZED - Already using cost-effective instance type"
    else
        # Only count instances with actual recommendations in totals
        total_analyzed=$((total_analyzed + 1))
        total_current_cost=$(echo "$total_current_cost + $monthly_cost" | bc -l)
        echo "  Recommendations:"
        echo ""
        
        best_graviton_savings=0
        best_non_graviton_savings=0
        first_recommendation=true
        
        while IFS='|' read -r alt_type alt_price description; do
            [ -z "$alt_type" ] && continue
            
            alt_monthly=$(echo "$alt_price * 730" | bc -l)
            savings_hour=$(echo "$current_price - $alt_price" | bc -l)
            savings_month=$(echo "$savings_hour * 730" | bc -l)
            savings_pct=$(echo "scale=3; ($savings_hour / $current_price) * 100" | bc -l)
            
            # Track best savings for each category
            if echo "$description" | grep -qi "graviton"; then
                if (( $(echo "$savings_month > $best_graviton_savings" | bc -l) )); then
                    best_graviton_savings=$savings_month
                fi
            else
                if (( $(echo "$savings_month > $best_non_graviton_savings" | bc -l) )); then
                    best_non_graviton_savings=$savings_month
                fi
            fi
            
            echo "    → $alt_type ($description)"
            printf "      Cost: \$%.4f/hour (\$%.2f/month)\n" "$alt_price" "$alt_monthly"
            
            if (( $(echo "$savings_hour > 0" | bc -l) )); then
                printf "      Savings: \$%.4f/hour (\$%.2f/month) - %.1f%% cheaper\n" "$savings_hour" "$savings_month" "$savings_pct"
            fi
            echo ""
        done <<< "$recommendations"
        
        # Add to totals
        total_graviton_savings=$(echo "$total_graviton_savings + $best_graviton_savings" | bc -l)
        total_non_graviton_savings=$(echo "$total_non_graviton_savings + $best_non_graviton_savings" | bc -l)
    fi
    
    echo "--------------------------------------------------------------------------------"
    echo ""
    
done <<< "$instances"

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo "Instances analyzed: $total_analyzed"

if [ "$total_analyzed" -gt 0 ]; then
    printf "Current monthly cost: \$%.2f\n" "$total_current_cost"
    echo ""
    
    if (( $(echo "$total_graviton_savings > 0" | bc -l) )); then
        graviton_pct=$(echo "scale=3; ($total_graviton_savings / $total_current_cost) * 100" | bc -l)
        printf "Potential savings with Graviton (ARM) migration:\n"
        printf "  Monthly: \$%.2f (%.1f%% reduction)\n" "$total_graviton_savings" "$graviton_pct"
        new_cost=$(echo "$total_current_cost - $total_graviton_savings" | bc -l)
        printf "  New monthly cost: \$%.2f\n" "$new_cost"
        echo ""
    fi
    
    if (( $(echo "$total_non_graviton_savings > 0" | bc -l) )); then
        non_graviton_pct=$(echo "scale=3; ($total_non_graviton_savings / $total_current_cost) * 100" | bc -l)
        printf "Potential savings without Graviton (x86 only):\n"
        printf "  Monthly: \$%.2f (%.1f%% reduction)\n" "$total_non_graviton_savings" "$non_graviton_pct"
        new_cost=$(echo "$total_current_cost - $total_non_graviton_savings" | bc -l)
        printf "  New monthly cost: \$%.2f\n" "$new_cost"
        echo ""
    fi
fi

echo "Notes:"
echo "  • Prices are approximate US East (N. Virginia) on-demand rates"
echo "  • Actual savings depend on region, usage patterns, and Reserved Instances"
echo "  • Graviton (ARM) instances require ARM-compatible software"
echo "  • Test compatibility before migrating production workloads"
echo ""
echo "To change an instance type:"
echo "  1. Stop the instance: aws ec2 stop-instances --instance-ids <instance-id>"
echo "  2. Modify type: aws ec2 modify-instance-attribute --instance-id <instance-id> --instance-type <new-type>"
echo "  3. Start instance: aws ec2 start-instances --instance-ids <instance-id>"
