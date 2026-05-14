import os
from typing import Optional, Dict, Any

class ProxyHandler:
    @staticmethod
    def get_oxylabs_proxy_url() -> Optional[str]:
        user = os.getenv("OXYLABS_PROXY_USERNAME")
        password = os.getenv("OXYLABS_PROXY_PASSWORD")
        host = os.getenv("OXYLABS_PROXY", "dc.oxylabs.io:8000")
        country = os.getenv("OXYLABS_PROXY_COUNTRY", "US")
        
        if not user or not password:
            return None
            
        # Format: http://user-username-country-US:password@dc.oxylabs.io:8000
        return f"http://user-{user}-country-{country}:{password}@{host}"

    @staticmethod
    def get_proxyscrape_proxy_url() -> Optional[str]:
        user = os.getenv("PROXYSCRAPE_PROXY_USERNAME")
        password = os.getenv("PROXYSCRAPE_PROXY_PASSWORD")
        # Using the host/port from the user's test_proxy.py
        host = "193.56.28.161:3129"
        
        if not user or not password:
            return None
            
        return f"http://{user}:{password}@{host}"

    @staticmethod
    def get_jobspy_proxies() -> Optional[list]:
        """Returns proxies in format expected by JobSpy."""
        url = ProxyHandler.get_oxylabs_proxy_url() or ProxyHandler.get_proxyscrape_proxy_url()
        return [url] if url else None

    @staticmethod
    def get_playwright_proxy() -> Optional[Dict[str, str]]:
        """Returns proxy config for Playwright context."""
        # Prefer Oxylabs for Playwright/Browsing
        user = os.getenv("OXYLABS_PROXY_USERNAME")
        password = os.getenv("OXYLABS_PROXY_PASSWORD")
        host = os.getenv("OXYLABS_PROXY", "dc.oxylabs.io:8000")
        country = os.getenv("OXYLABS_PROXY_COUNTRY", "US")

        if user and password:
            return {
                "server": f"http://{host}",
                "username": f"user-{user}-country-{country}",
                "password": password
            }
            
        # Fallback to ProxyScrape
        ps_user = os.getenv("PROXYSCRAPE_PROXY_USERNAME")
        ps_pass = os.getenv("PROXYSCRAPE_PROXY_PASSWORD")
        if ps_user and ps_pass:
            return {
                "server": "http://193.56.28.161:3129",
                "username": ps_user,
                "password": ps_pass
            }
            
        return None
