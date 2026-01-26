# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in hrcp, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainer directly at keongalvin@gmail.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

You can expect:
- Acknowledgment within 48 hours
- Regular updates on progress
- Credit in the security advisory (unless you prefer anonymity)

## Security Considerations

hrcp is a configuration library that:
- Does **not** make network requests
- Does **not** execute arbitrary code
- Does **not** access the filesystem (except via explicit `to_json`/`from_json` calls)

When using hrcp:
- Validate configuration data from untrusted sources before loading
- Be cautious with `from_json`/`from_dict` on untrusted input
