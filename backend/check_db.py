"""Simple database check for violations."""
import asyncio
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:Summerjoon202511!@localhost:5432/claims_saas_db"

def main():
    engine = create_engine(DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # First get the specific review details
    review = session.execute(text("""
        SELECT id, status, compliance_score, risk_score, summary, error_message
        FROM reviews 
        WHERE id = 'c21ed5f6-e6f5-4afb-9750-e7854480a1a5'
    """)).fetchone()
    
    if review:
        print("=" * 70)
        print("SPECIFIC REVIEW: c21ed5f6-e6f5-4afb-9750-e7854480a1a5")
        print("=" * 70)
        print(f"Status: {review[1]}")
        print(f"Compliance Score: {review[2]}")
        print(f"Risk Score: {review[3]}")
        print(f"Summary: {str(review[4])[:300] if review[4] else 'N/A'}...")
        print(f"Error: {review[5]}")
        
        # Get violations for this review
        violations = session.execute(text("""
            SELECT regulation, severity, agent_source, explanation, original_text
            FROM violations 
            WHERE review_id = 'c21ed5f6-e6f5-4afb-9750-e7854480a1a5'
            ORDER BY created_at
        """)).fetchall()
        
        print(f"\n🚨 Violations Found: {len(violations)}")
        for i, v in enumerate(violations, 1):
            print(f"\n  [{i}] {v[0]} ({v[1]})")
            print(f"      Agent: {v[2]}")
            print(f"      Explanation: {str(v[3])[:150]}...")
            print(f"      Violating Text: {str(v[4])[:100]}...")
    
    print("=" * 60)
    print("DATABASE COMPLIANCE DATA CHECK")
    print("=" * 60)
    
    # Check reviews
    reviews = session.execute(text("""
        SELECT id, status, compliance_score, risk_score, summary, created_at
        FROM reviews 
        ORDER BY created_at DESC 
        LIMIT 10
    """)).fetchall()
    
    print(f"\n📋 Recent Reviews ({len(reviews)})")
    print("-" * 60)
    for r in reviews:
        print(f"  [{r[1]}] ID: {str(r[0])[:8]}... Score: {r[2]}/{r[3]} @ {r[5]}")
    
    # Check violations
    violations = session.execute(text("""
        SELECT v.id, v.regulation, v.severity, v.agent_source, v.explanation, r.status
        FROM violations v
        JOIN reviews r ON v.review_id = r.id
        ORDER BY v.created_at DESC 
        LIMIT 20
    """)).fetchall()
    
    print(f"\n🚨 Recent Violations ({len(violations)})")
    print("-" * 60)
    for v in violations:
        print(f"\n  [{v[2]}] {v[1]}")
        print(f"       Agent: {v[3]}")
        print(f"       Review Status: {v[5]}")
        explanation = str(v[4])[:100] if v[4] else "N/A"
        print(f"       Explanation: {explanation}...")
    
    # Check audit logs
    audit_logs = session.execute(text("""
        SELECT agent_name, action, status, timestamp, details
        FROM audit_logs
        ORDER BY timestamp DESC
        LIMIT 30
    """)).fetchall()
    
    print(f"\n📝 Recent Audit Logs ({len(audit_logs)})")
    print("-" * 60)
    for log in audit_logs[:20]:
        details = str(log[4])[:50] if log[4] else ""
        print(f"  [{log[2]}] {log[0]}: {log[1]} @ {log[3]} {details}")
    
    # Check Bedrock call logs
    bedrock_logs = session.execute(text("""
        SELECT agent_name, latency_ms, input_tokens, output_tokens, created_at
        FROM bedrock_call_logs
        ORDER BY created_at DESC
        LIMIT 10
    """)).fetchall()
    
    print(f"\n🤖 Recent Bedrock Calls ({len(bedrock_logs)})")
    print("-" * 60)
    for log in bedrock_logs:
        print(f"  {log[0]}: {log[1]}ms, {log[2]} in / {log[3]} out @ {log[4]}")
    
    session.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
