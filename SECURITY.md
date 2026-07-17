# Security Policy

## Supported Versions

The following versions of the modules.gg Moderation Module are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

> **Note**: Version 1.0.0 has not yet been released. This policy will be updated upon the first stable release.

---

## Reporting a Vulnerability

We take the security of our software seriously. If you believe you have found a security vulnerability, please follow the responsible disclosure process outlined below.

### Do NOT

- **Do not** open a public GitHub issue for security vulnerabilities.
- **Do not** disclose the vulnerability publicly before a fix has been released.
- **Do not** attempt to access, modify, or delete data belonging to other users.

### Do

- **Do** report vulnerabilities privately to our security team.
- **Do** provide detailed information to help us understand and reproduce the issue.
- **Do** allow reasonable time for us to address the vulnerability before any public disclosure.

### How to Report

Send an email to **[modulesgg@protonmail.com](mailto:modulesgg@protonmail.com)** with the following information:

1. **Subject Line**: `[SECURITY] Brief description of the vulnerability`
2. **Description**: A detailed description of the vulnerability, including:
   - The type of vulnerability (e.g., injection, privilege escalation, data exposure)
   - The affected component(s) and version(s)
   - Steps to reproduce the issue
   - The potential impact
3. **Proof of Concept**: If possible, include a minimal proof of concept or exploit code.
4. **Suggested Fix**: If you have ideas for how to fix the vulnerability, please include them.
5. **Contact Information**: Your preferred method of contact for follow-up questions.

### What to Expect

After you submit a vulnerability report, you can expect the following:

1. **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.
2. **Investigation**: We will investigate the vulnerability and determine its severity.
3. **Updates**: We will provide updates on our progress at least every 7 days.
4. **Resolution**: Once the vulnerability is fixed, we will:
   - Release a patched version
   - Publish a security advisory on GitHub
   - Credit you in the advisory (unless you prefer to remain anonymous)
5. **Disclosure**: We will coordinate with you on the public disclosure timeline.

---

## Security Best Practices for Users

### Bot Token Security

- **Never** commit your bot token to version control.
- **Never** share your bot token in public channels or with untrusted parties.
- **Rotate** your bot token immediately if you suspect it has been compromised.
- **Use** environment variables or secure secret management for token storage.

### Configuration Security

- Review `config.json` permissions to ensure it is not world-readable.
- Use the principle of least privilege when configuring bot permissions in the Discord Developer Portal.
- Regularly audit the bot's OAuth2 scopes and permissions.

### Dependency Management

- Keep dependencies up to date by regularly running `pip install --upgrade -r requirements.txt`.
- Monitor security advisories for `discord.py` and other dependencies.
- Use `pip-audit` or similar tools to scan for known vulnerabilities in dependencies.

### Logging and Monitoring

- Enable appropriate logging levels to detect suspicious activity.
- Monitor bot logs for unusual patterns or errors.
- Set up alerts for critical errors or security-related events.

---

## Security-Related Configuration

The following configuration options in `config.json` have security implications:

| Option | Description | Security Note |
|--------|-------------|---------------|
| `bot.token` | Discord bot authentication token | Treat as a password; never expose publicly |
| `bot.owner_ids` | List of Discord user IDs with owner privileges | Restrict to trusted individuals only |
| `logging.level` | Minimum log level | Use `INFO` or higher in production; `DEBUG` may leak sensitive data |

---

## Acknowledgments

We would like to thank the following individuals and organizations for responsibly disclosing security issues:

> No security vulnerabilities have been reported yet. This section will be updated as reports are received and resolved.

---

Last updated: 2026-07-17

