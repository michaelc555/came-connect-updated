import requests
import logging
import string
import secrets
from requests.auth import HTTPBasicAuth
import hashlib
import base64
import re
import time
import json
import web
import os
from functools import wraps
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request timeout in seconds
REQUEST_TIMEOUT = 30

def validate_env_vars() -> None:
    """Validate that all required environment variables are set.
    
    Raises:
        ValueError: If any required environment variable is missing
    """
    required_vars = [
        'CAME_CONNECT_CLIENT_ID',
        'CAME_CONNECT_CLIENT_SECRET',
        'CAME_CONNECT_USERNAME',
        'CAME_CONNECT_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    logger.info("All required environment variables are set")

def validate_device_id(device_id: str) -> bool:
    """Validate that device_id is a positive integer.
    
    Args:
        device_id: Device ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        return int(device_id) > 0
    except (ValueError, TypeError):
        return False

def validate_command_id(command_id: str) -> bool:
    """Validate that command_id is a positive integer.
    
    Args:
        command_id: Command ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        return int(command_id) > 0
    except (ValueError, TypeError):
        return False

def check_api_key(f):
    """Decorator to check API key authentication.
    
    Checks for X-API-Key header against CAME_CONNECT_API_KEY env var.
    If CAME_CONNECT_API_KEY is not set, allows all requests (backward compatible).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.environ.get('CAME_CONNECT_API_KEY')
        
        # If no API key is configured, skip authentication (backward compatible)
        if not api_key:
            logger.warning("No API key configured - authentication disabled")
            return f(*args, **kwargs)
        
        # Check if request has the correct API key
        request_api_key = web.ctx.env.get('HTTP_X_API_KEY')
        
        if not request_api_key:
            logger.warning("Unauthorized access attempt - no API key provided")
            web.ctx.status = '401 Unauthorized'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": "API key required"})
        
        if request_api_key != api_key:
            logger.warning("Unauthorized access attempt - invalid API key")
            web.ctx.status = '401 Unauthorized'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": "Invalid API key"})
        
        return f(*args, **kwargs)
    
    return decorated_function

def replacer(match):
    return match.group(1).upper()

def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge from verifier.
    
    Args:
        code_verifier: PKCE code verifier
        
    Returns:
        Base64 URL-encoded SHA256 hash of the verifier
    """
    encoded_bytes = base64.b64encode(
        hashlib.sha256(str.encode(code_verifier)).digest())
    encoded_str = str(encoded_bytes, "utf-8")
    encoded_str = encoded_str.replace("=", "")
    encoded_str = encoded_str.replace("+", "-")
    encoded_str = encoded_str.replace("/", "_")
    return encoded_str


def fetch_auth_code(code_verifier: str) -> str:
    """Fetch authorization code from CAME Connect API.
    
    Args:
        code_verifier: PKCE code verifier
        
    Returns:
        Authorization code
        
    Raises:
        ValueError: If environment variables are missing
        requests.RequestException: If API request fails
    """
    try:
        client_id = os.environ['CAME_CONNECT_CLIENT_ID']
        client_secret = os.environ['CAME_CONNECT_CLIENT_SECRET']
        username = os.environ['CAME_CONNECT_USERNAME']
        password = os.environ['CAME_CONNECT_PASSWORD']
    except KeyError as e:
        logger.error(f"Missing environment variable: {e}")
        raise ValueError(f"Missing required environment variable: {e}")
    
    nonce = random_string(100)
    state = random_string(100)
    response_type = 'code'
    code_challenge = generate_code_challenge(code_verifier)
    code_challenge_method = 'S256'
    redirect_uri = 'https://www.cameconnect.net/role'

    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'username': username,
        'password': password
    }

    url = "https://app.cameconnect.net/api/oauth/auth-code?client_id={}&response_type={}&redirect_uri={}&state={}&nonce={}&code_challenge={}&code_challenge_method={}".format(
        client_id, response_type, redirect_uri, state, nonce, code_challenge, code_challenge_method)

    try:
        response = requests.post(
            url, data=data, auth=HTTPBasicAuth(client_id, client_secret), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        code = response.json()['code']
        logger.info("Successfully fetched auth code")
        return code
    except requests.RequestException as e:
        logger.error(f"Failed to fetch auth code: {e}")
        raise
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid response format: {e}")
        raise ValueError(f"Invalid API response: {e}")


def random_string(length: int) -> str:
    """Generate a cryptographically secure random string.
    
    Args:
        length: Length of the random string
        
    Returns:
        Cryptographically secure random string
    """
    letters = string.ascii_lowercase
    result_str = ''.join(secrets.choice(letters) for i in range(length))
    return result_str


def fetch_bearer_token(client_id: str, client_secret: str, code: str, code_verifier: str) -> Dict[str, Any]:
    """Fetch bearer token from CAME Connect API.
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        code: Authorization code
        code_verifier: PKCE code verifier
        
    Returns:
        Dictionary containing access_token and expires_in
        
    Raises:
        requests.RequestException: If API request fails
    """
    redirect_uri = 'https://www.cameconnect.net/role'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }

    url = "https://app.cameconnect.net/api/oauth/token"

    try:
        response = requests.post(
            url, data=data, auth=HTTPBasicAuth(client_id, client_secret), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        json_response = response.json()

        bearer = {
            'access_token': json_response['access_token'],
            'expires_in': json_response['expires_in']
        }
        
        logger.info("Successfully fetched bearer token")
        return bearer
    except requests.RequestException as e:
        logger.error(f"Failed to fetch bearer token: {e}")
        raise
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Invalid response format: {e}")
        raise ValueError(f"Invalid API response: {e}")


def fetch_token() -> str:
    """Fetch access token for API authentication.
    
    Returns:
        Access token string
        
    Raises:
        ValueError: If environment variables are missing
        requests.RequestException: If API request fails
    """
    try:
        code_verifier = random_string(100)
        code = fetch_auth_code(code_verifier)
        bearer = fetch_bearer_token(
            os.environ['CAME_CONNECT_CLIENT_ID'], 
            os.environ['CAME_CONNECT_CLIENT_SECRET'], 
            code, 
            code_verifier
        )
        return bearer['access_token']
    except Exception as e:
        logger.error(f"Failed to fetch token: {e}")
        raise

def fetch_sites(token: str) -> Dict[str, Any]:
    """Fetch sites from CAME Connect API.
    
    Args:
        token: Bearer token for authentication
        
    Returns:
        Sites data as dictionary
        
    Raises:
        requests.RequestException: If API request fails
    """
    headers = {"Authorization": "Bearer " + token}
    try:
        sites = requests.get(
            'https://app.cameconnect.net/api/sites', headers=headers, timeout=REQUEST_TIMEOUT)
        sites.raise_for_status()
        logger.info("Successfully fetched sites")
        return sites.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch sites: {e}")
        raise

def fetch_devices(token: str) -> List[Dict[str, Any]]:
    """Fetch devices from CAME Connect API.
    
    Args:
        token: Bearer token for authentication
        
    Returns:
        List of devices
        
    Raises:
        requests.RequestException: If API request fails
    """
    sites = fetch_sites(token)
    devices = sites.get('Data', [{}])[0].get('Devices', [])
    logger.info(f"Successfully fetched {len(devices)} devices")
    return devices

def fetch_device_statuses(token: str) -> Dict[str, Any]:
    """Fetch device statuses from CAME Connect API.
    
    Args:
        token: Bearer token for authentication
        
    Returns:
        Device statuses as dictionary
        
    Raises:
        requests.RequestException: If API request fails
    """
    ids = fetch_all_device_ids(token)
    headers = {"Authorization": "Bearer " + token}
    url = "https://app.cameconnect.net/api/devicestatus?devices=[{}]".format(",".join(ids))

    try:
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        logger.info("Successfully fetched device statuses")
        return res.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch device statuses: {e}")
        raise

def fetch_commands_for_device(token: str, device_id: str) -> Dict[str, Any]:
    """Fetch commands for a specific device.
    
    Args:
        token: Bearer token for authentication
        device_id: Device ID
        
    Returns:
        Commands data as dictionary
        
    Raises:
        ValueError: If device_id is invalid
        requests.RequestException: If API request fails
    """
    if not validate_device_id(device_id):
        raise ValueError(f"Invalid device_id: {device_id}")
    
    headers = {"Authorization": "Bearer " + token}
    url = "https://app.cameconnect.net/api/automations/{}/commands".format(device_id)
    
    try:
        commands = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        commands.raise_for_status()
        logger.info(f"Successfully fetched commands for device {device_id}")
        return commands.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch commands for device {device_id}: {e}")
        raise

def run_command_for_device(token: str, device_id: str, command_id: str) -> Dict[str, Any]:
    """Run a command on a specific device.
    
    Args:
        token: Bearer token for authentication
        device_id: Device ID
        command_id: Command ID
        
    Returns:
        Command execution result as dictionary
        
    Raises:
        ValueError: If device_id or command_id is invalid
        requests.RequestException: If API request fails
    """
    if not validate_device_id(device_id):
        raise ValueError(f"Invalid device_id: {device_id}")
    
    if not validate_command_id(command_id):
        raise ValueError(f"Invalid command_id: {command_id}")
    
    headers = {"Authorization": "Bearer " + token}
    url = "https://app.cameconnect.net/api/automations/{}/commands/{}".format(device_id, command_id)
    
    try:
        res = requests.post(url, headers=headers, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        logger.info(f"Successfully ran command {command_id} on device {device_id}")
        return res.json()
    except requests.RequestException as e:
        logger.error(f"Failed to run command {command_id} on device {device_id}: {e}")
        raise

def fetch_all_device_ids(token: str) -> List[str]:
    """Fetch all device IDs.
    
    Args:
        token: Bearer token for authentication
        
    Returns:
        List of device IDs as strings
    """
    devices = fetch_devices(token)
    ids = []
    for device in devices:
        ids.append(str(device.get('Id')))
    return ids

urls = (
    '/devices/(.*)/command/(.*)', 'devices_command',
    '/devices/status/(.*)', 'device_status'
)
app = web.application(urls, globals())

class devices_command:
    @check_api_key
    def GET(self, device_id: str, command_id: str):
        """Execute a command on a device.
        
        Args:
            device_id: Device ID
            command_id: Command ID
            
        Returns:
            JSON response with command execution result
        """
        try:
            # Validate inputs
            if not validate_device_id(device_id):
                web.ctx.status = '400 Bad Request'
                web.header('Content-Type', 'application/json')
                return json.dumps({"error": "Invalid device_id"})
            
            if not validate_command_id(command_id):
                web.ctx.status = '400 Bad Request'
                web.header('Content-Type', 'application/json')
                return json.dumps({"error": "Invalid command_id"})
            
            token = fetch_token()
            res = run_command_for_device(token, device_id, command_id)
            
            # Add security headers
            web.header('Content-Type', 'application/json')
            web.header('X-Content-Type-Options', 'nosniff')
            web.header('X-Frame-Options', 'DENY')
            web.header('X-XSS-Protection', '1; mode=block')
            
            return json.dumps(res)
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": str(e)})
        except requests.RequestException as e:
            logger.error(f"API error: {e}")
            web.ctx.status = '502 Bad Gateway'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": "Failed to communicate with CAME Connect API"})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            web.ctx.status = '500 Internal Server Error'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": "Internal server error"})

