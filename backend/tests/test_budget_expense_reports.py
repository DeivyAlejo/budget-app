import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.main import app


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "testpassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Budget User"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_budget_expense_and_reports_flow() -> None:
    with TestClient(app) as client:
        headers = _auth_headers(client)

        categories = client.get("/api/v1/categories", headers=headers)
        assert categories.status_code == 200
        category_id = categories.json()[0]["id"]

        methods = client.get("/api/v1/payment-methods", headers=headers)
        assert methods.status_code == 200
        payment_method_id = methods.json()[0]["id"]

        custom_category = client.post("/api/v1/categories", headers=headers, json={"name": "Pet Care"})
        assert custom_category.status_code == 201
        custom_category_id = custom_category.json()["id"]

        custom_method = client.post("/api/v1/payment-methods", headers=headers, json={"name": "Mobile Wallet"})
        assert custom_method.status_code == 201
        custom_method_id = custom_method.json()["id"]

        update_category = client.put(f"/api/v1/categories/{custom_category_id}", headers=headers, json={"name": "Pets"})
        assert update_category.status_code == 200
        assert update_category.json()["name"] == "Pets"

        update_method = client.put(f"/api/v1/payment-methods/{custom_method_id}", headers=headers, json={"name": "Wallet"})
        assert update_method.status_code == 200
        assert update_method.json()["name"] == "Wallet"

        budget = client.post(
            "/api/v1/budgets",
            headers=headers,
            json={"year": 2026, "month": 3, "planned_amount": "1000.00", "copy_previous_month": False},
        )
        assert budget.status_code == 201
        budget_id = budget.json()["id"]

        budget_update = client.put(f"/api/v1/budgets/{budget_id}", headers=headers, json={"planned_amount": "1200.00"})
        assert budget_update.status_code == 200
        assert budget_update.json()["planned_amount"] == "1200.00"

        expense = client.post(
            "/api/v1/expenses",
            headers=headers,
            json={
                "category_id": category_id,
                "payment_method_id": payment_method_id,
                "description": "Groceries",
                "amount": "75.50",
                "spent_at": date(2026, 3, 10).isoformat(),
            },
        )
        assert expense.status_code == 201
        expense_id = expense.json()["id"]

        expense_update = client.put(
            f"/api/v1/expenses/{expense_id}",
            headers=headers,
            json={
                "category_id": custom_category_id,
                "payment_method_id": custom_method_id,
                "description": "Vet visit",
                "amount": "95.00",
                "spent_at": date(2026, 3, 12).isoformat(),
            },
        )
        assert expense_update.status_code == 200
        assert expense_update.json()["description"] == "Vet visit"

        month_totals = client.get("/api/v1/reports/categories/totals?year=2026&month=3", headers=headers)
        assert month_totals.status_code == 200
        assert len(month_totals.json()) >= 1

        detail = client.get(f"/api/v1/reports/categories/{custom_category_id}?year=2026&month=3", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["category_id"] == custom_category_id

        delete_expense = client.delete(f"/api/v1/expenses/{expense_id}", headers=headers)
        assert delete_expense.status_code == 204

        delete_budget = client.delete(f"/api/v1/budgets/{budget_id}", headers=headers)
        assert delete_budget.status_code == 204

        delete_method = client.delete(f"/api/v1/payment-methods/{custom_method_id}", headers=headers)
        assert delete_method.status_code == 204

        delete_category = client.delete(f"/api/v1/categories/{custom_category_id}", headers=headers)
        assert delete_category.status_code == 204
