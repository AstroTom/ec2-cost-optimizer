# Contributing to EC2 Cost Optimizer

Thank you for considering contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, AWS CLI version, Python version)

### Suggesting Enhancements

We welcome suggestions for new features or improvements:
- Open an issue describing your enhancement
- Explain the use case and benefits
- If possible, provide examples

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

**Bash Scripts:**
- Use 4 spaces for indentation
- Add comments for complex logic
- Follow shellcheck recommendations

**Python Scripts:**
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small

### Adding New Instance Types

To add support for new instance types:

1. Update pricing in both scripts:
   - `ec2-cost-optimizer.sh`: Add to the pricing case statement
   - `ec2-cost-optimizer.py`: Add to `get_instance_pricing_estimate()`

2. Add recommendations:
   - `ec2-cost-optimizer.sh`: Add to the recommendations case statement
   - `ec2-cost-optimizer.py`: Add to `get_alternative_instances()`

3. Test with instances of that type

### Testing

Before submitting a PR:
- Test both bash and Python scripts
- Verify output matches between scripts
- Test with different AWS authentication methods
- Check that percentages and dollar amounts are accurate

## Questions?

Feel free to open an issue for any questions about contributing.

## Code of Conduct

Be respectful and constructive in all interactions. We're all here to learn and improve.
