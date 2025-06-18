import configparser
import ctypes
import shutil
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime
from tkcalendar import Calendar
from PIL import Image, ImageTk
import uuid

if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("YourAppID.UniqueName")

def resource_path(relative_path):
    """ Get absolute path to resources for both dev and PyInstaller """

    try:
        base_path = sys._MEIPASS

    except Exception:
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Resource not found: {full_path}")
    return full_path

class FinanceTracker:

    def __init__(self, root):
        self.root = root
        self.root.title("Finance Tracker")
        self.root.geometry("700x770")
        self.root.resizable(True, True)

        try:
            root.iconbitmap(resource_path(r"icons/icon.ico"))

        except Exception as e:
            print("Icon load error:", e)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.data_dir = os.path.join(os.path.expanduser("~"), ".FinanceTracker")
        os.makedirs(self.data_dir, exist_ok=True)

        if sys.platform == "win32":

            try:
                ctypes.windll.kernel32.SetFileAttributesW(self.data_dir, 2)

            except:
                pass
        self.expense_file = os.path.join(self.data_dir, "expenses.json")
        self.income_file = os.path.join(self.data_dir, "income.json")
        self.config_file = os.path.join(self.data_dir, "config.ini")
        self.migrate_old_files()
        self.range_start_date = None
        self.range_end_date = None
        self.trans_type = tk.StringVar(value=self.load_last_transaction_type() or "Expense")
        self.expense_data = self.load_data(self.expense_file)
        self.income_data = self.load_data(self.income_file)
        self.add_ids_to_data()
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.undo_stack = []
        self.load_window_geometry()
        self.create_widgets()
        self.update_display()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind('<Delete>', self.delete_selected)
        self.root.bind("<Control-z>", self.undo_delete)

    def migrate_old_files(self):
        """Move existing files to hidden directory"""
        old_files = {
            "expenses.json": self.expense_file,
            "income.json": self.income_file,
            "config.ini": self.config_file
        }
        for old_name, new_path in old_files.items():

            if os.path.exists(old_name) and not os.path.exists(new_path):

                try:
                    shutil.move(old_name, new_path)

                except Exception as e:
                    print(f"Error migrating {old_name}: {e}")

    def load_window_geometry(self):

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)

            if "Geometry" in config:
                geometry = config["Geometry"].get("size", "")
                state = config["Geometry"].get("state", "normal")

                if geometry:
                    self.root.geometry(geometry)
                    self.root.update_idletasks()
                    self.root.update()

                if state == "zoomed":
                    self.root.state("zoomed")
                elif state == "iconic":
                    self.root.iconify()

    def load_last_transaction_type(self):
        """Load last used transaction type from config"""

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)

            if "MainWindow" in config:
                return config["MainWindow"].get("last_transaction_type")
        return None

    def save_window_geometry(self):
        """Save window geometry and last transaction type"""
        config = configparser.ConfigParser()
        config["Geometry"] = {
            "size": self.root.geometry(),
            "state": self.root.state()
        }
        config["MainWindow"] = {
            "last_transaction_type": self.trans_type.get()
        }

        with open(self.config_file, "w") as f:
            config.write(f)

    def on_close(self):
        """Handle window close event"""
        self.save_window_geometry()
        root.destroy()

    def add_ids_to_data(self):
        """Add unique IDs to transactions if missing"""
        for data in [self.expense_data, self.income_data]:
            for date, transactions in data.items():
                for trans in transactions:

                    if 'id' not in trans:
                        trans['id'] = str(uuid.uuid4())

    def configure_styles(self):
        """Configure premium-looking styles"""
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('Header.TLabel',
                            background='#4a6fa5',
                            foreground='white',
                            font=('Helvetica', 15, 'bold'),
                            padding=10)
        self.style.configure('Accent.TFrame', background='#e0e7ff')
        self.style.configure('TButton',
                            font=('Helvetica', 15),
                            padding=5)
        self.style.map('TButton',
                      foreground=[('pressed', 'white'), ('active', 'white')],
                      background=[('pressed', '#3a5998'), ('active', '#5b7cbc')])
        self.style.configure('Treeview',
                            font=('Helvetica', 11),
                            rowheight=25)
        self.style.configure('Treeview.Heading',
                            font=('Helvetica', 13, 'bold'))
        self.style.configure('Total.TLabel',
                            font=('Helvetica', 11, 'bold'),
                            background='#e0e7ff')
        self.style.configure('TCombobox', font=('Helvetica', 10))
        self.style.configure('TRadiobutton',
                            font=('Helvetica', 11),
                            background='#f0f0f0')
        self.style.configure('Profit.TLabel', foreground='green', font=('Helvetica', 11, 'bold'), background = '#f0f0f0')
        self.style.configure('Loss.TLabel', foreground='red', font=('Helvetica', 10, 'bold'), background = '#f0f0f0')
        self.style.configure('Calendar.TButton', padding=2)
        self.style.configure('Modern.TRadiobutton',
                            background='#dfd8d8',
                            font=('Helvetica', 11, 'bold'),
                            foreground='#2c3e50',
                            padding=5)
        self.style.map('Modern.TRadiobutton',
                      background=[('active', '#c0d0e0')],
                      foreground=[('active', '#1a2b3c')])

    def load_data(self, filename):
        """Load data from JSON file or create new if doesn't exist"""

        if os.path.exists(filename):

            try:

                with open(filename, 'r') as f:
                    return json.load(f)

            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def save_data(self, data, filename):
        """Save data to JSON file"""

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def create_widgets(self):
        """Create all GUI widgets"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        header_frame = ttk.Frame(main_container, style='Header.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="Finance Tracker", style='Header.TLabel').pack()
        content_frame = tk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        input_frame = tk.LabelFrame(content_frame, text="Add Transaction", font=('Helvetica', 15))
        input_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        type_frame = tk.Frame(input_frame, background='#dfd8d8')
        type_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        ttk.Label(type_frame, text="Type:", font=('Helvetica', 12),
                 background='#dfd8d8').pack(side=tk.LEFT, padx=(10, 5))
        income_rb = ttk.Radiobutton(
            type_frame,
            text="Income",
            variable=self.trans_type,
            value="Income",
            command=self.toggle_bonus,
            style='Modern.TRadiobutton'
        )
        income_rb.pack(side=tk.LEFT, padx=(5, 10))
        expense_rb = ttk.Radiobutton(
            type_frame,
            text="Expense",
            variable=self.trans_type,
            value="Expense",
            command=self.toggle_bonus,
            style='Modern.TRadiobutton'
        )
        expense_rb.pack(side=tk.LEFT, padx=(0, 10))
        entry_frame = tk.Frame(input_frame, background='#dfd8d8')
        entry_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(entry_frame, text="Amount (₹):", font=('Helvetica', 12), background='#dfd8d8').pack(side=tk.LEFT, padx=(0, 10))
        self.amount_entry = ttk.Entry(entry_frame, width=15, font=('Helvetica', 12))
        self.amount_entry.pack(side=tk.LEFT)
        category_frame = tk.Frame(input_frame, background='#dfd8d8')
        category_frame.pack(fill=tk.X, pady=5, padx=5)
        tk.Label(category_frame, text="Category:", font=('Helvetica', 12), background='#dfd8d8').pack(side=tk.LEFT, padx=(0, 10))
        self.category = ttk.Combobox(category_frame, width=15, state="readonly")
        self.category['values'] = (
            'Food', 'Transport', 'Shopping',
            'Entertainment', 'Bills', 'Salary',
            'Freelance', 'Investment', 'Other'
        )
        self.category.current(0)
        self.category.pack(side=tk.LEFT)
        self.bonus_frame = tk.Frame(entry_frame, background='#dfd8d8')
        ttk.Label(self.bonus_frame,font=('Helvetica',12), text="Bonus (₹):", background='#dfd8d8').pack(side=tk.LEFT, padx=(20, 10))
        self.bonus_entry = ttk.Entry(self.bonus_frame, width=15, font=('Helvetica', 12))
        self.bonus_entry.pack(side=tk.LEFT)
        button_frame = tk.Frame(input_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=10,padx=5)
        add_button = ttk.Button(button_frame,  text="Add Transaction", command=self.add_transaction)
        add_button.pack(pady=5, ipadx=20)
        totals_frame = ttk.Frame(content_frame, style='Accent.TFrame', padding=10)
        totals_frame.pack(fill=tk.X, pady=(0, 15))
        today_frame = tk.Frame(totals_frame, bg='#e0e7ff')
        today_frame.pack(fill=tk.X, pady=5)
        ttk.Label(today_frame, text="Total Income:", style='Total.TLabel',
                 width=13).pack(side=tk.LEFT, padx=(20, 0))
        self.today_income_label = ttk.Label(today_frame, text="₹0", style='Total.TLabel')
        self.today_income_label.pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(today_frame, text="Total Expenses:", style='Total.TLabel',
                 width=15).pack(side=tk.LEFT, padx=(10,0))
        self.today_expense_label = ttk.Label(today_frame, text="₹0", style='Total.TLabel')
        self.today_expense_label.pack(side=tk.LEFT, padx=10)
        ttk.Label(today_frame, text="Total Bonus:", style='Total.TLabel',
                 width=12).pack(side=tk.LEFT, padx=(10,0))
        self.today_bonus_label = ttk.Label(today_frame, text="₹0", style='Total.TLabel')
        self.today_bonus_label.pack(side=tk.LEFT, padx=0)
        history_frame = tk.LabelFrame(content_frame, font=('Helvetica', 15))
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        history_header = tk.Frame(history_frame)
        history_header.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(
            history_header,
            text="Transaction History",
            font=('Helvetica', 12, 'bold')
        ).pack(side=tk.LEFT)

        try:
            original_img = Image.open(resource_path(r"icons\calender.png"))
            resized_img = original_img.resize((25, 25), Image.LANCZOS)
            self.cal_img = ImageTk.PhotoImage(resized_img)
            self.cal_menu = tk.Menubutton(
                history_header,
                image=self.cal_img,
                font=('Helvetica', 12),
                relief=tk.RAISED
            )
            self.cal_menu.pack(side=tk.LEFT, padx=20)
            self.cal_dropdown = tk.Menu(self.cal_menu, tearoff=0)
            self.cal_menu.config(menu=self.cal_dropdown)
            self.cal_dropdown.add_command(
                label="Date wise Transaction History",
                command=self.select_single_date
            )
            self.cal_dropdown.add_command(
                label="Transaction History Between Two Dates",
                command=self.select_date_range
            )

        except:
            pass
        self.date_label = tk.Label(
            history_header,
            text=f"Date: {self.format_display_date(self.current_date)}",
            font=('Helvetica', 13),
            foreground='black'
        )
        self.date_label.pack(side=tk.RIGHT)
        columns = ('Time', 'Type', 'Category', 'Amount')
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show='headings',
            selectmode='extended'
        )
        self.history_tree.column('Time', width=100, anchor=tk.CENTER)
        self.history_tree.column('Type', width=80, anchor=tk.CENTER)
        self.history_tree.column('Category', width=120, anchor=tk.CENTER)
        self.history_tree.column('Amount', width=120, anchor=tk.CENTER)
        self.history_tree.heading('Time', text='Time')
        self.history_tree.heading('Type', text='Type')
        self.history_tree.heading('Category', text='Category')
        self.history_tree.heading('Amount', text='Amount (₹)')
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.history_tree.tag_configure('expense', foreground='red')
        self.history_tree.tag_configure('income', foreground='green')
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_command(label="Customize", command=self.customize_selected)
        self.history_tree.bind("<Button-3>", self.show_context_menu)
        balance_frame = ttk.Frame(content_frame, padding=(0, 10, 0, 0))
        balance_frame.pack(fill=tk.X)
        tk.Label(balance_frame, text="Remaining Balance:",bg='#f0f0f0', font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        self.daily_balance_label = ttk.Label(balance_frame, text="₹0.00", style='Profit.TLabel')
        self.daily_balance_label.pack(side=tk.LEFT, padx=(5, 0))
        self.toggle_bonus()

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.history_tree.identify_row(event.y)

        if item:
            self.context_menu.post(event.x_root, event.y_root)

    def delete_selected(self, event = None):
        """Delete selected transactions"""
        self.selected_items = self.history_tree.selection()

        if not self.selected_items:
            return
        transactions_to_delete = []
        for item in self.selected_items:
            tags = self.history_tree.item(item, 'tags')

            if len(tags) < 2:
                continue
            trans_id = tags[1]
            trans_type = 'Expense' if tags[0] == 'expense' else 'Income'
            trans_date = self.current_date

            if 'range_mode' in tags:
                trans_date = tags[2]
            transactions_to_delete.append({
                'id': trans_id,
                'type': trans_type,
                'date': trans_date
            })
        self.perform_deletion(transactions_to_delete)

    def perform_deletion(self, transactions):
        """Perform deletion and store in undo stack"""
        deleted_transactions = []
        for trans in transactions:
            trans_id = trans['id']
            trans_type = trans['type']
            trans_date = trans['date']

            if trans_type == "Expense" and trans_date in self.expense_data:
                for i, t in enumerate(self.expense_data[trans_date]):

                    if t.get('id') == trans_id:
                        deleted_trans = self.expense_data[trans_date].pop(i)
                        deleted_trans['date'] = trans_date
                        deleted_trans['source'] = 'expense'
                        deleted_trans['index'] = i
                        deleted_transactions.append(deleted_trans)
                        break
            elif trans_type == "Income" and trans_date in self.income_data:
                for i, t in enumerate(self.income_data[trans_date]):

                    if t.get('id') == trans_id:
                        deleted_trans = self.income_data[trans_date].pop(i)
                        deleted_trans['date'] = trans_date
                        deleted_trans['source'] = 'income'
                        deleted_trans['index'] = i
                        deleted_transactions.append(deleted_trans)
                        break

        if deleted_transactions:
            self.save_data(self.expense_data, self.expense_file)
            self.save_data(self.income_data, self.income_file)
            self.undo_stack.append(deleted_transactions)
            self.update_display()

    def undo_delete(self, event=None):

        if not self.undo_stack:
            return
        transactions = self.undo_stack.pop()
        for trans in transactions:
            trans_date = trans['date']
            source = trans.pop('source', 'expense')
            original_index = trans.pop('index', None)

            if source == 'expense':

                if trans_date not in self.expense_data:
                    self.expense_data[trans_date] = []

                if original_index is not None and original_index <= len(self.expense_data[trans_date]):
                    self.expense_data[trans_date].insert(original_index, trans)
                else:
                    self.expense_data[trans_date].append(trans)
            elif source == 'income':

                if trans_date not in self.income_data:
                    self.income_data[trans_date] = []

                if original_index is not None and original_index <= len(self.income_data[trans_date]):
                    self.income_data[trans_date].insert(original_index, trans)
                else:
                    self.income_data[trans_date].append(trans)
        self.save_data(self.expense_data, self.expense_file)
        self.save_data(self.income_data, self.income_file)
        self.update_display()

    def customize_selected(self):
        """Customize selected transaction"""
        selected_items = self.history_tree.selection()

        if not selected_items:
            return
        item = selected_items[0]
        values = self.history_tree.item(item, 'values')
        tags = self.history_tree.item(item, 'tags')

        if len(tags) < 2:
            return
        trans_id = tags[1]
        trans_date = self.current_date
        trans_type = 'Expense' if tags[0] == 'expense' else 'Income'

        if 'range_mode' in tags:
            trans_date = tags[2]
            trans_time = values[1]
        else:
            trans_time = values[0]
        transaction = None
        data_source = None

        if trans_type == "Expense" and trans_date in self.expense_data:
            for t in self.expense_data[trans_date]:

                if t.get('id') == trans_id:
                    transaction = t
                    data_source = self.expense_data
                    break
        elif trans_type == "Income" and trans_date in self.income_data:
            for t in self.income_data[trans_date]:

                if t.get('id') == trans_id:
                    transaction = t
                    data_source = self.income_data
                    break

        if not transaction:
            return
        self.open_customization_window(transaction, data_source, trans_date)

    def open_customization_window(self, transaction, data_source, date):
        """Open window to customize transaction"""
        top = tk.Toplevel(self.root, background='#7e7e
