#!/usr/bin/env python3
"""
Verification script for Weather Agent setup
Checks if all components are configured correctly
"""
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_environment():
    """Check if .env file exists and is configured"""
    print("🔍 Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Run: echo 'GOOGLE_API_KEY=your_key' > .env")
        return False
    
    # Check if GOOGLE_API_KEY is set
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("❌ GOOGLE_API_KEY not configured in .env")
        print("   Get key from: https://aistudio.google.com/apikey")
        return False
    
    print(f"✅ GOOGLE_API_KEY configured ({api_key[:10]}...)")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        ("google.adk", "Google ADK"),
        ("google.genai", "Google GenAI SDK"),
        ("mcp", "MCP"),
        ("fastmcp", "FastMCP"),
        ("dotenv", "python-dotenv"),
        ("httpx", "httpx"),
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_installed = False
    
    if not all_installed:
        print("\n   Install with: uv sync")
        print("   Or: pip install google-adk google-genai mcp fastmcp python-dotenv httpx")
    
    return all_installed

def check_agent_structure():
    """Check if agent directory structure is correct"""
    print("\n🔍 Checking agent structure...")
    
    required_files = [
        "weather_agent/agent.py",
        "weather_agent/__init__.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False
    
    return all_exist

def check_mcp_server():
    """Check if MCP server is accessible"""
    print("\n🔍 Checking MCP server connectivity...")
    
    server_urls = [
        "http://localhost:8085/mcp",
        "https://weather-mcp-server-oze7nwnjba-as.a.run.app"
    ]
    
    try:
        import httpx
        import asyncio
        
        async def test_connection():
            async with httpx.AsyncClient() as client:
                for url in server_urls:
                    try:
                        response = await client.get(url, timeout=5.0)
                        if response.status_code in [200, 404, 405]:
                            return url, True
                    except Exception:
                        pass
                return server_urls[0], False
        
        url, ok = asyncio.run(test_connection())
        
        if ok:
            print(f"✅ MCP server reachable at {url}")
            return True
        else:
            print(f"⚠️  MCP server not reachable at {url}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot reach MCP server: {e}")
        return False

def check_agent_import():
    """Try to import the agent"""
    print("\n🔍 Checking agent import...")
    
    try:
        # Suppress warnings during import
        import warnings
        warnings.filterwarnings("ignore")
        
        from weather_agent import root_agent
        print(f"✅ Agent imported successfully: {root_agent.name}")
        print(f"   Model: {root_agent.model}")
        return True
    except Exception as e:
        print(f"❌ Failed to import agent: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Weather Agent Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        check_environment(),
        check_dependencies(),
        check_agent_structure(),
        check_mcp_server(),
        check_agent_import(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed!")
        print("\n🚀 Ready to start!")
        print("   Run: ./start_agent.sh")
        print("   Or:  uv run adk web")
        print("\n📍 Then open: http://localhost:8000")
        return 0
    else:
        print("❌ Some checks failed")
        print("\n⚠️  Fix the issues above and run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())

