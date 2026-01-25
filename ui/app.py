import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'dev_secret_key'  # Change for production


@app.template_filter('datetimeformat')
def datetimeformat(value):
    if not value:
        return "-"
    
    if isinstance(value, str):
        try:
            # Handle the ISO string from your API
            value = datetime.fromisoformat(value.replace('Z', ''))
        except ValueError:
            return value
            
    # %d=Day, %b=Short Month, %Y=Year, %H:%M:%S=Time
    return value.strftime('%d %b %Y %H:%M:%S')


# Configuration
API_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# --- Helper Functions ---
def get_headers():
    return {"Content-Type": "application/json"}

def fetch_all_admins():
    """Fetch list of admins for login and dropdowns."""
    try:
        resp = requests.get(f"{API_URL}/admins/")
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

# --- Authentication Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    
    admin = requests.get(f"{API_URL}/admins/contact/{email}")
    user = admin.json() if admin.status_code == 200 else None

    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['contact_value']
        return redirect(url_for('dashboard'))
    
    flash('Email not found. Please register.', 'danger')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1. Grab data from the form
        name = request.form.get('name')
        email = request.form.get('email')
        
        payload = {
            "name": name,
            "contact_type": "email",
            "contact_value": email
        }
        
        try:
            resp = requests.post(f"{API_URL}/admins/", json=payload)
            print(resp.text)
            
            if resp.status_code == 200:
                user_data = resp.json()
                print(user_data)
                # 3. Log them in automatically
                session['user_id'] = user_data['id']
                session['user_name'] = user_data['name']
                session['user_email'] = user_data['contact_value']
                flash("Registration successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                # This helps you see why the API rejected the request
                error_detail = resp.json().get('detail', 'Unknown error')
                flash(f"Registration failed: {error_detail}", "danger")
                
        except Exception as e:
            flash(f"Connection error: {str(e)}", "danger")
            
    return render_template('login.html') # Redirect back to main page on GET

# --- Core Functionality ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    services = []
    
    try:
        user_id = session['user_id']
        resp = requests.get(f"{API_URL}/admins/{user_id}/services")
        
        if resp.status_code == 200:
            services = resp.json()
            
            for svc in services:

                resp_admins = requests.get(f"{API_URL}/services/{svc['id']}/admins", headers=get_headers())
                if resp_admins.status_code == 200:
                    svc.update(resp_admins.json())
                else:
                    svc.update({"primary": None, "secondary": None})
                inc_resp = requests.get(f"{API_URL}/services/{svc['id']}/incidents")
                if inc_resp.status_code == 200:
                    svc['incidents'] = inc_resp.json()
                else:
                    svc['incidents'] = []

    except requests.exceptions.RequestException:
        flash("Could not connect to backend to fetch data.", "warning")

    return render_template('dashboard.html', services=services)


@app.route('/service/add', methods=['GET', 'POST'])
def add_service():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # 1. Create Service
        svc_payload = {
            "name": request.form.get('name'),
            "IP": request.form.get('ip'),
            "frequency_seconds": int(request.form.get('frequency')),
            "alerting_window_npings": int(request.form.get('window')),
            "failure_threshold": int(request.form.get('threshold'))  # new field
        }

        resp = requests.post(f"{API_URL}/services", json=svc_payload, headers=get_headers())

        if resp.status_code in [200, 201]:
            data = resp.json()
            service_id = data.get('service_id')

            # 2. Assign Current User as PRIMARY Admin
            primary_admin_payload = {
                "service_id": service_id,
                "role": "primary",
                "admin_id": session['user_id']  # Using the updated endpoint
            }
            resp_primary = requests.post(
                f"{API_URL}/services/{service_id}/admin",
                json=primary_admin_payload,
                headers=get_headers()
            )
            if resp_primary.status_code not in [200, 201]:
                flash(f"Error assigning primary admin: {resp_primary.text}", "danger")
                return redirect(url_for('add_service'))

            # 3. Assign Selected User as SECONDARY Admin (if selected)
            sec_admin_id = request.form.get('secondary_admin')
            if sec_admin_id:
                secondary_admin_payload = {
                    "service_id": service_id,
                    "role": "secondary",
                    "admin_id": int(sec_admin_id)
                }
                resp_secondary = requests.post(
                    f"{API_URL}/services/{service_id}/admin",
                    json=secondary_admin_payload,
                    headers=get_headers()
                )
                if resp_secondary.status_code not in [200, 201]:
                    flash(f"Error assigning secondary admin: {resp_secondary.text}", "danger")
                    return redirect(url_for('add_service'))

            flash("Service created and admins assigned.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash(f"Error creating service: {resp.text}", "danger")

    all_admins = fetch_all_admins()
    other_admins = [a for a in all_admins if a['id'] != session['user_id']]

    return render_template('add_service.html', admins=other_admins)


@app.route('/service/<int:service_id>/edit', methods=['GET', 'POST'])
def edit_service(service_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # 1. Fetch service details from API
    resp_service = requests.get(f"{API_URL}/services/{service_id}", headers=get_headers())
    if resp_service.status_code != 200:
        flash(f"Service not found: {resp_service.text}", "danger")
        return redirect(url_for('dashboard'))
    service = resp_service.json()

    # 2. Fetch current admins for the service
    resp_admins = requests.get(f"{API_URL}/services/{service_id}/admins", headers=get_headers())
    if resp_admins.status_code != 200:
        flash(f"Failed to fetch service admins: {resp_admins.text}", "danger")
        return redirect(url_for('dashboard'))
    
    current_admins = resp_admins.json()

    # 3. Fetch all other admins for dropdown (exclude current user)
    all_admins = fetch_all_admins()

    if request.method == 'POST':
        # 4. Update service fields
        svc_payload = {
            "frequency_seconds": int(request.form.get('frequency_seconds')),
            "alerting_window_npings": int(request.form.get('alerting_window_npings')),
            "failure_threshold": int(request.form.get('failure_threshold'))
        }
        resp_update_service = requests.put(
            f"{API_URL}/services/{service_id}",
            json=svc_payload,
            headers=get_headers()
        )
        if resp_update_service.status_code not in [200, 201]:
            flash(f"Failed to update service: {resp_update_service.text}", "danger")
            return redirect(url_for('edit_service', service_id=service_id))

        # 5. Update admins
        primary_admin_id = request.form.get('primary')
        secondary_admin_id = request.form.get('secondary')

        if primary_admin_id and (current_admins.get('primary')['id'] != int(primary_admin_id)):
            payload = {
                "role": "primary",
                "new_admin_id": int(primary_admin_id)
            }
            resp_admin = requests.put(f"{API_URL}/services/{service_id}/admin", json=payload, headers=get_headers())
            if resp_admin.status_code not in [200, 201]:
                flash(f"Failed to update primary admin: {resp_admin.text}", "danger")
                return redirect(url_for('edit_service', service_id=service_id))

        if secondary_admin_id and current_admins.get('secondary')['id'] != int(secondary_admin_id):
            payload = {
                "role": "secondary",
                "new_admin_id": int(secondary_admin_id)
            }

            resp_admin = requests.put(f"{API_URL}/services/{service_id}/admin", json=payload, headers=get_headers())
            if resp_admin.status_code not in [200, 201]:
                flash(f"Failed to update secondary admin: {resp_admin.text}", "danger")
                return redirect(url_for('edit_service', service_id=service_id))
            

        flash("Service and admins updated successfully.", "success")
        return redirect(url_for('dashboard'))

    # 6. GET request: render edit form
    return render_template(
        'edit_service.html',
        service=service,
        current_admins=current_admins,
        admins=all_admins
    )



@app.route('/service/delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        # Call your FastAPI DELETE endpoint
        resp = requests.delete(f"{API_URL}/services/{service_id}")
        
        if resp.status_code == 200:
            flash("Service successfully deleted.", "success")
        elif resp.status_code == 404:
            flash("Service not found.", "warning")
        else:
            flash(f"Failed to delete service: {resp.text}", "danger")
            
    except requests.exceptions.RequestException as e:
        flash(f"Connection error: {str(e)}", "danger")
        
    return redirect(url_for('dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # Update Contact Method
        new_email = request.form.get('email')
        resp = requests.patch(
            f"{API_URL}/admins/{session['user_id']}",
            json={"contact_value": new_email, "contact_type": "email"},
            headers=get_headers()
        )
        if resp.status_code == 200:
            session['user_email'] = new_email
            flash("Contact info updated.", "success")
        else:
            flash("Update failed.", "danger")
            
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)