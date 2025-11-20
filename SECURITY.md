# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@yourdomain.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information (as much as you can provide) to help us better understand the nature and scope of the possible issue:

* Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English or Romanian.

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine the affected versions.
2. Audit code to find any potential similar problems.
3. Prepare fixes for all releases still under maintenance.
4. Release new security patch versions as soon as possible.

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request.

## Security Best Practices

### For Users

1. **Keep Dependencies Updated**: Regularly update to the latest version
2. **Use Environment Variables**: Never commit secrets to version control
3. **Secure Your .env**: Keep your `.env` file secure and never share it
4. **HTTPS Only**: Always use HTTPS in production
5. **Validate Inputs**: Be cautious with user-supplied data

### For Developers

1. **Dependency Scanning**: Use tools like `safety` or `pip-audit`
   ```bash
   pip install safety
   safety check
   ```

2. **Code Scanning**: Use Bandit for security checks
   ```bash
   bandit -r src/ -f json -o bandit-report.json
   ```

3. **Secret Scanning**: Never commit credentials, API keys, or secrets

4. **CORS Configuration**: Properly configure CORS in production

5. **Input Validation**: Always validate and sanitize inputs

## Known Security Considerations

### Web Scraping
- The application scrapes external websites. Be aware of rate limiting and robots.txt
- Use responsibly and respect website terms of service

### PDF Generation
- WeasyPrint processes HTML. Ensure templates are trusted sources only
- Do not accept user-provided HTML without sanitization

### API Endpoints
- `/cache/clear` and `/cache/refresh` should be protected in production
- Consider adding authentication for sensitive endpoints

## Security Updates

Security updates will be announced via:
- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Git tags with security fixes

## Contact

For security concerns, contact: **security@yourdomain.com**

For general questions: **support@yourdomain.com**

