import asyncio
import certifi
import ssl
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    # Try with tlsAllowInvalidCertificates to distinguish cert issue vs IP whitelist issue
    c = AsyncIOMotorClient(
        'mongodb+srv://ash:123@idolcode.q1zez1a.mongodb.net/?appName=Idolcode',
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000
    )
    db = c['idolcode']
    try:
        colls = await db.list_collection_names()
        print('Connected successfully!')
        print('Collections:', colls)
    except Exception as e:
        print(f'Error: {e}')
        print()
        print('If you see TLSV1_ALERT_INTERNAL_ERROR:')
        print('  -> Your IP is NOT whitelisted in MongoDB Atlas.')
        print('  -> Go to https://cloud.mongodb.com -> Network Access -> Add IP Address')
        print('  -> Add 0.0.0.0/0 (Allow from Anywhere) for development')

asyncio.run(test())
