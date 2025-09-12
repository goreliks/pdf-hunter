from langchain.tools import tool
import whois
from whois.parser import PywhoisError
import datetime

@tool
def domain_whois(domain: str) -> str:
    """
    Performs a WHOIS lookup on a root domain to gather registration details.
    This is critical for verifying the identity and age of a website.
    Use this on the main part of the domain (e.g., 'example.com' from 'http://login.example.com/auth').
    """
    try:
        w = whois.whois(domain)
        
        if w.get('domain_name') is None:
            return f"Error: No WHOIS record found for domain '{domain}'. It may be available for registration or an invalid domain."

        # Make dates JSON serializable for easier processing by the LLM
        for key, value in w.items():
            if isinstance(value, datetime.datetime):
                w[key] = value.isoformat()
            elif isinstance(value, list) and all(isinstance(item, datetime.datetime) for item in value):
                w[key] = [item.isoformat() for item in value]

        # Return a clean, concise summary of the most important fields
        creation_date = w.get('creation_date')
        registrar = w.get('registrar')
        
        summary = (
            f"WHOIS Record for: {w.get('domain_name')}\n"
            f"Registrar: {registrar}\n"
            f"Creation Date: {creation_date}\n"
            f"Expiration Date: {w.get('expiration_date')}\n"
            f"Name Servers: {w.get('name_servers')}"
        )
        return summary

    except PywhoisError as e:
        return f"Error: Could not retrieve WHOIS data for '{domain}'. It might be a subdomain or an invalid domain. Error: {e}"
    except Exception as e:
        return f"An unexpected error occurred during WHOIS lookup for '{domain}': {e}"
