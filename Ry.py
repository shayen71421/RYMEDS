import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

class MedicineExpiryTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Medicine Expiry Tracker")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f4f7')  # Light background color
        
        # Window to be fullscreen
        self.root.attributes('-fullscreen', True)
        
        self.sort_column = None
        self.sort_ascending = True
        
        self.create_database()

        # Configuring styles of the search text
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 10), padding=6, relief="flat")
        self.style.configure('TLabel', font=('Arial', 12), background='#f0f4f7')
        self.style.configure('Treeview', font=('Arial', 10))
        self.style.configure('Treeview.Heading', font=('Arial', 12, 'bold'), background='#4CAF50', foreground='black')

        # Configuring styles of the box and buttons
        search_frame = tk.Frame(root, bg='#f0f4f7')
        search_frame.pack(pady=10)

        self.search_label = ttk.Label(search_frame, text="Search by Code or Name:")
        self.search_label.pack(side="left", padx=10)

        self.search_entry = ttk.Entry(search_frame, width=25, font=('Arial', 10))
        self.search_entry.pack(side="left", pady=5, fill="x", padx=10)

        self.search_button = ttk.Button(search_frame, text="Search", command=self.search_medicine, style="TButton")
        self.search_button.pack(side="left", pady=5)

        self.back_button = ttk.Button(root, text="Back", command=self.back_to_default, state=tk.DISABLED, style="TButton")
        self.back_button.pack(pady=5)

        # Code for the table of all rows
        self.tree = ttk.Treeview(root, columns=("Code", "Batch", "Name", "Chemical Name", "Company", "MFD Date", 
                                                "EXP Date", "Quantity", "Price", "Dosage", "Nos per Strip"), 
                                 show="headings")
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Buttons for add edit delete etc
        button_frame = tk.Frame(root, bg='#f0f4f7')
        button_frame.pack(pady=20)

        self.add_button = ttk.Button(button_frame, text="Add Medicine", command=self.open_add_medicine_popup, style="TButton")
        self.add_button.pack(side="left", padx=10)

        self.edit_button = ttk.Button(button_frame, text="Edit Medicine", command=self.open_edit_medicine_popup, state=tk.DISABLED, style="TButton")
        self.edit_button.pack(side="left", padx=10)

        self.delete_button = ttk.Button(button_frame, text="Delete Medicine", command=self.delete_medicine, state=tk.DISABLED, style="TButton")
        self.delete_button.pack(side="left", padx=10)

        self.check_expiry_button = ttk.Button(button_frame, text="Check Expiry", command=self.check_expiry, style="TButton")
        self.check_expiry_button.pack(side="left", padx=10)

        self.load_data()

        # Turning on and off buttons related to the situation
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def create_database(self):
        with sqlite3.connect('PEEPEEE.db') as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS medicine (
                            code TEXT PRIMARY KEY,
                            batch INTEGER,
                            name TEXT,
                            chem_name TEXT,
                            company TEXT,
                            mfg_date TEXT,
                            expiry_date TEXT,
                            quantity INTEGER,
                            price INTEGER,
                            dosage INTEGER,
                            Nos_Per_Strip INTEGER)''')
            conn.commit()

    def on_tree_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def load_data(self, search_query=""):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Making the default to be sorted with exp date 
        with sqlite3.connect('PEEPEEE.db') as conn:
            c = conn.cursor()
            if search_query:
                c.execute("SELECT * FROM medicine WHERE code LIKE ? OR name LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
            else:
                c.execute("SELECT * FROM medicine ORDER BY expiry_date ASC")
            rows = c.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)

    def search_medicine(self):
        search_query = self.search_entry.get()
        self.load_data(search_query)
        self.back_button.config(state=tk.NORMAL)

    def back_to_default(self):
        self.search_entry.delete(0, tk.END)
        self.load_data()
        self.back_button.config(state=tk.DISABLED)

    def sort_by_column(self, column):
        self.sort_ascending = not self.sort_ascending if self.sort_column == column else True
        self.sort_column = column

        with sqlite3.connect('PEEPEEE.db') as conn:
            c = conn.cursor()
            order = "ASC" if self.sort_ascending else "DESC"
            
            # Using SQL for sorting of the dates as it can't be done in normal tkinter
            if column == "MFD Date" or column == "EXP Date":
                if column == "MFD Date":
                    c.execute(f"SELECT * FROM medicine ORDER BY strftime('%Y-%m-%d', mfg_date) {order}")
                elif column == "EXP Date":
                    c.execute(f"SELECT * FROM medicine ORDER BY strftime('%Y-%m-%d', expiry_date) {order}")
            else:
                c.execute(f"SELECT * FROM medicine ORDER BY {column.lower().replace(' ', '_')} {order}")
            rows = c.fetchall()
            
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in rows:
            self.tree.insert("", "end", values=row)

    def check_expiry(self):
        current_date = datetime.now()
        two_months_later = current_date + timedelta(days=60)  # the time in which all medicines are about to expire

        # For a new window for the expiry check
        expiry_window = tk.Toplevel(self.root)
        expiry_window.title("Medicine Expiry Status")
        expiry_window.geometry("800x400")

        # Table for the expired medicines
        tree = ttk.Treeview(expiry_window, columns=("Code", "Batch", "Name", "Chemical Name", "Company", "MFD Date", 
                                                     "EXP Date", "Quantity", "Price", "Dosage", "Nos per Strip"), show="headings")

        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(expiry_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        with sqlite3.connect('PEEPEEE.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM medicine")
            rows = c.fetchall()

            for row in rows:
                expiry_date_str = row[6]
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                    if expiry_date <= current_date:
                        # Expired medicines in red
                        tree.tag_configure("expired", background="red", foreground="white")
                        tree.insert("", "end", values=row, tags="expired")
                    elif expiry_date <= two_months_later:
                        # Expiring medicines in yellow
                        tree.tag_configure("expiring_soon", background="yellow", foreground="black")
                        tree.insert("", "end", values=row, tags="expiring_soon")
                    else:
                        # Safe medicines in green
                        tree.tag_configure("safe", background="green", foreground="white")
                        tree.insert("", "end", values=row, tags="safe")
                except ValueError:
                    print(f"Invalid expiry date format for row: {row[0]}, skipping this record.")

    def open_add_medicine_popup(self):
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Add Medicine")
        self.popup.geometry("500x400")

        frame = tk.Frame(self.popup)
        frame.pack(pady=20)

        labels = ["Medicine Code", "Batch", "Medicine Name", "Chemical Name", "Company", "Manufacturing Date (YYYY-MM-DD)",
                  "Expiry Date (YYYY-MM-DD)", "Quantity", "Price", "Dosage", "No. Per Strip"]
        self.entries = {}

        for idx, label in enumerate(labels):
            tk.Label(frame, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(frame)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.entries[label] = entry

        add_button = ttk.Button(frame, text="Add Medicine", command=self.add_medicine)
        add_button.grid(row=len(labels), columnspan=2, pady=10)

    def add_medicine(self):
        values = [entry.get() for entry in self.entries.values()]
        with sqlite3.connect('PEEPEEE.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO medicine VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
            conn.commit()
        self.popup.destroy()
        self.load_data()

    def open_edit_medicine_popup(self):
        selected_item = self.tree.selection()[0]
        row_values = self.tree.item(selected_item, "values")

        self.popup = tk.Toplevel()
        self.popup.title("Edit Medicine")

        frame = tk.Frame(self.popup)
        frame.pack(pady=20)

        labels = ["Medicine Code", "Batch", "Medicine Name", "Chemical Name", "Company", "Manufacturing Date (YYYY-MM-DD)",
                  "Expiry Date (YYYY-MM-DD)", "Quantity", "Price", "Dosage", "No. Per Strip"]
        self.entries = {}

        for idx, (label, value) in enumerate(zip(labels, row_values)):
            tk.Label(frame, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(frame)
            entry.insert(0, value)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.entries[label] = entry

        save_button = ttk.Button(frame, text="Save Changes", command=lambda: self.edit_medicine(selected_item))
        save_button.grid(row=len(labels), columnspan=2, pady=10)

    def edit_medicine(self, selected_item):
        updated_values = [entry.get() for entry in self.entries.values()]
        with sqlite3.connect('PEEPEEE.db') as conn:
            c = conn.cursor()
            c.execute("""UPDATE medicine 
                         SET code = ?, batch = ?, name = ?, chem_name = ?, company = ?, mfg_date = ?, 
                             expiry_date = ?, quantity = ?, price = ?, dosage = ?, Nos_Per_Strip = ? 
                         WHERE code = ?""",
                      (*updated_values, self.tree.item(selected_item, "values")[0]))
            conn.commit()
        self.popup.destroy()
        self.load_data()

    def delete_medicine(self):
        selected_item = self.tree.selection()[0]
        code = self.tree.item(selected_item, "values")[0]
        
        if messagebox.askyesno("Delete Medicine", f"Are you sure you want to delete medicine with code {code}?"):
            with sqlite3.connect('PEEPEEE.db') as conn:
                c = conn.cursor()
                c.execute("DELETE FROM medicine WHERE code = ?", (code,))
                conn.commit()
            self.load_data()


if __name__ == "__main__":
    root = tk.Tk()
    app = MedicineExpiryTracker(root)
    root.mainloop()
