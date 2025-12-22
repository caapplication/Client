"""
Script to fix client_type values in the database
Converts display names to enum values
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment variables")
    sys.exit(1)

# Mapping from display names to enum values
MAPPING = {
    'Individual': 'individual',
    'Sole Proprietorship': 'sole_proprietorship',
    'Partnership': 'partnership',
    'LLP': 'llp',
    'HUF': 'huf',
    'Private Limited Company': 'private_limited',
    'Public Limited Company': 'limited_company',
    'Joint Venture': 'joint_venture',
    'One Person Company': 'one_person_company',
    'NGO\'s': 'ngo',
    'NGO': 'ngo',
    'Trust': 'trust',
    'Section 8 Company': 'section_8_company',
    'Government Entity': 'government_entity',
    'Cooperative Society': 'cooperative_society',
    'Branch Office': 'branch_office',
    'AOP': 'aop',
    'Society': 'society',
}

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all clients with invalid client_type values
        check_query = text("""
            SELECT id, client_type 
            FROM clients 
            WHERE client_type NOT IN (
                'individual', 'sole_proprietorship', 'partnership', 'llp', 'huf',
                'private_limited', 'limited_company', 'joint_venture', 'one_person_company',
                'ngo', 'trust', 'section_8_company', 'government_entity', 
                'cooperative_society', 'branch_office', 'aop', 'society'
            )
        """)
        result = conn.execute(check_query)
        invalid_clients = result.fetchall()
        
        if invalid_clients:
            print(f"Found {len(invalid_clients)} clients with invalid client_type values:")
            for client_id, client_type in invalid_clients:
                print(f"  Client {client_id}: '{client_type}'")
                if client_type in MAPPING:
                    new_value = MAPPING[client_type]
                    update_query = text("""
                        UPDATE clients 
                        SET client_type = :new_value 
                        WHERE id = :client_id
                    """)
                    conn.execute(update_query, {"new_value": new_value, "client_id": client_id})
                    print(f"    -> Updated to '{new_value}'")
                else:
                    print(f"    -> No mapping found, skipping")
            
            conn.commit()
            print(f"\nSuccessfully updated {len([c for c in invalid_clients if c[1] in MAPPING])} client records")
        else:
            print("No clients with invalid client_type values found")
    
    print("Database migration completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

