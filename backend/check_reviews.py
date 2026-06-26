"""Check completed reviews in database."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5432, 
    user='postgres', 
    password='Summerjoon202511!', 
    dbname='claims_saas_db'
)
cur = conn.cursor()

# Get completed reviews with violation counts
cur.execute('''
SELECT 
    d.original_filename,
    r.status, 
    r.compliance_score, 
    r.risk_score,
    (SELECT COUNT(*) FROM violations v WHERE v.review_id = r.id) as total_violations,
    (SELECT COUNT(*) FROM violations v WHERE v.review_id = r.id AND v.severity = 'CRITICAL') as critical,
    (SELECT COUNT(*) FROM violations v WHERE v.review_id = r.id AND v.severity = 'HIGH') as high,
    (SELECT COUNT(*) FROM violations v WHERE v.review_id = r.id AND v.severity = 'MEDIUM') as medium,
    (SELECT COUNT(*) FROM violations v WHERE v.review_id = r.id AND v.severity = 'LOW') as low,
    (SELECT string_agg(DISTINCT v.agent_source, ', ') FROM violations v WHERE v.review_id = r.id) as agents
FROM reviews r 
JOIN documents d ON r.document_id = d.id 
WHERE r.status = 'COMPLETE'
ORDER BY r.created_at DESC 
LIMIT 10
''')
rows = cur.fetchall()

print("=" * 110)
print("COMPLETED REVIEWS")
print("=" * 110)
print(f"{'Filename':<35} {'Score':>6} {'Risk':>5} {'Total':>6} {'C':>3} {'H':>3} {'M':>3} {'L':>3} Agents")
print("-" * 110)
for row in rows:
    filename = (row[0] or "")[:35]
    score = row[2] or 0
    risk = row[3] or 0
    total = row[4] or 0
    critical = row[5] or 0
    high = row[6] or 0
    medium = row[7] or 0
    low = row[8] or 0
    agents = (row[9] or "")[:50]
    print(f"{filename:<35} {score:>6} {risk:>5} {total:>6} {critical:>3} {high:>3} {medium:>3} {low:>3} {agents}")

# Summary of all agents that have been triggered
cur.execute('''
SELECT DISTINCT agent_source, COUNT(*) as count
FROM violations
GROUP BY agent_source
ORDER BY count DESC
''')
print("\n" + "=" * 50)
print("AGENT COVERAGE SUMMARY")
print("=" * 50)
for row in cur.fetchall():
    print(f"  {row[0]:<30} {row[1]:>5} violations")

conn.close()
