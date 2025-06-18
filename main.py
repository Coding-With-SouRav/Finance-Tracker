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

        # Apply modern theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        self.data_dir = os.path.join(os.path.expanduser("~"), ".FinanceTracker")
        # print(f"Data files stored in: {self.data_dir}")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set hidden attribute (Windows only)
        if sys.platform == "win32":
            try:
                ctypes.windll.kernel32.SetFileAttributesW(self.data_dir, 2)
            except:
                pass
        
        # Initialize data files in hidden directory
        self.expense_file = os.path.join(self.data_dir, "expenses.json")
        self.income_file = os.path.join(self.data_dir, "income.json")
        self.config_file = os.path.join(self.data_dir, "config.ini")
        
        # Migrate existing files
        self.migrate_old_files()

        self.range_start_date = None
        self.range_end_date = None

        self.trans_type = tk.StringVar(value=self.load_last_transaction_type() or "Expense")
        self.expense_data = self.load_data(self.expense_file)
        self.income_data = self.load_data(self.income_file)

        # Add unique IDs to existing transactions
        self.add_ids_to_data()
        
        # Current date
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Undo stack
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
                    self.root.state("zoomed")  # Restore maximized state
                elif state == "iconic":
                    self.root.iconify()  # Restore minimized state
    
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
        
        # Geometry section
        config["Geometry"] = {
            "size": self.root.geometry(),
            "state": self.root.state()
        }
        
        # MainWindow section for app state
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
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_container, style='Header.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="Finance Tracker", style='Header.TLabel').pack()
        
        # Content frame
        content_frame = tk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Inputs
        input_frame = tk.LabelFrame(content_frame, text="Add Transaction", font=('Helvetica', 15))
        input_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Transaction type selection
        # type_frame = ttk.Frame(input_frame, style='Modern.TFrame')
        type_frame = tk.Frame(input_frame, background='#dfd8d8')
        type_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
         
        # ttk.Label(type_frame, text="Type:",font=('Helvetica', 12), background="#dfd8d8").pack(side=tk.LEFT, padx=(0, 10))
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

        # Amount entry
        entry_frame = tk.Frame(input_frame, background='#dfd8d8')
        entry_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(entry_frame, text="Amount (₹):", font=('Helvetica', 12), background='#dfd8d8').pack(side=tk.LEFT, padx=(0, 10))
        self.amount_entry = ttk.Entry(entry_frame, width=15, font=('Helvetica', 12))
        self.amount_entry.pack(side=tk.LEFT)
        
        # Category selection
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
        
        # Bonus entry (only for income
        self.bonus_frame = tk.Frame(entry_frame, background='#dfd8d8')
        ttk.Label(self.bonus_frame,font=('Helvetica',12), text="Bonus (₹):", background='#dfd8d8').pack(side=tk.LEFT, padx=(20, 10))
        self.bonus_entry = ttk.Entry(self.bonus_frame, width=15, font=('Helvetica', 12))
        self.bonus_entry.pack(side=tk.LEFT)
        
        # Add button
        button_frame = tk.Frame(input_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=10,padx=5)
        
        add_button = ttk.Button(button_frame,  text="Add Transaction", command=self.add_transaction)
        add_button.pack(pady=5, ipadx=20)
        
        # Totals frame (only today's totals remain)
        totals_frame = ttk.Frame(content_frame, style='Accent.TFrame', padding=10)
        totals_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Today's totals
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
        
        # Create header for history frame
        history_header = tk.Frame(history_frame)
        history_header.pack(fill=tk.X, padx=10, pady=5)
        
        # Add title to header
        tk.Label(
            history_header, 
            text="Transaction History", 
            font=('Helvetica', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        
        # Load and resize image
        try:
            original_img = Image.open(resource_path(r"icons\calender.png"))
            resized_img = original_img.resize((25, 25), Image.LANCZOS)  # Resize to 20x20
            self.cal_img = ImageTk.PhotoImage(resized_img)
            
            # Calendar dropdown menu
            self.cal_menu = tk.Menubutton(
                history_header, 
                image=self.cal_img,
                font=('Helvetica', 12),
                relief=tk.RAISED
            )
            self.cal_menu.pack(side=tk.LEFT, padx=20)
            
            # Create dropdown menu
            self.cal_dropdown = tk.Menu(self.cal_menu, tearoff=0)
            self.cal_menu.config(menu=self.cal_dropdown)
            
            # Add menu items
            self.cal_dropdown.add_command(
                label="Date wise Transaction History",
                # font=2,
                command=self.select_single_date
            )
            self.cal_dropdown.add_command(
                label="Transaction History Between Two Dates",
                # font=2,
                command=self.select_date_range
            )
        except:
            pass
        
        # Date label on the right
        self.date_label = tk.Label(
            history_header, 
            text=f"Date: {self.format_display_date(self.current_date)}",
            font=('Helvetica', 13),
            foreground='black'
        )
        self.date_label.pack(side=tk.RIGHT)

        # Treeview for history
        columns = ('Time', 'Type', 'Category', 'Amount')
        self.history_tree = ttk.Treeview(
            history_frame, 
            columns=columns, 
            show='headings',
            selectmode='extended'
        )
        
        # Configure columns
        self.history_tree.column('Time', width=100, anchor=tk.CENTER)
        self.history_tree.column('Type', width=80, anchor=tk.CENTER)
        self.history_tree.column('Category', width=120, anchor=tk.CENTER)
        self.history_tree.column('Amount', width=120, anchor=tk.CENTER)
        
        # Create headings
        self.history_tree.heading('Time', text='Time')
        self.history_tree.heading('Type', text='Type')
        self.history_tree.heading('Category', text='Category')
        self.history_tree.heading('Amount', text='Amount (₹)')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Tag configurations for coloring
        self.history_tree.tag_configure('expense', foreground='red')
        self.history_tree.tag_configure('income', foreground='green')
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_command(label="Customize", command=self.customize_selected)
        self.history_tree.bind("<Button-3>", self.show_context_menu)

        # Daily balance frame
        balance_frame = ttk.Frame(content_frame, padding=(0, 10, 0, 0))
        balance_frame.pack(fill=tk.X)
        
        tk.Label(balance_frame, text="Remaining Balance:",bg='#f0f0f0', font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        self.daily_balance_label = ttk.Label(balance_frame, text="₹0.00", style='Profit.TLabel')
        self.daily_balance_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Initially hide bonus frame
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
            
        # Collect transactions to delete
        transactions_to_delete = []
        
        for item in self.selected_items:
            tags = self.history_tree.item(item, 'tags')
            if len(tags) < 2:  # Ensure we have ID tag
                continue
                
            trans_id = tags[1]
            # Get type from first tag instead of values
            trans_type = 'Expense' if tags[0] == 'expense' else 'Income'
            trans_date = self.current_date
            
            # For range mode, we need to find the actual date
            if 'range_mode' in tags:
                trans_date = tags[2]
                
            transactions_to_delete.append({
                'id': trans_id,
                'type': trans_type,
                'date': trans_date
            })
        
        # Perform deletion
        self.perform_deletion(transactions_to_delete)

    def perform_deletion(self, transactions):
        """Perform deletion and store in undo stack"""
        deleted_transactions = []
    
        for trans in transactions:
            trans_id = trans['id']
            trans_type = trans['type']
            trans_date = trans['date']
            
            # Find and remove transaction
            if trans_type == "Expense" and trans_date in self.expense_data:
                for i, t in enumerate(self.expense_data[trans_date]):
                    if t.get('id') == trans_id:
                        deleted_trans = self.expense_data[trans_date].pop(i)
                        deleted_trans['date'] = trans_date
                        deleted_trans['source'] = 'expense'
                        deleted_trans['index'] = i  # Store original index
                        deleted_transactions.append(deleted_trans)
                        break
            
            elif trans_type == "Income" and trans_date in self.income_data:
                for i, t in enumerate(self.income_data[trans_date]):
                    if t.get('id') == trans_id:
                        deleted_trans = self.income_data[trans_date].pop(i)
                        deleted_trans['date'] = trans_date
                        deleted_trans['source'] = 'income'
                        deleted_trans['index'] = i  # Store original index
                        deleted_transactions.append(deleted_trans)
                        break
        
        if deleted_transactions:
            # Save changes
            self.save_data(self.expense_data, self.expense_file)
            self.save_data(self.income_data, self.income_file)
            
            # Add to undo stack
            self.undo_stack.append(deleted_transactions)
            
            # Update display
            self.update_display()
            
            # messagebox.showinfo("Success", f"Deleted {len(deleted_transactions)} transaction(s)")

    def undo_delete(self, event=None):
        if not self.undo_stack:
            return
            
        # Get last deleted transactions
        transactions = self.undo_stack.pop()
        
        for trans in transactions:
            trans_date = trans['date']
            source = trans.pop('source', 'expense')
            original_index = trans.pop('index', None) 
            
            if source == 'expense':
                if trans_date not in self.expense_data:
                    self.expense_data[trans_date] = []
                # Insert at original position if possible, else append
                if original_index is not None and original_index <= len(self.expense_data[trans_date]):
                    self.expense_data[trans_date].insert(original_index, trans)
                else:
                    self.expense_data[trans_date].append(trans)
                    
            elif source == 'income':
                if trans_date not in self.income_data:
                    self.income_data[trans_date] = []
                # Insert at original position if possible, else append
                if original_index is not None and original_index <= len(self.income_data[trans_date]):
                    self.income_data[trans_date].insert(original_index, trans)
                else:
                    self.income_data[trans_date].append(trans)
        
        # Save changes
        self.save_data(self.expense_data, self.expense_file)
        self.save_data(self.income_data, self.income_file)
        
        # Update display
        self.update_display()
        
        # messagebox.showinfo("Undo", f"Restored {len(transactions)} transaction(s)")

    def customize_selected(self):
        """Customize selected transaction"""
        selected_items = self.history_tree.selection()
        if not selected_items:
            return
            
        # Get first selected item
        item = selected_items[0]
        values = self.history_tree.item(item, 'values')
        tags = self.history_tree.item(item, 'tags')
        
        if len(tags) < 2:  # Ensure we have ID tag
            return
            
        trans_id = tags[1]
        trans_date = self.current_date
        # Get type from tag instead of values
        trans_type = 'Expense' if tags[0] == 'expense' else 'Income'
        
        # For range mode, get time from values since structure changed
        if 'range_mode' in tags:
            trans_date = tags[2]
            trans_time = values[1]  # Time is now at index 1
        
        else:
            trans_time = values[0] 
            
        # Find the transaction
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
            
        # Open customization window
        self.open_customization_window(transaction, data_source, trans_date)

    def open_customization_window(self, transaction, data_source, date):
        """Open window to customize transaction"""
        top = tk.Toplevel(self.root, background='#7e7e7e')
        top.title("Customize Transaction")
        top.geometry("300x300")
        top.resizable(False, False)
        top.grab_set()

        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        top.geometry(f"+{root_x+50}+{root_y+50}")
        
        # Time (display only)
        time_frame = ttk.Frame(top, padding=10)
        time_frame.pack(fill=tk.X)
        ttk.Label(time_frame, text="Time:", font=('Helvetica', 12)).pack(side=tk.LEFT)
        
        # Format time consistently
        time_str = transaction['time']  # Use original 24-hour format time
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
        formatted_time = time_obj.strftime("%I:%M:%S %p").lstrip('0')
        ttk.Label(time_frame, text=formatted_time, font=('Helvetica', 12)).pack(side=tk.LEFT, padx=10)

        # Type
        type_frame = ttk.Frame(top, padding=10)
        type_frame.pack(fill=tk.X)
        ttk.Label(type_frame, text="Type:", font=('Helvetica', 12)).pack(side=tk.LEFT)
        trans_type = tk.StringVar(value=transaction.get('type', "Expense"))
        ttk.Radiobutton(type_frame, text="Expense", variable=trans_type, 
                       value="Expense").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Income", variable=trans_type, 
                       value="Income").pack(side=tk.LEFT, padx=5)
        
        # Category
        category_frame = ttk.Frame(top, padding=10)
        category_frame.pack(fill=tk.X)
        ttk.Label(category_frame, text="Category:", font=('Helvetica', 12)).pack(side=tk.LEFT)
        category = ttk.Combobox(category_frame, state="readonly", width=15)
        category['values'] = (
            'Food', 'Transport', 'Shopping', 
            'Entertainment', 'Bills', 'Salary', 
            'Freelance', 'Investment', 'Other'
        )
        category.set(transaction.get('category', 'Other'))
        category.pack(side=tk.LEFT, padx=10)
        
        # Amount
        amount_frame = ttk.Frame(top, padding=10)
        amount_frame.pack(fill=tk.X)
        ttk.Label(amount_frame, text="Amount (₹):", font=('Helvetica', 12)).pack(side=tk.LEFT)
        amount = ttk.Entry(amount_frame, width=15)
        amount.insert(0, str(transaction.get('amount', 0)))
        amount.pack(side=tk.LEFT, padx=10)
        
        # Save button
        button_frame = ttk.Frame(top, padding=10)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="Save Changes", 
                  command=lambda: self.save_customization(
                      transaction, data_source, date,
                      trans_type.get(), category.get(), amount.get(),
                      top
                  )).pack(pady=10)

    def save_customization(self, transaction, data_source, date, 
                          trans_type, category, amount, window):
        """Save customized transaction"""
        try:
            amount_val = float(amount)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount value")
            return
            
        # Update transaction data
        transaction['type'] = trans_type
        transaction['category'] = category
        transaction['amount'] = amount_val
        
        # If type changed, move to appropriate data source
        if trans_type == "Expense" and data_source is not self.expense_data:
            # Remove from current data source
            if date in data_source:
                for i, t in enumerate(data_source[date]):
                    if t['id'] == transaction['id']:
                        data_source[date].pop(i)
                        break
                        
            # Add to expense data
            if date not in self.expense_data:
                self.expense_data[date] = []
            self.expense_data[date].append(transaction)
            data_source = self.expense_data
            
        elif trans_type == "Income" and data_source is not self.income_data:
            # Remove from current data source
            if date in data_source:
                for i, t in enumerate(data_source[date]):
                    if t['id'] == transaction['id']:
                        data_source[date].pop(i)
                        break
                        
            # Add to income data
            if date not in self.income_data:
                self.income_data[date] = []
            self.income_data[date].append(transaction)
            data_source = self.income_data
        
        
        # Save changes
        self.save_data(self.expense_data, self.expense_file)
        self.save_data(self.income_data, self.income_file)
        
        # Update display
        self.update_display()
        
        # Close window
        window.destroy()
        messagebox.showinfo("Success", "Transaction updated successfully")

    def format_display_date(self, date_str):
        """Format YYYY-MM-DD date for display (e.g., 16 Jun 2023)"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d %b %Y")

    def open_calendar(self):
        """Open option popup to select history type"""
        top = tk.Toplevel(self.root)
        top.title("Select History Type")
        top.geometry("300x150")
        top.resizable(False, False)
        top.grab_set()  # Make it modal
        
        # Create option buttons
        btn_frame = ttk.Frame(top)
        btn_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        ttk.Button(
            btn_frame, 
            text="Date wise Transaction History",
            command=lambda: self.select_single_date(top)
        ).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            btn_frame, 
            text="Transaction History Between Two Dates",
            command=lambda: self.select_date_range(top)
        ).pack(fill=tk.X, pady=5)

    def select_single_date(self, top=None):
        """Handle single date selection"""
        if top:
            top.destroy()
        self.show_calendar_popup("Select Date", self.handle_single_date_selection)

    def select_date_range(self, top=None):
        """Handle date range selection"""
        if top:
            top.destroy()
        self.show_range_calendar_popup()

    def show_calendar_popup(self, title, command_handler):
        """Show calendar popup for single date selection"""
        top = tk.Toplevel(self.root, background='#7e7e7e')
        top.title(title)
        top.grab_set()

        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        top.geometry(f"+{root_x+50}+{root_y+50}")
        
        cal = Calendar(
            top, 
            selectmode='day', 
            date_pattern='y-mm-dd',
            year=int(self.current_date[:4]),
            month=int(self.current_date[5:7]),
            day=int(self.current_date[8:])
        )
        cal.pack(padx=10, pady=10)
        
        def set_date():
            selected_date = cal.get_date()
            command_handler(selected_date)
            top.destroy()
        
        ttk.Button(top, text="OK", command=set_date).pack(pady=10)

    def show_range_calendar_popup(self): 
        """Show calendar popup for date range selection"""
        top = tk.Toplevel(self.root, background='#7e7e7e')
        top.title("Select Date Range")
        top.grab_set()

        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        top.geometry(f"+{root_x+50}+{root_y+50}") 
        
        # Create frames for the two calendars
        frame = ttk.Frame(top)
        frame.pack(padx=10, pady=10)
        
        # Start date calendar
        start_frame = ttk.Frame(frame)
        start_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(start_frame, text="Start Date", font=10).pack()

        if self.range_start_date:
            start_year = int(self.range_start_date[:4])
            start_month = int(self.range_start_date[5:7])
            start_day = int(self.range_start_date[8:])
        else:
            today = datetime.now()
            start_year, start_month, start_day = today.year, today.month, today.day

        start_cal = Calendar(
            start_frame, 
            selectmode='day', 
            date_pattern='y-mm-dd',
            year=start_year,
            month=start_month,
            day=start_day
        )
        start_cal.pack(pady=5)
        
        # End date calendar
        end_frame = ttk.Frame(frame)
        end_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(end_frame, text="End Date", font=10).pack()

        if self.range_end_date:
            end_year = int(self.range_end_date[:4])
            end_month = int(self.range_end_date[5:7])
            end_day = int(self.range_end_date[8:])
        else:
            today = datetime.now()
            end_year, end_month, end_day = today.year, today.month, today.day
            
        end_cal = Calendar(
            end_frame, 
            selectmode='day', 
            date_pattern='y-mm-dd',
            year=end_year,
            month=end_month,
            day=end_day
        )
        end_cal.pack(pady=5)
        
        def set_range():
            start_date = start_cal.get_date()
            end_date = end_cal.get_date()
            self.range_start_date = start_date  # Remember start date
            self.range_end_date = end_date      # Remember end date
            self.handle_date_range_selection(start_date, end_date)
            top.destroy()
        
        ttk.Button(top, text="OK", command=set_range).pack(pady=10)

    def handle_single_date_selection(self, selected_date):
        """Handle selection of a single date"""
        self.current_date = selected_date
        self.date_label.config(text=f"Date: {self.format_display_date(self.current_date)}")
        self.update_display()

    def handle_date_range_selection(self, start_date, end_date):
        """Handle selection of a date range"""
        # Convert to datetime objects for comparison
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Swap dates if start is after end
        if start_dt > end_dt:
            start_date, end_date = end_date, start_date
            
        self.date_label.config(text=f"Date: {self.format_display_date(start_date)} to {self.format_display_date(end_date)}")
        self.show_range_history(start_date, end_date)

    def show_range_history(self, start_date, end_date):
        """Show transaction history between two dates"""
        # Convert to datetime objects for comparison
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Clear current treeview
        self.history_tree.delete(*self.history_tree.get_children())
        
        # Collect all transactions in the date range
        all_transactions = []
        
        # Process expenses
        for date, transactions in self.expense_data.items():
            trans_dt = datetime.strptime(date, "%Y-%m-%d")
            if start_dt <= trans_dt <= end_dt:
                for trans in transactions:
                    all_transactions.append((
                        date,  # Add date to display
                        trans['time'],
                        'Expense',
                        trans['category'],
                        trans['amount'],
                        trans.get('id', str(uuid.uuid4()))  # Add unique ID
                    ))
        
        # Process income
        for date, transactions in self.income_data.items():
            trans_dt = datetime.strptime(date, "%Y-%m-%d")
            if start_dt <= trans_dt <= end_dt:
                for trans in transactions:
                    all_transactions.append((
                        date,  # Add date to display
                        trans['time'],
                        'Income',
                        trans['category'],
                        trans['amount'],
                        trans.get('id', str(uuid.uuid4()))  # Add unique ID
                    ))
        
        # Sort by datetime descending (newest first)
        all_transactions.sort(
            key=lambda x: datetime.strptime(f"{x[0]} {x[1]}", "%Y-%m-%d %H:%M:%S"), 
            reverse=True
        )
        
        # Update treeview columns to include date
        self.update_treeview_columns(include_date=True)
        
        # Add transactions to treeview
        for trans in all_transactions:
            date, time, trans_type, category, amount, trans_id = trans
            time_obj = datetime.strptime(time, "%H:%M:%S")
            formatted_time = time_obj.strftime("%I:%M:%S %p").lstrip('0')
            
            if trans_type == "Expense":
                tag = 'expense'
                amount_str = f"-₹{amount:.2f}"
            else:
                tag = 'income'
                amount_str = f"+₹{amount:.2f}"
            
            # Format date for display
            formatted_date = self.format_display_date(date)
            
            # Add transaction ID and date as tags for context menu
            tags = (tag, trans_id, date, 'range_mode')
            
            self.history_tree.insert(
                '', tk.END, 
                values=(formatted_date, formatted_time, trans_type, category, amount_str),
                tags=tags
            )
        
        # Update totals for the date range
        self.update_range_totals(start_date, end_date)

    def update_treeview_columns(self, include_date=False):
        """Update treeview columns based on display mode"""
        # Clear existing columns
        for col in self.history_tree['columns']:
            self.history_tree.heading(col, text='')
            self.history_tree.column(col, width=0)
        
        # Create new columns based on mode
        if include_date:
            columns = ('Date', 'Time', 'Type', 'Category', 'Amount')
            self.history_tree['columns'] = columns
            
            # Configure columns
            self.history_tree.column('Date', width=100, anchor=tk.CENTER)
            self.history_tree.column('Time', width=100, anchor=tk.CENTER)
            self.history_tree.column('Type', width=80, anchor=tk.CENTER)
            self.history_tree.column('Category', width=120, anchor=tk.CENTER)
            self.history_tree.column('Amount', width=120, anchor=tk.CENTER)
            
            # Create headings
            self.history_tree.heading('Date', text='Date')
            self.history_tree.heading('Time', text='Time')
            self.history_tree.heading('Type', text='Type')
            self.history_tree.heading('Category', text='Category')
            self.history_tree.heading('Amount', text='Amount (₹)')
        else:
            columns = ('Time', 'Type', 'Category', 'Amount')
            self.history_tree['columns'] = columns
            
            # Configure columns
            self.history_tree.column('Time', width=100, anchor=tk.CENTER)
            self.history_tree.column('Type', width=80, anchor=tk.CENTER)
            self.history_tree.column('Category', width=120, anchor=tk.CENTER)
            self.history_tree.column('Amount', width=120, anchor=tk.CENTER)
            
            # Create headings
            self.history_tree.heading('Time', text='Time')
            self.history_tree.heading('Type', text='Type')
            self.history_tree.heading('Category', text='Category')
            self.history_tree.heading('Amount', text='Amount (₹)')

    def update_range_totals(self, start_date, end_date):
        """Calculate and display totals for a date range"""
        total_expense = 0
        total_income = 0
        total_bonus = 0 
        
        # Convert to datetime objects
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate expenses
        for date, transactions in self.expense_data.items():
            trans_dt = datetime.strptime(date, "%Y-%m-%d")
            if start_dt <= trans_dt <= end_dt:
                for trans in transactions:
                    total_expense += trans['amount']
        
        # Calculate income
        for date, transactions in self.income_data.items():
            trans_dt = datetime.strptime(date, "%Y-%m-%d")
            if start_dt <= trans_dt <= end_dt:
                for trans in transactions:
                    total_income += trans['amount']
                    # Add bonus calculation
                    if trans.get('category') == "Bonus":
                        total_bonus += trans['amount']
        
        # Update UI
        self.today_expense_label.config(text=f"₹{total_expense:.2f}")
        self.today_income_label.config(text=f"₹{total_income:.2f}")
        self.today_bonus_label.config(text=f"₹{total_bonus:.2f}")
        
        # Update daily balance
        daily_balance = total_income - total_expense
        balance_text = f"₹{daily_balance:.2f}"
        if daily_balance >= 0:
            self.daily_balance_label.config(text=balance_text, style='Profit.TLabel')
        else:
            self.daily_balance_label.config(text=balance_text, style='Loss.TLabel')

    def toggle_bonus(self):
        """Show/hide bonus entry based on transaction type"""
        if self.trans_type.get() == "Income":
            self.bonus_frame.pack(fill=tk.X, pady=5)
        else:
            self.bonus_frame.pack_forget()

    def add_transaction(self):
        """Add a new transaction (expense or income)"""
        amount_str = self.amount_entry.get()
        bonus_str = self.bonus_entry.get() if self.trans_type.get() == "Income" else ""
        trans_type = self.trans_type.get()
        category = self.category.get()
        
        if not amount_str:
            messagebox.showerror("Error", "Please enter an amount")
            return
            
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
            return
            
        # Get current time but use the SELECTED DATE
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = self.current_date  # Use the selected date instead of current date
        
        # Create transaction record
        transaction = {
            "id": str(uuid.uuid4()),  # Add unique ID
            "date": date_str,
            "time": time_str,
            "amount": amount,
            "category": category,
            "type": trans_type  # Store type with transaction
        }
        
        # Save to appropriate file
        if trans_type == "Expense":
            if date_str not in self.expense_data:
                self.expense_data[date_str] = []
            self.expense_data[date_str].append(transaction)
            self.save_data(self.expense_data, self.expense_file)
        else:
            if date_str not in self.income_data:
                self.income_data[date_str] = []
            self.income_data[date_str].append(transaction)
            
            # Add bonus transaction if applicable
            if bonus_str:
                try:
                    bonus = float(bonus_str)
                    bonus_transaction = {
                        "id": str(uuid.uuid4()),
                        "date": date_str,
                        "time": time_str,
                        "amount": bonus,
                        "category": "Bonus",
                        "type": "Income"
                    }
                    self.income_data[date_str].append(bonus_transaction)
                except ValueError:
                    pass  # Silently ignore invalid bonus entries
            
            self.save_data(self.income_data, self.income_file)
        
        # Update display and clear entries
        self.update_display()
        self.amount_entry.delete(0, tk.END)
        self.bonus_entry.delete(0, tk.END)

    def update_display(self):
        """Update all display elements with current data"""
        # Calculate totals for selected date
        selected_expense = 0
        selected_income = 0
        self.selected_bonus = 0
        
        if self.current_date in self.expense_data:
            for trans in self.expense_data[self.current_date]:
                selected_expense += trans['amount']
        
        if self.current_date in self.income_data:
            for trans in self.income_data[self.current_date]:
                selected_income += trans['amount']
                # Add bonus calculation
                if trans.get('category') == "Bonus":
                    self.selected_bonus += trans['amount']

        self.today_expense_label.config(text=f"₹{selected_expense:.2f}")
        self.today_income_label.config(text=f"₹{selected_income:.2f}")
        self.today_bonus_label.config(text=f"₹{self.selected_bonus:.2f}")
        
        # Update daily balance
        daily_balance = selected_income - selected_expense
        balance_text = f"₹{daily_balance:.2f}"
        if daily_balance >= 0:
            self.daily_balance_label.config(text=balance_text, style='Profit.TLabel')
        else:
            self.daily_balance_label.config(text=balance_text, style='Loss.TLabel')
        
        self.update_treeview_columns(include_date=False)

        # Update history tree
        self.history_tree.delete(*self.history_tree.get_children())
        
        # Collect all transactions and sort by datetime
        selected_transactions  = []
        
        # Add expenses
        if self.current_date in self.expense_data:
            for trans in self.expense_data[self.current_date]:
                selected_transactions.append((
                    'Expense',
                    trans['time'],
                    trans['category'],
                    trans['amount'],
                    datetime.strptime(f"{self.current_date} {trans['time']}", "%Y-%m-%d %H:%M:%S"),
                    trans.get('id', str(uuid.uuid4()))  # Add unique ID
                ))
        
        # Add income
        if self.current_date in self.income_data:
            for trans in self.income_data[self.current_date]:
                selected_transactions.append((
                    'Income',
                    trans['time'],
                    trans['category'],
                    trans['amount'],
                    datetime.strptime(f"{self.current_date} {trans['time']}", "%Y-%m-%d %H:%M:%S"),
                    trans.get('id', str(uuid.uuid4()))  # Add unique ID
                ))
        
        # Sort by datetime descending (newest first)
        selected_transactions.sort(key=lambda x: x[4], reverse=True)
        
        # Add sorted transactions to treeview
        for trans in selected_transactions:
            trans_type, time, category, amount, _, trans_id = trans
            time_obj = datetime.strptime(time, "%H:%M:%S")
            formatted_time = time_obj.strftime("%I:%M:%S %p")
            # Remove leading zero if present (e.g., 04: → 4:)
            if formatted_time.startswith('0'):
                formatted_time = formatted_time[1:]

            if trans_type == "Expense":
                tag = 'expense'
                amount_str = f"-₹{amount:.2f}"
            else:
                tag = 'income'
                amount_str = f"+₹{amount:.2f}"
            
            # Add transaction ID as tag for context menu
            tags = (tag, trans_id)
            
            self.history_tree.insert(
                '', tk.END, 
                values=(formatted_time, trans_type, category, amount_str),
                tags=tags
            )














if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()