class device_status:
    STATUS_MAP = {
        16: "Open",
        32: "Opening",
        33: "Closing",
        17: "Closed",
        19: "Stopped (Partially Open)"
    }

    @check_api_key
    def GET(self, device_id: str):
        """Get status of a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Device status string
        """
        try:
            # Validate input
            if not validate_device_id(device_id):
                web.ctx.status = '400 Bad Request'
                web.header('Content-Type', 'application/json')
                return json.dumps({"error": "Invalid device_id"})
            
            token = fetch_token()
            res = fetch_device_statuses(token)
            device = next((d for d in res.get("Data", []) if str(d["Id"]) == device_id), None)

            if not device:
                web.ctx.status = '404 Not Found'
                web.header('Content-Type', 'application/json')
                return json.dumps({"error": "Device not found"})

            # Extract status from Data array
            status_code = device["States"][0]["Data"][0]
            status_meaning = self.STATUS_MAP.get(status_code, "Unknown Status")

            # Add security headers
            web.header('Content-Type', 'text/plain')
            web.header('X-Content-Type-Options', 'nosniff')
            web.header('X-Frame-Options', 'DENY')
            web.header('X-XSS-Protection', '1; mode=block')
            
            return status_meaning
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": str(e)})
        except requests.RequestException as e:
            logger.error(f"API error: {e}")
            web.ctx.status = '502 Bad Gateway'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": "Failed to communicate with CAME Connect API"})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            web.ctx.status = '500 Internal Server Error'
            web.header('Content-Type', 'application/json')
            return json.dumps({"error": "Internal server error"})

if __name__ == "__main__":
    # Validate environment variables on startup
    try:
        validate_env_vars()
        logger.info("Starting CAME Connect web server")
        app.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        exit(1)
