<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://github.com/Mqxx/GitHub-Markdown/blob/main/blockquotes/badge/light-theme/info.svg">
  <img alt="Info" src="https://github.com/Mqxx/GitHub-Markdown/blob/main/blockquotes/badge/dark-theme/info.svg">
</picture><br>

**Note:** I no longer have access to Came Connect, nor do I have a CAME gateway or slave, so I won't be able to maintain this further. I've switched recently to an ESP32 + Relays + Tasmota based opener, which is more reliable and doesn't require the cloud.

# came-connect

An unofficial Python library/Web Server to use [Came Connect](https://www.cameconnect.net) for home automation purposes such as automating the control of gates via Home Assistant.

The library lets you authenticate with the Came Connect service, and view the status of devices, issue commands or return the status of inputs.

It was designed with usage of a CAME Ethernet Gateway (RETH001) and associated RF slave (RSLV001) in mind.

It can be used as a CLI, via `cli.py`.

Running `main.py` will start a local RESTful web server, that you can interact with using. This web server can be used with, for example, Home Assistant's [RESTful command](https://www.home-assistant.io/integrations/rest_command/) integration to trigger automations with Gates etc.

## Docker

### Build
`docker build -t jasonmadigan/came-connect .`

## Install Deps

`pipenv install`


## Pre-reqs

You need to setup some environment variables to run both the CLI and the web server.

You need to fetch two values from the Came Connect login page. To get:
- Visit https://www.cameconnect.net/login
- View the source of https://www.cameconnect.net/main.XXX.js
- Search for `clientId` - this will be your `CAME_CONNECT_CLIENT_ID` value
- Search for `clientSecret` - this will be your `CAME_CONNECT_CLIENT_SECRET` value

| Env Var   |      Description      |
|----------|-------------|
| `CAME_CONNECT_CLIENT_ID` |  See above |
| `CAME_CONNECT_CLIENT_SECRET` | See above  |
| `CAME_CONNECT_USERNAME` | Username for the https://www.cameconnect.net portal |
| `CAME_CONNECT_PASSWORD` | Password for the https://www.cameconnect.net portal |
| `CAME_CONNECT_API_KEY` | (Optional) API key for securing web server endpoints. If not set, endpoints are accessible without authentication (backward compatible). Strongly recommended for production use. |


## Security

### API Key Authentication

For production use, it is **strongly recommended** to set the `CAME_CONNECT_API_KEY` environment variable to secure your web server endpoints. When set, all API requests must include an `X-API-Key` header with the correct API key.

Generate a secure API key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Security Features

This application includes the following security controls:

- **Input Validation**: Device IDs and command IDs are validated to prevent injection attacks
- **Cryptographically Secure Random**: Uses `secrets` module instead of `random` for security-sensitive operations
- **Request Timeouts**: All API requests have a 30-second timeout to prevent hanging
- **Error Handling**: Proper exception handling to prevent information leakage
- **Security Headers**: Includes X-Content-Type-Options, X-Frame-Options, and X-XSS-Protection headers
- **Logging**: Comprehensive logging for security auditing and troubleshooting
- **Environment Variable Validation**: Checks required environment variables on startup

### Security Best Practices

- Always use HTTPS when exposing this service to the internet (e.g., behind a reverse proxy like nginx)
- Set a strong `CAME_CONNECT_API_KEY` for production deployments
- Regularly rotate your API keys and CAME Connect credentials
- Monitor logs for suspicious activity
- Keep dependencies up to date


## Run

`pipenv run python main.py --help`


```
docker run -p --rm 9002:8080 --name=came-connect -e CAME_CONNECT_CLIENT_ID=xxx -e CAME_CONNECT_CLIENT_SECRET=xxx -e CAME_CONNECT_USERNAME=xxx -e CAME_CONNECT_PASSWORD=xxx -e CAME_CONNECT_API_KEY=your-secure-key-here ghcr.io/jasonmadigan/came-connect:main
```


## Commands

In the examples below, we have a RSLV001 slave device (with an example ID: 11111), with two outputs configured - one for closing a gate (command ID: 2), one for opening it (command ID: 5). Triggering these outputs on cameconnect.net, with an eye on the Dev Tools console in your browser of choice, we can get the ID of these specific commands. Our `came-connect` container is running on 192.168.1.100.

### Read sites

TODO

### Fetch Device statuses

TODO

### Run device commands

`curl -H "X-API-Key: your-api-key-here" http://192.168.1.100:9002/devices/<device_id>/command/<command_id>`

**Note:** If `CAME_CONNECT_API_KEY` environment variable is set, you must include the `X-API-Key` header with your requests.

You can get the device or command IDs by triggering these outputs while on cameconnect.net, with a network tab open in your browser.

### Example Home Assistant integration

With API key authentication:

```yaml
# configuration.yaml

rest_command:
  gate_open:
    url: "http://192.168.1.100:9002/devices/<device_id>/command/5"
    method: GET
    headers:
      X-API-Key: "your-api-key-here"
  gate_close:
    url: "http://192.168.1.100:9002/devices/<device_id>/command/2"
    method: GET
    headers:
      X-API-Key: "your-api-key-here"
```

Without API key (backward compatible, not recommended):

```yaml
# configuration.yaml

rest_command:
  gate_open:
    url: "http://192.168.1.100:9002/devices/<device_id>/command/5"
    method: GET
  gate_close:
    url: "http://192.168.1.100:9002/devices/<device_id>/command/2"
    method: GET
```
