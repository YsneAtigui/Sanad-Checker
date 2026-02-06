"""
Test script for Edge Visibility Tester

Run with: python test_edge.py
"""

import asyncio
from app.services.edge_visibility import (
    comprehensive_edge_test,
    test_ai_agent_access,
    check_cloudflare_config
)


async def main():
    # Test URL
    test_url = "https://hijabti.ae/"
    
    print(f"Testing Edge Visibility for: {test_url}\n")
    print("=" * 80)
    
    # Run comprehensive test
    print("\n🔍 Running Comprehensive Edge Visibility Test...")
    print("-" * 80)
    
    results = await comprehensive_edge_test(test_url)
    
    # Display AI agent results
    print("\n🤖 AI Agent Access Results:")
    print("-" * 80)
    
    for agent_name, data in results['ai_agents'].items():
        accessible = data.get('accessible')
        
        if accessible is True:
            status_icon = "✅"
            status_text = "ACCESSIBLE"
        elif accessible is False:
            status_icon = "❌"
            status_text = "BLOCKED"
        else:
            status_icon = "⚠️"
            status_text = f"{str(accessible).upper()}"
        
        print(f"\n{status_icon} {agent_name.upper()}: {status_text}")
        
        if 'reason' in data:
            print(f"   Reason: {data['reason']}")
        
        if 'status_code' in data:
            print(f"   Status Code: {data['status_code']}")
        
        if 'blocked_by' in data:
            print(f"   Blocked By: {data['blocked_by']}")
        
        print(f"   Severity: {data.get('severity', 'unknown')}")
    
    # Display Cloudflare results
    print("\n\n☁️  Cloudflare Configuration:")
    print("-" * 80)
    
    cf = results['cloudflare']
    
    if cf.get('cloudflare_detected'):
        print("✅ Cloudflare detected")
        print(f"   CF-Ray: {cf.get('cf_headers', {}).get('cf-ray', 'N/A')}")
        print(f"   Server: {cf.get('cf_headers', {}).get('server', 'N/A')}")
    else:
        print("❌ Cloudflare NOT detected")
    
    if cf.get('blocks_ai_agents'):
        print(f"\n⚠️  BLOCKS AI AGENTS")
        print(f"   Bot Status: {cf.get('bot_status')}")
        print(f"   Browser Status: {cf.get('browser_status')}")
        
        if 'recommendation' in cf:
            print(f"\n💡 Recommendation:")
            print(f"   {cf['recommendation']}")
    else:
        print("\n✅ Does NOT block AI agents")
    
    # Display summary
    print("\n\n📊 Summary:")
    print("-" * 80)
    
    summary = results['summary']
    
    print(f"Total Agents Tested: {summary['total_agents_tested']}")
    print(f"✅ Accessible: {summary['accessible_agents']}")
    print(f"❌ Blocked: {summary['blocked_agents']}")
    print(f"⚠️  Suspicious: {summary['suspicious_agents']}")
    print(f"\nFully Accessible: {'YES ✅' if summary['fully_accessible'] else 'NO ❌'}")
    print(f"Overall Severity: {summary['severity'].upper()}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
