"""Check final audit trail for errors."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

engine = create_engine('postgresql://postgres:Summerjoon202511!@localhost:5432/claims_saas_db')
Session = sessionmaker(bind=engine)
session = Session()

# Get the final audit log entry 
logs = session.execute(text("""
    SELECT agent_name, details
    FROM audit_logs 
    WHERE review_id = 'c21ed5f6-e6f5-4afb-9750-e7854480a1a5'
    AND agent_name = 'audit_trail'
    AND action = 'final_summary'
""")).fetchall()

for log in logs:
    print(f'Agent: {log[0]}')
    details = json.loads(str(log[1])) if log[1] else {}
    if 'errors' in details:
        print('Errors from other agents:')
        for err in details['errors']:
            print(f'  - {err[:300]}...')

session.close()
