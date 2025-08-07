#!/usr/bin/env python3
"""SDK API Usage Analysis Script.

This script analyzes the AI Chatbot SDK to identify potential issues with API endpoint usage,
including deprecated endpoints, incorrect URLs, and missing endpoints.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_api_routes_from_file(file_path: Path) -> List[Tuple[str, str, str]]:
    """Extract API routes from FastAPI router files.

    Returns:
        List of (method, route, function_name) tuples

    """
    routes = []

    with open(file_path) as f:
        content = f.read()

    # Find @router.method("/path") patterns - handle multi-line definitions
    # This regex handles both single-line and multi-line router definitions
    route_pattern = r'@router\.(\w+)\(\s*"([^"]+)"[^)]*\)(?:\s*@[^)]+\))*\s*async def (\w+)'
    matches = re.findall(route_pattern, content, re.MULTILINE | re.DOTALL)

    for method, route, func_name in matches:
        routes.append((method.upper(), route, func_name))

    # Handle edge cases where the route definition spans multiple lines
    # Look for patterns like @router.post(\n    "/path"
    multiline_pattern = r'@router\.(\w+)\(\s*\n\s*"([^"]+)"[^)]*\)(?:\s*@[^)]+\))*\s*async def (\w+)'
    multiline_matches = re.findall(multiline_pattern, content, re.MULTILINE | re.DOTALL)

    for method, route, func_name in multiline_matches:
        # Avoid duplicates
        if (method.upper(), route, func_name) not in [(m, r, f) for m, r, f in routes]:
            routes.append((method.upper(), route, func_name))

    return routes


def extract_sdk_api_calls(file_path: Path) -> List[Tuple[str, str, str]]:
    """Extract API calls from SDK file.

    Returns:
        List of (method, endpoint, context) tuples

    """
    calls = []

    with open(file_path) as f:
        content = f.read()

    # Find self.sdk._request() calls
    request_pattern = r'await self\.sdk\._request\(\s*"([^"]+)"[^,]*(?:,\s*[^,]*)?(?:,\s*method="([^"]+)")?[^)]*\)'
    matches = re.findall(request_pattern, content)

    for endpoint, method in matches:
        method = method.upper() if method else "GET"
        calls.append((method, endpoint, "SDK call"))

    return calls


def analyze_api_coverage():
    """Analyze API endpoint coverage and identify issues."""
    # Get all API routes from the backend
    api_dir = project_root / "app" / "api"
    all_routes = {}

    for api_file in api_dir.glob("*.py"):
        if api_file.name == "__init__.py":
            continue

        routes = extract_api_routes_from_file(api_file)
        module_name = api_file.stem
        all_routes[module_name] = routes

    # Get SDK calls
    sdk_file = project_root / "client" / "ai_chatbot_sdk.py"
    sdk_calls = extract_sdk_api_calls(sdk_file)

    # Read main.py to get route prefixes
    main_file = project_root / "app" / "main.py"
    with open(main_file) as f:
        main_content = f.read()

    prefixes = {}
    prefix_pattern = r'app\.include_router\((\w+)_router,\s*prefix="([^"]+)"'
    prefix_matches = re.findall(prefix_pattern, main_content)

    for router_name, prefix in prefix_matches:
        prefixes[router_name] = prefix

    print("🔍 AI Chatbot SDK API Usage Analysis")
    print("=" * 50)

    # Build full endpoint map
    full_endpoints = {}
    deprecated_endpoints = {}

    for module_name, routes in all_routes.items():
        prefix = prefixes.get(module_name, f"/api/v1/{module_name}")
        for method, route, func_name in routes:
            full_endpoint = prefix + route
            full_endpoints[f"{method} {full_endpoint}"] = {
                'module': module_name,
                'function': func_name,
                'route': route
            }

            # Check for deprecated endpoints
            api_file = api_dir / f"{module_name}.py"
            with open(api_file) as f:
                file_content = f.read()

            if 'deprecated=True' in file_content:
                # Find which functions are deprecated
                func_pattern = rf'@router\.{method.lower()}\("{re.escape(route)}"[^)]*deprecated=True[^)]*\)[^@]*async def {func_name}'
                if re.search(func_pattern, file_content, re.IGNORECASE | re.DOTALL):
                    deprecated_endpoints[f"{method} {full_endpoint}"] = {
                        'module': module_name,
                        'function': func_name
                    }

    # Analyze SDK calls
    print("\n📋 API Endpoint Analysis")
    print("-" * 30)

    issues = []
    correct_calls = []

    for method, endpoint, context in sdk_calls:
        full_call = f"{method} {endpoint}"

        # Check if endpoint exists
        if full_call in full_endpoints:
            if full_call in deprecated_endpoints:
                issues.append({
                    'type': 'DEPRECATED_ENDPOINT',
                    'call': full_call,
                    'description': f"SDK is calling deprecated endpoint: {endpoint}",
                    'severity': 'HIGH'
                })
            else:
                correct_calls.append(full_call)
        else:
            # Check if it's a close match (wrong prefix, etc.)
            possible_matches = []
            for existing_call in full_endpoints.keys():
                existing_method, existing_endpoint = existing_call.split(" ", 1)
                if existing_method == method and existing_endpoint.endswith(endpoint.split("/")[-1]):
                    possible_matches.append(existing_call)

            if possible_matches:
                issues.append({
                    'type': 'INCORRECT_ENDPOINT',
                    'call': full_call,
                    'description': f"SDK calls {endpoint} but should probably call one of: {possible_matches}",
                    'severity': 'HIGH'
                })
            else:
                issues.append({
                    'type': 'MISSING_ENDPOINT',
                    'call': full_call,
                    'description': f"SDK calls non-existent endpoint: {endpoint}",
                    'severity': 'CRITICAL'
                })

    # Print results
    print(f"✅ Correct API calls: {len(correct_calls)}")
    print(f"⚠️  Issues found: {len(issues)}")

    if issues:
        print("\n🚨 Issues Detected:")
        print("-" * 20)

        for i, issue in enumerate(issues, 1):
            severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
            print(f"{i}. {severity_emoji.get(issue['severity'], '⚪')} {issue['type']} ({issue['severity']})")
            print(f"   Call: {issue['call']}")
            print(f"   Issue: {issue['description']}")
            print()

    print("\n📊 Summary:")
    print("-" * 12)
    print(f"Total API endpoints available: {len(full_endpoints)}")
    print(f"Deprecated endpoints: {len(deprecated_endpoints)}")
    print(f"SDK API calls analyzed: {len(sdk_calls)}")
    print(f"Issues requiring fixes: {len(issues)}")

    # Print deprecated endpoints
    if deprecated_endpoints:
        print("\n⚠️  Deprecated Endpoints:")
        print("-" * 25)
        for endpoint, info in deprecated_endpoints.items():
            print(f"  • {endpoint} in {info['module']}.py ({info['function']})")

    return issues


if __name__ == "__main__":
    issues = analyze_api_coverage()

    if issues:
        print(f"\n🔧 Found {len(issues)} issues that need to be fixed in the SDK")
        sys.exit(1)
    else:
        print("\n✅ All SDK API calls are correct!")
        sys.exit(0)
