from sqlalchemy.orm import Session
from models.companies import Company
from schemas.company import CompanyCreate, CompanyUpdate


def create_company(db: Session, data: CompanyCreate):
    data_dict = data.model_dump()

    if data_dict.get("website"):
        data_dict["website"] = str(data_dict["website"])

    company = Company(**data_dict)

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


def get_all(db: Session):
    return db.query(Company).all()


def get_one(db: Session, company_id: int):
    return db.query(Company).filter(Company.id == company_id).first()


def update_company(db: Session, company_id: int, data: CompanyUpdate):
    company = get_one(db, company_id)
    if not company:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "website" and value is not None:
            value = str(value)
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company_id: int):
    company = get_one(db, company_id)
    if not company:
        return False

    db.delete(company)
    db.commit()
    return True