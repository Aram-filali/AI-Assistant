# Security Policy

## Overview

This document outlines the security practices, vulnerabilities handling, and compliance measures for the AI Sales Assistant project.

## Security Features

### Authentication & Authorization

- **JWT-based Authentication**: Stateless, scalable token-based authentication
- **Password Hashing**: PBKDF2-SHA256 with configurable salt rounds
- **Token Expiration**: Configurable token TTL (default: 24 hours)
- **Multi-Tenant Isolation**: UserID-based filtering on all queries
- **Role-Based Access Control**: Admin endpoints require admin role

### Data Protection

- **Encryption in Transit**: HTTPS/TLS in production
- **Database Security**: 
  - PostgreSQL with strong credentials
  - No plaintext passwords stored
  - Connection pooling with timeout
- **Sensitive Data**: 
  - API keys stored as environment variables (not in code)
  - Never logged or exposed in responses
- **Audit Trail**: User actions logged with timestamps and user context

### API Security

- **CORS**: Strict origin validation (no "*" in production)
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: Input validation and output encoding
- **Rate Limiting**: Token bucket algorithm to prevent brute force
- **Input Validation**: Pydantic schemas validate all requests
- **Error Handling**: Generic error messages (no SQL or system details leaked)

### Infrastructure Security

- **Environment Isolation**: Development/Staging/Production separation
- **Secrets Management**: Environment variables for all secrets
- **Dependency Management**: 
  - Regular updates via Dependabot
  - Vulnerability scanning with `pip-audit` and `npm audit`
  - Pinned exact versions in production
- **Docker Security**: 
  - Non-root user in containers
  - Minimal base images (Python 3.11-slim)
  - Health checks configured

---

## Vulnerability Reports

### Reporting Security Issues

⚠️ **DO NOT** open public GitHub issues for security vulnerabilities.

Instead, report to: **security@yourdomain.com**

Include:
- Type of vulnerability
- Location (file/endpoint)
- Impact assessment
- Steps to reproduce
- Suggested fix (optional)

### Response Timeline

- **Acknowledgment**: Within 24 hours
- **Assessment**: Within 7 days
- **Fix Development**: Based on severity
- **Disclosure**: 30 days after patch (coordinated)

### Severity Levels

| Level | CVSS | Examples | Timeline |
|-------|------|----------|----------|
| Critical | 9.0-10.0 | Auth bypass, RCE | 24-48h |
| High | 7.0-8.9 | SQL injection, XSS | 7 days |
| Medium | 4.0-6.9 | Information leak | 30 days |
| Low | 0.1-3.9 | Documentation issues | Next release |

---

## Security Testing

### Regular Scans

- **SAST** (Static Analysis): Bandit, Pylint
- **DAST** (Dynamic Analysis): OWASP ZAP
- **Dependency Scanning**: Dependabot, npm audit
- **Container Scanning**: Trivy

### Test Coverage

- **Unit Tests**: >80% coverage for all business logic
- **Integration Tests**: All API endpoints tested with auth
- **Security Tests**: 25+ specific security test cases
  - SQL injection prevention
  - XSS payload handling
  - JWT token validation
  - Rate limiting enforcement
  - CORS header validation

### Penetration Testing

Recommended annually by professional security firm.

---

## Compliance

### Standards

- **OWASP Top 10**: Addressed in architecture and testing
- **CWE**: Common Weakness Enumeration coverage
- **NIST**: Cybersecurity Framework aligned
- **GDPR**: User data handling (if applicable)

### Data Handling

- **User Data**: Never shared without consent
- **Audit Logs**: Retained for 90 days minimum
- **Backups**: Encrypted, stored separately
- **Data Deletion**: Cascade delete on user account removal

---

## Deployment Security

### Production Checklist

- [ ] All environment variables set from secure vault
- [ ] HTTPS/TLS enabled (Railway auto-enables)
- [ ] CORS domains configured (not "*")
- [ ] Rate limiting enabled
- [ ] Logging enabled (without secrets)
- [ ] Monitoring configured (error tracking)
- [ ] Backups configured
- [ ] Database credentials strong (Railway auto-generates)
- [ ] API keys rotated (if exposed)
- [ ] Dependencies up-to-date

### Environment Variables Vault

Sensitive variables stored in Railway Vault:
- `SECRET_KEY` (JWT signing key)
- `POSTGRES_PASSWORD` (DB credentials)
- `OPENAI_API_KEY` (LLM access)
- `HUMANLOOP_API_KEY` (Feedback service)

---

## Incident Response

### If Compromised

1. **Immediate Actions**:
   - Disable compromised credentials
   - Rotate all secrets
   - Review access logs
   - Notify affected users

2. **Investigation**:
   - Determine scope of breach
   - Identify root cause
   - Assess data exposure
   - Document timeline

3. **Remediation**:
   - Deploy security fix
   - Implement monitoring
   - Update security controls
   - Request audit

4. **Communication**:
   - Notify users (if data exposed)
   - Post-incident report
   - Transparency with community

---

## Security Headers

### Recommended Headers (for deployment)

```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

Configured in FastAPI via middleware:
```python
app.add_middleware(SecurityHeadersMiddleware)
```

---

## Dependencies Security

### Critical Dependencies

| Package | Purpose | Update Frequency |
|---------|---------|------------------|
| FastAPI | Web framework | Every release (minor updates ok) |
| SQLAlchemy | ORM | Q3 (quarterly) |
| OpenAI | LLM access | As released |
| Sentence-Transformers | Embeddings | Q3 |
| FAISS | Vector index | Q6 (monthly) |

### Update Process

1. Test updates locally first
2. Run full test suite
3. Deploy to staging
4. Monitor for issues
5. Deploy to production

### Supply Chain Security

- Verify package signatures
- Use exact version pinning in production
- Review dependency changelogs
- Monitor for retracted packages

---

## Monitoring & Alerting

### Monitored Events

- Failed authentication attempts
- Rate limit violations
- Database errors
- API response time degradation
- Unusual data access patterns
- System resource exhaustion

### Alerting Thresholds

- **High Priority**: Auth failures >10/min, DB down, API errors >1%
- **Medium Priority**: Slow queries >1s, Cache misses >50%
- **Low Priority**: Deployment events, scheduled tasks

---

## Best Practices for Developers

### When Writing Code

- ✅ Validate all inputs (Pydantic schemas)
- ✅ Use parameterized queries (SQLAlchemy ORM)
- ✅ Hash sensitive data (passwords, tokens)
- ✅ Log security events (auth, changes)
- ✅ Add type hints (catch errors early)
- ✅ Comment non-obvious security logic
- ❌ Never log passwords or tokens
- ❌ Never hardcode secrets
- ❌ Never use eval() or exec()
- ❌ Never trust user input directly

### Code Review Checklist

- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention (parameterized)
- [ ] Auth checks on protected endpoints
- [ ] Error messages don't leak info
- [ ] Logging doesn't include secrets
- [ ] Rate limiting on public endpoints

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-syntax.html)

---

## Contact

- **Security Issues**: security@yourdomain.com
- **General Questions**: contact@yourdomain.com
- **Twitter**: @yourhandle

---

**Last Updated**: April 2026  
**Next Review**: April 2027
