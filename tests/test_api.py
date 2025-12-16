def test_add_service(client):
    resp = client.post(
        "/services",
        json={
            "name": "new-service",
            "IP": "8.8.8.8",
            "frequency_seconds": 30,
            "alerting_window_seconds": 300,
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "service added"

def test_debug_db(client, test_db): 
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row 
    
    with conn:
        cur = conn.execute("SELECT rowid, * FROM services")
        rows = [dict(row) for row in cur.fetchall()]
        print("Current services in DB (via direct access):", rows)

        cur = conn.execute("SELECT rowid, * FROM service_admins")
        rows = [dict(row) for row in cur.fetchall()]
        print("Current admins in DB (via direct access):", rows)
        

def test_delete_service(client, test_db):
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row 
    
    with conn:
        cur = conn.execute("SELECT rowid, * FROM services")
        rows = [dict(row) for row in cur.fetchall()]
        print("Current services in DB (via direct access):", rows)

        cur = conn.execute("SELECT rowid, * FROM service_admins")
        rows = [dict(row) for row in cur.fetchall()]
        print("Current admins in DB (via direct access):", rows)
    resp = client.delete("/services/2")
    assert resp.status_code == 200
    assert resp.json()["status"] == "service deleted"

def test_change_service_admin(client):
    resp = client.put(
        "/services/0/admin",
        json={
            "admin_id": 1,
            "role": "primary",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "service admin updated"

def test_update_admin_contact(client):
    resp = client.patch(
        "/admins/1",
        json={
            "contact_value": "alice_new@test.com",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "admin contact updated"

def test_update_missing_admin(client):
    resp = client.patch(
        "/admins/999",
        json={"contact_value": "x@test.com"},
    )

    assert resp.status_code == 404
