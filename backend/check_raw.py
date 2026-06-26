"""Check final audit trail for errors."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:Summerjoon202511!@localhost:5432/claims_saas_db')
Session = sessionmaker(bind=engine)
session = Session()

# Get the final audit log entry with raw details
logs = session.execute(text("""
    SELECT details
    FROM audit_logs 
    WHERE agent_name = 'audit_trail'
    AND action = 'final_summary'
    ORDER BY timestamp DESC
    LIMIT 1
""")).fetchall()

for log in logs:
    print(f'Type: {type(log[0])}')
    print(f'Raw value:')
    print(log[0])

session.close()
