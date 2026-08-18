# test_duplicate_company.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import session_local
from app.models.companies import Company
from app.schemas.company import CompanyCreate
from app.services import company_service

def run_test():
    db = session_local()
    name = "Duplicate Test Company"
    
    # Reset
    db.query(Company).filter(Company.name == name).delete()
    db.commit()
    
    try:
        # Create first entry
        c1 = company_service.create_company(db, CompanyCreate(name=name))
        print(f"Entry 1 created (ID: {c1.id})")
        
        # Try creating duplicate
        c2 = company_service.create_company(db, CompanyCreate(name=name))
        print(f"Entry 2 created (ID: {c2.id}) - Duplicates allowed.")
    except Exception as e:
        print(f"Insertion blocked: {e} - Duplicates prevented.")
        db.rollback()
    finally:
        db.query(Company).filter(Company.name == name).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_test()
