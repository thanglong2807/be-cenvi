from app.db.repositories.employee_repo import EmployeeRepository

repo = EmployeeRepository()

def list_employees():
    return repo.get_all()

def get_employee(employee_id: int):
    return repo.get_by_id(employee_id)

def create_employee(data: dict):
    if repo.get_by_email(data["email"]):
        raise ValueError("Email nhân viên đã tồn tại")

    return repo.create(data)

def update_employee(employee_id: int, data: dict):
    employee = repo.get_by_id(employee_id)
    if not employee:
        raise ValueError("Nhân viên không tồn tại")

    return repo.update(employee_id, data)
