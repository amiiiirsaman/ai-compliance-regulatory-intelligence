"""Check audit logs for specialist agents."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:Summerjoon202511!@localhost:5432/claims_saas_db')
Session = sessionmaker(bind=engine)
session = Session()

# Get audit logs for the specialists
logs = session.execute(text("""
    SELECT agent_name, action, status, error_message, details::text
    FROM audit_logs 
    WHERE review_id = 'c21ed5f6-e6f5-4afb-9750-e7854480a1a5'
    AND agent_name IN ('finra_specialist', 'sec_specialist', 'cfpb_specialist', 'aml_kyc_agent', 'data_privacy_agent')
    ORDER BY timestamp
""")).fetchall()

print('Specialist Agent Audit Logs:')
print('-' * 80)
for log in logs:
    err = log[3][:150] if log[3] else 'None'
    print(f'{log[0]} | {log[1]} | {log[2]}')
    if log[3]:
        print(f'  Error: {err}...')

session.close()
