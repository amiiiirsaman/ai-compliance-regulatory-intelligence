"""Check latest review results."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:Summerjoon202511!@localhost:5432/claims_saas_db')
Session = sessionmaker(bind=engine)
session = Session()

# Get the latest review
review = session.execute(text("""
    SELECT id, status, compliance_score, risk_score
    FROM reviews 
    ORDER BY created_at DESC 
    LIMIT 1
""")).fetchone()

print("=" * 60)
print("LATEST REVIEW RESULTS")
print("=" * 60)
print(f"Review ID: {review[0]}")
print(f"Status: {review[1]}")
print(f"Compliance Score: {review[2]}")
print(f"Risk Score: {review[3]}")

# Count violations by agent
violations = session.execute(text("""
    SELECT agent_source, COUNT(*) as count, 
           SUM(CASE WHEN severity::text = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
           SUM(CASE WHEN severity::text = 'HIGH' THEN 1 ELSE 0 END) as high
    FROM violations 
    WHERE review_id = :review_id
    GROUP BY agent_source
    ORDER BY count DESC
"""), {"review_id": str(review[0])}).fetchall()

print("\nViolations by Agent:")
print("-" * 60)
total = 0
for v in violations:
    print(f"  {v[0]}: {v[1]} violations (Critical: {v[2]}, High: {v[3]})")
    total += v[1]
print(f"\nTOTAL VIOLATIONS: {total}")

session.close()
