"""
Test script for AEO Protocol Checker

Run with: python test_protocol.py
"""

import asyncio
from app.services.protocol import check_aeo_protocols


async def main():
    # Test with a real URL (or use a test site)
    test_url = "https://hijabti.ae/products/shimmer-georgette-hijab-dusty-rose"  # Example site
    
    print(f"Testing AEO protocol compliance for: {test_url}\n")
    print("=" * 60)
    
    results = await check_aeo_protocols(test_url)
    
    # Display results
    print("\n📄 llms.txt Check:")
    print(f"  Status: {results['llms_txt']['status']}")
    print(f"  Severity: {results['llms_txt']['severity']}")
    if 'issue' in results['llms_txt']:
        print(f"  Issue: {results['llms_txt']['issue']}")
    if 'valid_structure' in results['llms_txt']:
        print(f"  Valid Structure: {results['llms_txt']['valid_structure']}")
    
    print("\n🤖 agent-card.json Check:")
    print(f"  Status: {results['agent_card']['status']}")
    print(f"  Severity: {results['agent_card']['severity']}")
    if 'issue' in results['agent_card']:
        print(f"  Issue: {results['agent_card']['issue']}")
    if 'schema_valid' in results['agent_card']:
        print(f"  Schema Valid: {results['agent_card']['schema_valid']}")
    
    print("\n🤖 robots.txt Check:")
    print(f"  Status: {results['robots_txt']['status']}")
    print(f"  Severity: {results['robots_txt']['severity']}")
    if 'ai_agents_blocked' in results['robots_txt']:
        blocked = results['robots_txt']['ai_agents_blocked']
        if blocked:
            print(f"  ⚠️  Blocked AI Agents: {', '.join(blocked)}")
        else:
            print(f"  ✅ No AI agents blocked")
    if 'sitemap_present' in results['robots_txt']:
        print(f"  Sitemap Present: {results['robots_txt']['sitemap_present']}")
    
    print("\n" + "=" * 60)
    print("\nFull results:")
    import json
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
