from app.db.repositories.company_repo import CompanyRepository

repo = CompanyRepository()

def get_companies():
    return repo.get_all()

def get_company_detail(code: str):
    return repo.get_by_code(code)

def create_company(data: dict):
    if repo.get_by_code(data["code"]):
        raise ValueError("Company already exists")
    return repo.create(data)
