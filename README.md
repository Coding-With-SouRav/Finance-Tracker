# Finance Tracker

### Overview
This is a Python desktop application built with Tkinter for personal finance management. It tracks income and expenses with a modern UI, data persistence, and multiple view options.

### Key Features
1. **Dual Transaction Tracking**:
   - Records both expenses and income
   - Separate categories for each type (Food, Transport, Salary, Freelance, etc.)
   - Special "Bonus" category for income

2. **Data Management**:
   - Stores data in JSON files
   - Uses hidden directory (`~/.FinanceTracker`) for data storage
   - Auto-migrates old data files
   - Unique UUIDs for all transactions

3. **Modern UI**:
   - Themed interface with accent colors
   - Responsive layout
   - Custom icons and calendar integration
   - Context menus for transactions

4. **Transaction Management**:
   - Add/edit/delete transactions
   - Undo functionality (Ctrl+Z)
   - Right-click context menu
   - Customizable transaction fields

5. **Date Management**:
   - Daily transaction view
   - Date range selection (between two dates)
   - Calendar popups for date selection
   - Persistent date selection

6. **Financial Insights**:
   - Daily income/expense totals
   - Bonus income tracking
   - Balance calculation (income - expenses)
   - Color-coded balances (green/red)

7. **Advanced Functionality**:
   - Search transactions by date range
   - Sortable transaction history
   - Time-formatted transaction entries
   - Window state persistence (size/position)

8. **Technical Features**:
   - Resource path handling for PyInstaller
   - Windows-specific hidden folder attributes
   - Config file for preferences
   - Keyboard shortcuts (Delete, Ctrl+Z)

### Usage Flow
1. **Add Transaction**:
   - Select income/expense type
   - Enter amount
   - Choose category
   - Add bonus for income (optional)

2. **View History**:
   - Daily view (default)
   - Date range view (via calendar icon)
   - Sort by time/date

3. **Manage Transactions**:
   - Delete via selection + Delete key
   - Edit via right-click → Customize
   - Undo deletion with Ctrl+Z

4. **Analyze Finances**:
   - View daily totals
   - See balance calculations
   - Compare income vs expenses

### Technical Highlights
- Uses `tkcalendar` for date pickers
- Pillow for image handling
- ConfigParser for settings
- JSON for data storage
- UUID for transaction tracking
- Windows API for hidden folders

This application provides a comprehensive solution for personal finance tracking with a polished interface and robust data management capabilities. The combination of daily tracking, historical views, and financial insights makes it suitable for regular financial monitoring.

# Demo Image
![Screenshot 2025-06-18 101455](https://github.com/user-attachments/assets/b1cf0d93-7bff-429a-8d50-2cd127ad949b)
![Screenshot 2025-06-18 101416](https://github.com/user-attachments/assets/aa6308d5-723d-425d-84ad-6a84eb6bc999)
![Screenshot 2025-06-18 101523](https://github.com/user-attachments/assets/f21f6413-765a-4fa4-898b-e356f356d9db)

