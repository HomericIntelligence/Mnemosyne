# Security Policy

All active technical prose in this policy must follow the
[ASD-STE100 writing policy](docs/asd-ste100.md).

## Supported Versions

| Version | Supported |
| --------- | ----------- |
| Latest on `main` | Yes |
| Older releases | No |

## Reporting a Vulnerability

If you find a security vulnerability in Mnemosyne, report it with **GitHub
Private Security Advisories**:

1. Go to the [Security Advisories page](https://github.com/HomericIntelligence/Mnemosyne/security/advisories).
2. Select **"New draft security advisory"**.
3. Enter the vulnerability details.

**Do not open a public issue for a security vulnerability.**

## Response Timeline

- **Acknowledgment**: Within 48 hours of report
- **Assessment**: Within 7 days
- **Fix or mitigation**: Dependent on severity and complexity

## Scope

Mnemosyne is a **skills and session-memory store**. It contains Markdown
documents and skill files. It also contains Python scripts for validation and
repository maintenance. It does not handle user data or run production
services.

This policy covers these items:

- Python scripts for validation, migration, and CI automation
- CI/CD workflows and GitHub Actions configurations
- Pre-commit hook configurations

Community skill files contain information. The Markdown content does not run
code directly.

## Security Scanning

Pre-commit hooks check basic file hygiene. The checks include YAML validation,
JSON validation, and large-file detection. The repository does **not** configure
Bandit in `.pre-commit-config.yaml`. The Python codebase is small. Maintainers
accept the current configuration. If the Python codebase grows, maintainers can
add Bandit.

## Contact

For questions about this policy, open a GitHub issue. You can also contact the
HomericIntelligence project maintainers.
