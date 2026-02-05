# Security Quick Start Guide

## For New Users

### 1. Generate a Strong API Key
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
Save this key securely - you'll need it for all API requests.

### 2. Set Environment Variables
```bash
export CAME_CONNECT_CLIENT_ID="your-client-id"
export CAME_CONNECT_CLIENT_SECRET="your-client-secret"
export CAME_CONNECT_USERNAME="your-username"
export CAME_CONNECT_PASSWORD="your-password"
export CAME_CONNECT_API_KEY="your-generated-api-key"
```

### 3. Run with Docker (Recommended)
```bash
docker run -p 9002:8080 --rm --name=came-connect \
  -e CAME_CONNECT_CLIENT_ID="xxx" \
  -e CAME_CONNECT_CLIENT_SECRET="xxx" \
  -e CAME_CONNECT_USERNAME="xxx" \
  -e CAME_CONNECT_PASSWORD="xxx" \
  -e CAME_CONNECT_API_KEY="xxx" \
  ghcr.io/jasonmadigan/came-connect:main
```

### 4. Make Secure API Requests
```bash
# Always include X-API-Key header
curl -H "X-API-Key: your-api-key" \
  http://localhost:9002/devices/123/command/456
```

## Security Checklist

- [ ] Generated strong API key using `secrets` module
- [ ] Set `CAME_CONNECT_API_KEY` environment variable
- [ ] Using HTTPS (via reverse proxy like nginx) for external access
- [ ] Configured firewall to restrict access to trusted networks
- [ ] Monitoring logs for suspicious activity
- [ ] Using Docker or virtual environment for isolation
- [ ] Keeping dependencies up to date

## Common Mistakes to Avoid

❌ **Don't** expose the service directly to the internet without HTTPS  
✅ **Do** use a reverse proxy with TLS certificates

❌ **Don't** share API keys in code or version control  
✅ **Do** use environment variables or secrets management

❌ **Don't** use weak or predictable API keys  
✅ **Do** generate strong random keys using the `secrets` module

❌ **Don't** ignore log warnings about security  
✅ **Do** monitor and investigate security-related log entries

## Troubleshooting

### "API key required" Error
- Check that you set `CAME_CONNECT_API_KEY` environment variable
- Verify you're including `X-API-Key` header in requests
- Confirm the header value matches the environment variable

### "Invalid device_id" Error
- Ensure device_id is a positive integer (e.g., 123, not "abc")
- Check that the device exists in your CAME Connect account
- Verify you're using the correct device ID from the API

### Environment Variable Errors
- Confirm all required variables are set:
  - `CAME_CONNECT_CLIENT_ID`
  - `CAME_CONNECT_CLIENT_SECRET`
  - `CAME_CONNECT_USERNAME`
  - `CAME_CONNECT_PASSWORD`
- Check for typos in variable names
- Verify variables are exported before running the application

## Need Help?

Check `SECURITY_IMPROVEMENTS.md` for detailed information about all security features and best practices.
