from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.config import Config
import sqlite3
from datetime import datetime
import shutil
import csv

Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

def init_db():
    conn = sqlite3.connect('assets.db')
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        );
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            quantity INTEGER,
            value REAL,
            status TEXT DEFAULT 'Available',
            notes TEXT,
            last_updated TEXT
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            position TEXT,
            department TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY,
            asset_id INTEGER,
            employee_id INTEGER,
            assigned_date TEXT,
            notes TEXT
        );
    ''')
    conn.commit()
    conn.close()

init_db()

class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()
        if not username or not password:
            print("Please enter username and password")
            return
        conn = sqlite3.connect('assets.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        if c.fetchone():
            self.manager.current = 'dashboard'
        else:
            print("Invalid username or password")
        conn.close()

    def go_to_register(self):
        self.manager.current = 'register'

class RegisterScreen(Screen):
    def register(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()
        if not username or not password:
            print("Please fill all fields")
            return
        try:
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            print("Account created!")
            self.manager.current = 'login'
        except sqlite3.IntegrityError:
            print("Username already exists")

    def go_to_login(self):
        self.manager.current = 'login'

class DashboardScreen(Screen):
    def on_enter(self):
        self.update_stats()

    def update_stats(self):
        conn = sqlite3.connect('assets.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM assets")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM assets WHERE status='Assigned'")
        assigned = c.fetchone()[0]
        c.execute("SELECT SUM(value * quantity) FROM assets")
        value = c.fetchone()[0] or 0
        conn.close()
        self.ids.stats.text = f"Total Assets: {total}\nAssigned: {assigned}\nTotal Value: KSh {value:,.2f}"

    def toggle_theme(self):
        App.get_running_app().toggle_theme()

    def backup(self):
        try:
            path = '/storage/emulated/0/Download/assets_backup.db'
            shutil.copy('assets.db', path)
            print("Backup saved to Downloads!")
        except Exception as e:
            print("Backup failed:", e)

    def export_csv(self):
        try:
            path = '/storage/emulated/0/Download/assets_export.csv'
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Category', 'Quantity', 'Value', 'Status', 'Notes'])
                conn = sqlite3.connect('assets.db')
                c = conn.cursor()
                c.execute("SELECT id, name, category, quantity, value, status, notes FROM assets")
                writer.writerows(c.fetchall())
                conn.close()
            print("CSV exported to Downloads!")
        except Exception as e:
            print("Export failed:", e)

class AssetsScreen(Screen):
    def on_enter(self):
        self.load_assets()

    def load_assets(self, search='', category='All Categories'):
        self.ids.asset_list.clear_widgets()
        conn = sqlite3.connect('assets.db')
        c = conn.cursor()

        if category == 'All Categories':
            c.execute("SELECT * FROM assets WHERE name LIKE ? OR category LIKE ?", 
                      (f'%{search}%', f'%{search}%'))
        else:
            c.execute("SELECT * FROM assets WHERE (name LIKE ? OR category LIKE ?) AND category = ?", 
                      (f'%{search}%', f'%{search}%', category))

        for asset in c.fetchall():
            row = BoxLayout(size_hint_y=None, height=55, spacing=4)
            row.add_widget(Label(text=str(asset[0]), size_hint_x=0.08))
            row.add_widget(Label(text=asset[1], size_hint_x=0.28))
            row.add_widget(Label(text=asset[2] or '-', size_hint_x=0.18))
            row.add_widget(Label(text=str(asset[3]), size_hint_x=0.1))
            row.add_widget(Label(text=f"{asset[4]:.0f}", size_hint_x=0.12))
            row.add_widget(Label(text=asset[5], size_hint_x=0.12))

            edit_btn = Button(text='E', size_hint_x=0.06, background_color=(0.2, 0.5, 0.9, 1))
            edit_btn.bind(on_press=lambda x, a=asset: self.edit_asset(a))
            row.add_widget(edit_btn)

            del_btn = Button(text='D', size_hint_x=0.06, background_color=(0.9, 0.2, 0.2, 1))
            del_btn.bind(on_press=lambda x, aid=asset[0]: self.delete_asset(aid))
            row.add_widget(del_btn)

            self.ids.asset_list.add_widget(row)
        conn.close()

    def filter_assets(self):
        search = self.ids.search.text
        category = self.ids.category_spinner.text
        self.load_assets(search, category)

    def add_asset(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        name_input = TextInput(hint_text='Asset Name', multiline=False)
        category = Spinner(text='Electronics', values=('Electronics', 'Furniture', 'Vehicle', 'Other'))
        quantity = TextInput(hint_text='Quantity', text='1', multiline=False, input_filter='int')
        value = TextInput(hint_text='Value (KSh)', text='0', multiline=False, input_filter='float')
        notes = TextInput(hint_text='Notes (optional)', multiline=False)

        content.add_widget(name_input)
        content.add_widget(category)
        content.add_widget(quantity)
        content.add_widget(value)
        content.add_widget(notes)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        save_btn = Button(text='Save Asset', background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text='Cancel')

        def save(instance):
            if not name_input.text.strip():
                print("Name is required")
                return
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("""INSERT INTO assets (name, category, quantity, value, status, notes, last_updated) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (name_input.text.strip(), category.text, int(quantity.text or 1),
                       float(value.text or 0), 'Available', notes.text.strip(),
                       datetime.now().isoformat()))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_assets()
            print("Asset added!")

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Add New Asset', content=content, size_hint=(0.9, 0.7))
        popup.open()

    def edit_asset(self, asset):
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        name_input = TextInput(text=asset[1], multiline=False)
        category = Spinner(text=asset[2] or 'Electronics', values=('Electronics', 'Furniture', 'Vehicle', 'Other'))
        quantity = TextInput(text=str(asset[3]), multiline=False, input_filter='int')
        value = TextInput(text=str(asset[4]), multiline=False, input_filter='float')
        notes = TextInput(text=asset[6] or '', multiline=False)

        content.add_widget(name_input)
        content.add_widget(category)
        content.add_widget(quantity)
        content.add_widget(value)
        content.add_widget(notes)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        save_btn = Button(text='Update', background_color=(0.2, 0.5, 0.9, 1))
        cancel_btn = Button(text='Cancel')

        def save(instance):
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("""UPDATE assets SET name=?, category=?, quantity=?, value=?, notes=?, last_updated=? WHERE id=?""",
                      (name_input.text.strip(), category.text, int(quantity.text or 1),
                       float(value.text or 0), notes.text.strip(), datetime.now().isoformat(), asset[0]))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_assets()
            print("Asset updated!")

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Edit Asset', content=content, size_hint=(0.9, 0.7))
        popup.open()

    def delete_asset(self, asset_id):
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        content.add_widget(Label(text='Are you sure you want to delete this asset?'))
        btn_layout = BoxLayout(spacing=10, size_hint_y=0.4)
        yes_btn = Button(text='Yes, Delete', background_color=(0.9, 0.2, 0.2, 1))
        no_btn = Button(text='Cancel')

        def confirm(instance):
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("DELETE FROM assets WHERE id=?", (asset_id,))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_assets()
            print("Asset deleted")

        yes_btn.bind(on_press=confirm)
        no_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Confirm Delete', content=content, size_hint=(0.8, 0.4))
        popup.open()

class EmployeesScreen(Screen):
    def on_enter(self):
        self.load_employees()

    def load_employees(self):
        self.ids.employee_list.clear_widgets()
        conn = sqlite3.connect('assets.db')
        c = conn.cursor()
        c.execute("SELECT * FROM employees")
        for emp in c.fetchall():
            row = BoxLayout(size_hint_y=None, height=55, spacing=5)
            row.add_widget(Label(text=str(emp[0]), size_hint_x=0.1))
            row.add_widget(Label(text=emp[1], size_hint_x=0.3))
            row.add_widget(Label(text=emp[2] or '-', size_hint_x=0.25))
            row.add_widget(Label(text=emp[3] or '-', size_hint_x=0.2))

            del_btn = Button(text='Del', size_hint_x=0.15, background_color=(0.9, 0.2, 0.2, 1))
            del_btn.bind(on_press=lambda x, eid=emp[0]: self.delete_employee(eid))
            row.add_widget(del_btn)

            self.ids.employee_list.add_widget(row)
        conn.close()

    def add_employee(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        name = TextInput(hint_text='Full Name', multiline=False)
        position = TextInput(hint_text='Position', multiline=False)
        department = TextInput(hint_text='Department', multiline=False)
        email = TextInput(hint_text='Email', multiline=False)

        content.add_widget(name)
        content.add_widget(position)
        content.add_widget(department)
        content.add_widget(email)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        save_btn = Button(text='Save Employee', background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text='Cancel')

        def save(instance):
            if not name.text.strip():
                print("Name is required")
                return
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("INSERT INTO employees (name, position, department, email) VALUES (?, ?, ?, ?)",
                      (name.text.strip(), position.text.strip(), department.text.strip(), email.text.strip()))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_employees()
            print("Employee added!")

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Add New Employee', content=content, size_hint=(0.9, 0.65))
        popup.open()

    def delete_employee(self, emp_id):
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        content.add_widget(Label(text='Delete this employee?'))
        btn_layout = BoxLayout(spacing=10, size_hint_y=0.4)
        yes_btn = Button(text='Yes, Delete', background_color=(0.9, 0.2, 0.2, 1))
        no_btn = Button(text='Cancel')

        def confirm(instance):
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("DELETE FROM employees WHERE id=?", (emp_id,))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_employees()
            print("Employee deleted")

        yes_btn.bind(on_press=confirm)
        no_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Confirm Delete', content=content, size_hint=(0.8, 0.4))
        popup.open()

class AssignmentsScreen(Screen):
    def on_enter(self):
        self.load_assignments()

    def load_assignments(self):
        self.ids.assignment_list.clear_widgets()
        conn = sqlite3.connect('assets.db')
        c = conn.cursor()
        c.execute("SELECT * FROM assignments")
        for a in c.fetchall():
            row = BoxLayout(size_hint_y=None, height=55, spacing=5)
            row.add_widget(Label(text=str(a[0]), size_hint_x=0.15))
            row.add_widget(Label(text=f"Asset {a[1]}", size_hint_x=0.25))
            row.add_widget(Label(text=f"Emp {a[2]}", size_hint_x=0.25))
            row.add_widget(Label(text=a[3][:10] if a[3] else '-', size_hint_x=0.2))

            del_btn = Button(text='Del', size_hint_x=0.15, background_color=(0.9, 0.2, 0.2, 1))
            del_btn.bind(on_press=lambda x, aid=a[0]: self.delete_assignment(aid))
            row.add_widget(del_btn)

            self.ids.assignment_list.add_widget(row)
        conn.close()

    def add_assignment(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)

        conn = sqlite3.connect('assets.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM assets WHERE status='Available'")
        assets = c.fetchall()
        c.execute("SELECT id, name FROM employees")
        employees = c.fetchall()
        conn.close()

        asset_spinner = Spinner(text='Select Asset', values=[f"{a[0]} - {a[1]}" for a in assets] or ['No available assets'])
        employee_spinner = Spinner(text='Select Employee', values=[f"{e[0]} - {e[1]}" for e in employees] or ['No employees'])
        notes = TextInput(hint_text='Notes (optional)', multiline=False)

        content.add_widget(asset_spinner)
        content.add_widget(employee_spinner)
        content.add_widget(notes)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        save_btn = Button(text='Assign', background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text='Cancel')

        def save(instance):
            if 'No available' in asset_spinner.text or 'No employees' in employee_spinner.text:
                print("Cannot assign")
                return
            asset_id = int(asset_spinner.text.split(' - ')[0])
            employee_id = int(employee_spinner.text.split(' - ')[0])

            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("INSERT INTO assignments (asset_id, employee_id, assigned_date, notes) VALUES (?, ?, ?, ?)",
                      (asset_id, employee_id, datetime.now().isoformat(), notes.text.strip()))
            c.execute("UPDATE assets SET status='Assigned' WHERE id=?", (asset_id,))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_assignments()
            print("Asset assigned!")

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='New Assignment', content=content, size_hint=(0.9, 0.6))
        popup.open()

    def delete_assignment(self, assignment_id):
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        content.add_widget(Label(text='Delete this assignment?'))
        btn_layout = BoxLayout(spacing=10, size_hint_y=0.4)
        yes_btn = Button(text='Yes, Delete', background_color=(0.9, 0.2, 0.2, 1))
        no_btn = Button(text='Cancel')

        def confirm(instance):
            conn = sqlite3.connect('assets.db')
            c = conn.cursor()
            c.execute("SELECT asset_id FROM assignments WHERE id=?", (assignment_id,))
            asset_id = c.fetchone()[0]
            c.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
            c.execute("UPDATE assets SET status='Available' WHERE id=?", (asset_id,))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.load_assignments()
            print("Assignment deleted")

        yes_btn.bind(on_press=confirm)
        no_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='Confirm Delete', content=content, size_hint=(0.8, 0.4))
        popup.open()

class AssetTrackerApp(App):
    def build(self):
        self.theme_mode = 'light'
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(AssetsScreen(name='assets'))
        sm.add_widget(EmployeesScreen(name='employees'))
        sm.add_widget(AssignmentsScreen(name='assignments'))
        return sm

    def toggle_theme(self):
        if self.theme_mode == 'light':
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
            self.theme_mode = 'dark'
        else:
            Window.clearcolor = (1, 1, 1, 1)
            self.theme_mode = 'light'

if __name__ == '__main__':
    AssetTrackerApp().run()