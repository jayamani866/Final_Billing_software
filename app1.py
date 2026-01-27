# app.py
# Theme 3: Dark Purple Gaming Theme
# Run: python3 app.py
# Requires: db_connection.get_connection(), fpdf, mysql-connector-python

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from fpdf import FPDF
from db_connection import get_connection
import datetime
import threading

# -------------------------
# Theme colors (dark purple gaming)
# -------------------------
BG = "#1e1b29"
CARD = "#252133"
ACCENT1 = "#7b6bff"
ACCENT2 = "#4bd1ff"
TEXT = "#e6e1ff"
BUTTON_TEXT = "#ffffff"
WARN = "#ff6b6b"
GOOD = "#5ef27e"

# -------------------------
# Window helper
# -------------------------
def center_window(win, w, h):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (w // 2)
    y = (screen_h // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

# -------------------------
# Small helper: safe DB execute (auto commit optional)
# -------------------------
def ensure_tables_exist(shop_id):
    """
    Create customers, sales, bill_items tables if they don't exist.
    customers table schema uses the schema provided by user (with shop_id FK).
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        # customers
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL,
            name VARCHAR(255),
            phone VARCHAR(255) UNIQUE,
            address VARCHAR(255),
            total_spent DOUBLE DEFAULT 0,
            joined_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # sales
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_phone VARCHAR(255),
            total_amount DOUBLE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # bill_items
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT,
            product_id VARCHAR(255),
            quantity INT,
            price DOUBLE,
            subtotal DOUBLE
        )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("Ensure tables error:", e)

# -------------------------
# SMS placeholder
# -------------------------
def send_sms(phone, message):
    # placeholder - replace with Twilio or your provider
    print(f"[SMS -> {phone}]: {message}")
    # Example Twilio snippet:
    # from twilio.rest import Client
    # account_sid = 'AC...'
    # auth_token = '...'
    # client = Client(account_sid, auth_token)
    # client.messages.create(body=message, from_='+1xxx', to=phone)

# -------------------------
# Billing window
# -------------------------
def start_billing_app(shop_id, owner_name):
    # ensure DB tables exist first
    ensure_tables_exist(shop_id)

    billing = tk.Toplevel()
    billing.title(f"Billing - {owner_name}")
    billing.configure(bg=BG)
    center_window(billing, 1200, 760)

    header = tk.Frame(billing, bg=BG)
    header.pack(fill="x", pady=6)
    lbl_title = tk.Label(header, text="SRI KRISHNA DEPARTMENT STORE", font=("Helvetica", 20, "bold"),
                         fg=TEXT, bg=BG)
    lbl_title.pack()

    sub = tk.Label(header, text=f"Shop Owner: {owner_name} | Shop ID: {shop_id}", bg=BG, fg=ACCENT1)
    sub.pack()

    # -------- top frame: phone, name, save, tick ----------
    top = tk.Frame(billing, bg=BG)
    top.pack(pady=8)

    tk.Label(top, text="Customer Phone:", bg=BG, fg=TEXT).grid(row=0, column=0, padx=6)
    entry_phone = tk.Entry(top, width=18, bg=CARD, fg=TEXT, insertbackground=TEXT)
    entry_phone.grid(row=0, column=1, padx=6)

    lbl_name = tk.Label(top, text="Name: ------", bg=BG, fg=TEXT)
    lbl_name.grid(row=0, column=2, padx=10)

    tick_lbl = tk.Label(top, text="", bg=BG, fg=GOOD, font=("Arial", 14))
    tick_lbl.grid(row=0, column=3, padx=6)

    def lookup_customer(event=None):
        phone = entry_phone.get().strip()
        if phone == "":
            lbl_name.config(text="Name: ------")
            tick_lbl.config(text="")
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT name FROM customers WHERE phone=%s", (phone,))
            row = cur.fetchone()
            conn.close()
            if row:
                lbl_name.config(text=f"Name: {row[0]}")
                tick_lbl.config(text="✅")
            else:
                lbl_name.config(text="Name: NEW CUSTOMER")
                tick_lbl.config(text="")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def save_customer():
        phone = entry_phone.get().strip()
        if phone == "":
            messagebox.showwarning("Warning", "Enter phone to save.")
            return
        name_text = lbl_name.cget("text").replace("Name: ", "")
        if name_text in ("------", "NEW CUSTOMER"):
            name_text = simpledialog.askstring("Customer name", "Enter customer name:")
            if not name_text:
                return
        try:
            conn = get_connection()
            cur = conn.cursor()
            # insert or update
            cur.execute("""
                INSERT INTO customers (shop_id, name, phone) VALUES (%s,%s,%s)
                ON DUPLICATE KEY UPDATE name=%s
            """, (shop_id, name_text, phone, name_text))
            conn.commit()
            conn.close()
            lbl_name.config(text=f"Name: {name_text}")
            tick_lbl.config(text="✅")
            messagebox.showinfo("Saved", "Customer saved.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    entry_phone.bind("<Return>", lookup_customer)
    btn_save_cust = tk.Button(top, text="Save Customer", bg=ACCENT1, fg=BUTTON_TEXT, command=save_customer)
    btn_save_cust.grid(row=0, column=4, padx=6)

    # -------- item entry ----------
    item_frame = tk.Frame(billing, bg=BG)
    item_frame.pack(pady=6)
    tk.Label(item_frame, text="Item ID / Barcode:", bg=BG, fg=TEXT).grid(row=0, column=0, padx=6)
    entry_item = tk.Entry(item_frame, width=30, bg=CARD, fg=TEXT, insertbackground=TEXT)
    entry_item.grid(row=0, column=1, padx=6)

    # -------- treeview ----------
    cols = ("sno", "item", "mrp", "price", "qty", "amount", "del")
    tree = ttk.Treeview(billing, columns=cols, show="headings", height=15)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=BG, fieldbackground=CARD, foreground=TEXT,
                    rowheight=24, borderwidth=0)
    style.map("Treeview", background=[("selected", ACCENT1)])
    headings = ["SNO", "ITEM", "MRP", "PRICE", "QTY", "AMOUNT", "DEL"]
    widths = [60, 360, 100, 100, 80, 120, 60]
    for c, h, w in zip(cols, headings, widths):
        tree.heading(c, text=h)
        tree.column(c, width=w, anchor="center")
    tree.pack(padx=12, pady=8, fill="both", expand=True)

    # internal bill list: list of (iid, product_id, qty, price, amount)
    bill_items = []
    sno = 1

    def add_item(event=None):
        nonlocal sno
        pid = entry_item.get().strip()
        if pid == "":
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT product_name, mrp, selling_price FROM products WHERE product_id=%s", (pid,))
            row = cur.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Error", "Invalid product id")
                return
            name, mrp, price = row
            qty = 1
            amount = float(price) * qty
            iid = tree.insert("", "end", values=(sno, name, mrp, price, qty, amount, "X"))
            bill_items.append([iid, pid, qty, float(price), float(amount)])
            sno += 1
            entry_item.delete(0, tk.END)
            calculate_total()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    entry_item.bind("<Return>", add_item)

    # single click delete on 'del' column
    def on_tree_click(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = tree.identify_column(event.x)  # '#7' style
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        # last column index = len(cols) => '#7'
        if col == f"#{len(cols)}":
            # remove from bill_items
            for i, rec in enumerate(bill_items):
                if rec[0] == row_id:
                    bill_items.pop(i)
                    break
            tree.delete(row_id)
            renumber()
            calculate_total()

    tree.bind("<ButtonRelease-1>", on_tree_click)

    def renumber():
        i = 1
        for iid in tree.get_children():
            vals = list(tree.item(iid, "values"))
            vals[0] = i
            tree.item(iid, values=vals)
            i += 1

    # -------- total & payment ----------
    bottom = tk.Frame(billing, bg=BG)
    bottom.pack(pady=8, fill="x")

    lbl_total = tk.Label(bottom, text="Total: 0", bg=BG, fg=TEXT, font=("Helvetica", 12, "bold"))
    lbl_total.pack(side="left", padx=12)

    entry_given = tk.Entry(bottom, width=16, bg=CARD, fg=TEXT, insertbackground=TEXT)
    entry_given.pack(side="left", padx=8)
    entry_given.insert(0, "")

    lbl_balance = tk.Label(bottom, text="Balance: 0", bg=BG, fg=TEXT)
    lbl_balance.pack(side="left", padx=8)

    def calculate_total():
        total = 0.0
        for iid in tree.get_children():
            try:
                val = float(tree.item(iid)["values"][5])
            except:
                val = 0.0
            total += val
        lbl_total.config(text=f"Total: {total:.2f}")
        return total

    def save_and_print(event=None):
        phone = entry_phone.get().strip()
        if phone == "":
            messagebox.showwarning("Warning", "Enter customer phone")
            return
        total = calculate_total()
        try:
            given = float(entry_given.get()) if entry_given.get().strip() != "" else 0.0
        except:
            given = 0.0
        balance = given - total
        lbl_balance.config(text=f"Balance: {balance:.2f}")

        # save to DB
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO sales (customer_phone, total_amount, created_at) VALUES (%s,%s,NOW())",
                        (phone, total))
            sale_id = cur.lastrowid
            for rec in bill_items:
                (_, pid, qty, price, amount) = rec
                cur.execute("INSERT INTO bill_items (sale_id, product_id, quantity, price, subtotal) VALUES (%s,%s,%s,%s,%s)",
                            (sale_id, pid, qty, price, amount))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        # make pdf
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="SRI KRISHNA DEPARTMENT STORE", ln=True, align='C')
        pdf.cell(200, 8, txt=f"Phone: {phone}", ln=True)
        pdf.cell(200, 8, txt=f"Total: {total:.2f}", ln=True)
        pdf.cell(200, 8, txt=f"Balance: {balance:.2f}", ln=True)
        fname = f"bill_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(fname)

        # send sms in background
        sms_text = f"Thanks! Your bill total is {total:.2f}. - {owner_name}"
        threading.Thread(target=send_sms, args=(phone, sms_text), daemon=True).start()

        messagebox.showinfo("Success", f"Bill saved & PDF created: {fname}")

    billing.bind("<Shift-Return>", save_and_print)

    # end of billing window

# -------------------------
# Animated square button - purple theme
# -------------------------
def animated_square(parent, text, cmd, size=120):
    btn = tk.Button(parent, text=text, command=cmd, fg=BUTTON_TEXT, bd=0, relief="raised")
    # dynamic styling
    palette = ["#7b6bff", "#9b84ff", "#bda8ff", "#7b6bff"]
    idx = {"i": 0}
    def tick():
        c = palette[idx["i"] % len(palette)]
        btn.config(bg=c, activebackground=c)
        idx["i"] += 1
        btn.after(300, tick)
    btn.config(width=int(size/10), height=int(size/40))
    tick()
    return btn

# -------------------------
# Dashboard
# -------------------------
def show_dashboard(shop_id, owner_name):
    dash = tk.Toplevel()
    dash.title("Dashboard")
    dash.configure(bg=BG)
    center_window(dash, 600, 420)

    header = tk.Label(dash, text=f"Welcome, {owner_name}", bg=BG, fg=TEXT, font=("Helvetica", 14, "bold"))
    header.pack(pady=8)

    frame = tk.Frame(dash, bg=BG)
    frame.pack(padx=12, pady=12)

    billing_btn = animated_square(frame, "BILLING", lambda: start_billing_app(shop_id, owner_name), size=140)
    billing_btn.grid(row=0, column=0, padx=12, pady=12)

    reports_btn = animated_square(frame, "REPORTS", lambda: messagebox.showinfo("Info", "Reports - coming soon"), size=140)
    reports_btn.grid(row=0, column=1, padx=12, pady=12)

    cust_btn = animated_square(frame, "CUSTOMERS", lambda: messagebox.showinfo("Info", "Customers - coming soon"), size=140)
    cust_btn.grid(row=1, column=0, padx=12, pady=12)

    exit_btn = animated_square(frame, "LOGOUT", lambda: dash.destroy(), size=140)
    exit_btn.grid(row=1, column=1, padx=12, pady=12)

# -------------------------
# Login window
# -------------------------
def login_window():
    root = tk.Tk()
    root.title("Login - Billing System")
    root.configure(bg=BG)
    center_window(root, 420, 300)

    lbl = tk.Label(root, text="SRI KRISHNA DEPARTMENT STORE", bg=BG, fg=TEXT, font=("Helvetica", 14, "bold"))
    lbl.pack(pady=12)

    frm = tk.Frame(root, bg=BG)
    frm.pack(pady=8)

    tk.Label(frm, text="Username:", bg=BG, fg=TEXT).grid(row=0, column=0, sticky="e", padx=6, pady=6)
    entry_user = tk.Entry(frm, bg=CARD, fg=TEXT, insertbackground=TEXT, width=26)
    entry_user.grid(row=0, column=1, pady=6)

    tk.Label(frm, text="Password:", bg=BG, fg=TEXT).grid(row=1, column=0, sticky="e", padx=6, pady=6)
    entry_pass = tk.Entry(frm, show="*", bg=CARD, fg=TEXT, insertbackground=TEXT, width=26)
    entry_pass.grid(row=1, column=1, pady=6)

    def do_login():
        username = entry_user.get().strip()
        password = entry_pass.get().strip()
        if username == "" or password == "":
            messagebox.showwarning("Warning", "Enter username & password.")
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT shop_id, owner_name FROM shops WHERE username=%s AND password=%s",
                        (username, password))
            row = cur.fetchone()
            conn.close()
            if row:
                shop_id, owner_name = row
                messagebox.showinfo("Welcome", f"Hello {owner_name}")
                root.destroy()
                show_dashboard(shop_id, owner_name)
            else:
                messagebox.showerror("Login failed", "Invalid credentials.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    btn_login = tk.Button(root, text="Login", bg=ACCENT1, fg=BUTTON_TEXT, width=20, command=do_login)
    btn_login.pack(pady=12)

    root.mainloop()

# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    login_window()
