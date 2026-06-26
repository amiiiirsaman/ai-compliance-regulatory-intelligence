"""Create the database if it doesn't exist."""
import asyncio
import asyncpg

async def create_database():
    # Connect to default postgres database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='Summerjoon202511!',
        database='postgres'
    )
    
    # Check if database exists
    result = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = 'claims_saas_db'"
    )
    
    if not result:
        # Create the database
        await conn.execute('CREATE DATABASE claims_saas_db')
        print('✅ Database claims_saas_db created successfully!')
    else:
        print('✅ Database claims_saas_db already exists')
    
    await conn.close()

if __name__ == '__main__':
    asyncio.run(create_database())
