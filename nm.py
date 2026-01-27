# app.py
# Theme 3: Dark Purple Gaming Theme
# Run: python3 app.py
# Requires: db_connection.get_connection(), fpdf, mysql-connector-python, pillow

import os
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from fpdf import FPDF
from db_connection import get_connection
import datetime
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from tkinter import messagebox
import mysql.connector
from tkinter import messagebox
from tkinter import ttk, messagebox



import json, os

SETTINGS_FILE = "app_settings.json"

def load_sms_state():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f).get("sms_enabled", False)
        except:
            return False
    return False

def save_sms_state(val):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"sms_enabled": val}, f)

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
# DB table ensure (best-effort)
# -------------------------
def ensure_tables_exist(shop_id):
    """Create minimal tables if they don't exist (safe - IF NOT EXISTS)."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # shops
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            shop_id INT AUTO_INCREMENT PRIMARY KEY,
            owner_name VARCHAR(255),
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)

        # customers
        cur.execute("""
        CREATE TABLE customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,

        shop_id INT NOT NULL,

        customer_name VARCHAR(255) NOT NULL,

        phone_1 VARCHAR(20) NOT NULL,
        phone_2 VARCHAR(20) DEFAULT NULL,

        address TEXT DEFAULT NULL,
        email VARCHAR(255) DEFAULT NULL,

        last_purchase_datetime DATETIME NULL,
        last_purchase_amount DOUBLE DEFAULT 0,

        lifetime_total DOUBLE DEFAULT 0,

        total_points INT DEFAULT 0,
        current_points INT DEFAULT 0,
        spent_points INT DEFAULT 0,

        status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP,

        UNIQUE (shop_id, phone_1),

        FOREIGN KEY (shop_id)
            REFERENCES shops(shop_id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB;



        """)

                # products (final version with all new columns)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            product_print_name VARCHAR(255),
            barcode1 VARCHAR(255),
            barcode2 VARCHAR(255),
            barcode3 VARCHAR(255),
            mrp_rate DOUBLE DEFAULT 0,
            purchase_rate DOUBLE DEFAULT 0,
            selling_price DOUBLE DEFAULT 0,
            sale_wholesale DOUBLE DEFAULT 0,
            brand VARCHAR(255),
            stock INT DEFAULT 0,
            gst_sgst DOUBLE DEFAULT 0,
            gst_cgst DOUBLE DEFAULT 0,
            hsn VARCHAR(50),
            hsn_code VARCHAR(50),
            category VARCHAR(255),
            company VARCHAR(255),
            other VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
        ) ENGINE=InnoDB
        """)

        # sales (match your DB: requires shop_id)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL,
            customer_id INT,
            total_amount DOUBLE NOT NULL,
            discount DOUBLE DEFAULT 0,
            payment_method VARCHAR(255),
            date_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)

        # bill_items (use product_id INT)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT,
            product_id INT,
            quantity INT,
            price DOUBLE,
            subtotal DOUBLE
        ) ENGINE=InnoDB
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        print("Ensure tables error:", e)

# -------------------------
# SMS placeholder (replace with Twilio or your provider)
# -------------------------
# -------------------------
# Simple SMS placeholder 
# -------------------------
def send_sms(phone, message):
    print(f"[SMS → {phone}]:\n{message}")



# -------------------------
# Printer helpers
# -------------------------
def shutil_which(cmd):
    from shutil import which
    return which(cmd)

def is_printer_connected_system():
    system = platform.system().lower()

    # Unix-like
    if system in ("linux", "darwin"):
        try:
            out = subprocess.check_output(["lpstat", "-p"], stderr=subprocess.STDOUT).decode(errors="ignore")
            # If lpstat returns nothing, no printers. If returns printers, text contains 'printer'
            return ("printer" in out.lower() or "device for" in out.lower() or "enabled" in out.lower())
        except Exception:
            return False

    # Windows
    if system == "windows":
        try:
            # prefer pywin32 if available
            import subprocess
            default = subprocess.GetDefaultPrinter()
            return bool(default)
        except Exception:
            # fallback: try powershell to list printers (best-effort)
            try:
                p = subprocess.run(["powershell", "-Command", "Get-Printer | Select-Object -First 1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return p.returncode == 0 and p.stdout.strip() != b""
            except Exception:
                return False

    return False

def send_pdf_to_printer(path):
    system = platform.system().lower()
    path_abs = os.path.abspath(path)

    if system == "windows":
        try:
            # This uses the shell "print" verb
            os.startfile(path_abs, "print")
            return True, "Sent to printer (Windows print)"
        except Exception as e:
            return False, f"Windows print error: {e}"
    else:
        try:
            # prefer lp then lpr
            if shutil_which("lp"):
                p = subprocess.run(["lp", path_abs], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif shutil_which("lpr"):
                p = subprocess.run(["lpr", path_abs], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                return False, "No lp/lpr installed"
            if p.returncode == 0:
                return True, "Sent to printer (lp/lpr)"
            else:
                err = p.stderr.decode(errors="ignore")
                return False, err or f"lp/lpr returned {p.returncode}"
        except Exception as e:
            return False, f"Print error: {e}"

# -------------------------
# Animated UI helpers
# -------------------------
def animated_icon_button(parent, img_path, cmd, size=130):
    try:
        img = Image.open(img_path)
        img = img.resize((80, 80), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
    except Exception as e:
        print("Image Load Error:", e)
        return tk.Button(parent, text="BILLING", command=cmd, bg=ACCENT1, fg=BUTTON_TEXT)

    btn = tk.Button(parent, image=tk_img, command=cmd, bd=0, relief="flat", bg="#ffffff", activebackground="#ffffff")
    btn.image = tk_img
    palette = ["#ffffff", "#f3f0ff", "#e6deff", "#ffffff"]
    idx = {"i": 0}
    def animate():
        c = palette[idx["i"] % len(palette)]
        btn.config(bg=c)
        idx["i"] += 1
        btn.after(350, animate)
    animate()
    btn.config(width=size, height=size)
    return btn

def animated_square(parent, text, cmd, size=120):
    btn = tk.Button(parent, text=text, command=cmd, fg=BUTTON_TEXT, bd=0, relief="raised")
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




def open_add_product_window(workspace, shop_id):
    import tkinter as tk
    from tkinter import ttk, messagebox

    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # =============================
    # CARD
    # =============================
    card = tk.Frame(workspace, bg="white",
                    highlightbackground=ACCENT, highlightthickness=3)
    card.pack(fill="both", expand=True, padx=20, pady=20)

    # =============================
    # TITLE
    # =============================
    tk.Label(card, text="Add Product",
             font=("Segoe UI", 22, "bold"),
             fg=ACCENT, bg="white").pack(pady=(15, 10))

    # =============================
    # MAIN FORM
    # =============================
    form = tk.Frame(card, bg="white")
    form.pack(fill="both", expand=True, pady=10)

    left = tk.Frame(form, bg="white")
    right = tk.Frame(form, bg="white")

    left.grid(row=0, column=0, padx=60, sticky="n")
    right.grid(row=0, column=1, padx=60, sticky="n")

    def make_entry(parent, label, r):
        tk.Label(
            parent,
            text=label,
            bg="white",
            fg=TITLE_COLOR,
            font=("Segoe UI", 11)
        ).grid(row=r, column=0, sticky="e", pady=6, padx=10)

        e = tk.Entry(
            parent,
            width=30,
            bg=WORK_BG,              # input background
            fg="#0F172A",            # ✅ DARK TEXT (VERY IMPORTANT)
            insertbackground="#0F172A",  # ✅ cursor color
            relief="solid",
            bd=1,
            font=("Segoe UI", 11)
        )
        e.grid(row=r, column=1, sticky="w", pady=6)
        return e


    # =============================
    # LEFT SIDE
    # =============================
    entry_name = make_entry(left, "Product Name", 0)
    entry_print = make_entry(left, "Product Print Name", 1)
    entry_barcode1 = make_entry(left, "Barcode 1", 2)
    entry_barcode2 = make_entry(left, "Barcode 2 (optional)", 3)
    entry_barcode3 = make_entry(left, "Barcode 3 (optional)", 4)
    entry_mrp_rate = make_entry(left, "MRP Rate", 5)
    entry_purchase = make_entry(left, "Purchase Rate", 6)


    # =============================
    # RIGHT SIDE
    # =============================
    entry_wholesale = make_entry(right, "Wholesale", 0)
    entry_selling = make_entry(right, "Selling Rate", 1)
    entry_stock = make_entry(right, "Stock", 2)
    entry_gst_sgst = make_entry(right, "GST SGST %", 3)
    entry_gst_cgst = make_entry(right, "GST CGST %", 4)
    entry_hsn = make_entry(right, "HSN Code", 5)

    # =============================
    # CATEGORY DROPDOWN
    # =============================
    tk.Label(right, text="Category", bg="white",
             fg=TITLE_COLOR, font=("Segoe UI", 11))\
        .grid(row=6, column=0, sticky="e", pady=6, padx=10)

    category_var = tk.StringVar()
    categories = [
        "All", "Bathing", "Biscuits", "Child Items", "Chocolates",
        "Cool Drinks", "Detergents", "Fairness", "General",
        "Masalas", "Medicals", "Milk Mixers", "Mosquito Coils",
        "Napkins", "Oils", "Perfumes", "Rice & Dhalls",
        "Salt", "School Needs", "Semeya", "Snacks",
        "Swamy Items", "Tooth Paste / Brush", "Vegetables"
    ]

    ttk.Combobox(right, textvariable=category_var,
                 values=categories, width=28,
                 state="readonly").grid(row=6, column=1, pady=6)
    
    entries = [
        entry_name,
        entry_print,
        entry_barcode1,
        entry_barcode2,
        entry_barcode3,
        entry_mrp_rate,
        entry_purchase,
        entry_wholesale,
        entry_selling,
        entry_stock,
        entry_gst_sgst,
        entry_gst_cgst,
        entry_hsn
    ]


    def focus_next(event, next_widget):
        next_widget.focus_set()
        return "break"   # 🔥 IMPORTANT: prevents default Enter behavior

    for i in range(len(entries) - 1):
        entries[i].bind(
            "<Return>",
            lambda e, nxt=entries[i+1]: focus_next(e, nxt)
        )


    # =============================
    # RADIO BUTTONS (GREY → SKY BLUE)
    # =============================
    radio_frame = tk.Frame(card, bg="white")
    radio_frame.pack(pady=20)

    type_var = tk.StringVar()

    def styled_radio(text, value):
        return tk.Radiobutton(
            radio_frame,
            text=text,
            variable=type_var,
            value=value,
            bg="white",
            fg="#6B7280",            # grey before
            selectcolor="#7DD3FC",   # sky blue after
            activebackground="white",
            activeforeground="#0F172A",
            font=("Segoe UI", 12, "bold"),
            indicatoron=True,
            padx=10
        )

    styled_radio("Company", "Company").pack(side="left", padx=25)
    styled_radio("Other", "Other").pack(side="left", padx=25)
    


    def get_categories_map():
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT category_id, category_name
            FROM categories
            WHERE status='Active'
            ORDER BY category_name
        """)

        rows = cur.fetchall()
        conn.close()

        # {"Oils": 5, "Biscuits": 2}
        return {r["category_name"]: r["category_id"] for r in rows}

    category_map = get_categories_map()

    def save_product():
        try:
            product_name = entry_name.get().strip()
            product_print = entry_print.get().strip()
            barcode1 = entry_barcode1.get().strip()
            barcode2 = entry_barcode2.get().strip()
            barcode3 = entry_barcode3.get().strip()

            mrp_rate = float(entry_mrp_rate.get() or 0)
            purchase_rate = float(entry_purchase.get() or 0)
            wholesale = float(entry_wholesale.get() or 0)
            selling_rate = float(entry_selling.get() or 0)
            stock = int(entry_stock.get() or 0)
            gst_sgst = float(entry_gst_sgst.get() or 0)
            gst_cgst = float(entry_gst_cgst.get() or 0)
            hsn = entry_hsn.get().strip()

            category_name = category_var.get()
            product_type = type_var.get()

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers")
            return

        if not product_name:
            messagebox.showwarning("Missing", "Product Name is required")
            return

        if not category_name:
            messagebox.showwarning("Missing", "Please select Category")
            return

        if category_name not in category_map:
            messagebox.showerror("Error", "Invalid Category selected")
            return

        category_id = category_map[category_name]   # 🔥 IMPORTANT

        if not product_type:
            messagebox.showwarning("Missing", "Please select Company / Other")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO products (
                    shop_id,
                    product_name,
                    product_print_name,
                    barcode1,
                    barcode2,
                    barcode3,
                    mrp_rate,
                    purchase_rate,
                    sale_wholesale,
                    selling_price,
                    stock,
                    gst_sgst,
                    gst_cgst,
                    hsn,
                    category_id,
                    type
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                shop_id,
                product_name,
                product_print,
                barcode1,
                barcode2,
                barcode3,
                mrp_rate,
                purchase_rate,
                wholesale,
                selling_rate,
                stock,
                gst_sgst,
                gst_cgst,
                hsn,
                category_id,     # ✅ FIXED
                product_type
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "✅ Product saved successfully")
            clear_form()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))


    # =============================
    # SAVE BUTTON (CENTER BOTTOM)
    # =============================
    tk.Button(
        card,
        text="SAVE PRODUCT",
        bg=ACCENT,
        fg="white",
        font=("Segoe UI", 13, "bold"),
        padx=60,
        pady=12,
        relief="flat",
        command=save_product
    ).pack(pady=20)

        # =============================
    # CLEAR FORM AFTER SAVE
    # =============================
    def clear_form():
        entries = [
            entry_name, entry_print,
            entry_barcode1, entry_barcode2, entry_barcode3,
            entry_mrp_rate, entry_purchase,
            entry_wholesale, entry_selling, entry_stock,
            entry_gst_sgst, entry_gst_cgst, entry_hsn
        ]

        for e in entries:
            e.delete(0, tk.END)

        category_var.set("")
        type_var.set("")
        entry_name.focus_set()

  
blink_running = False
inline_edit_active = False
editing_from_icon = False
editing_row = None
edit_entries = {}
bill_window_alive = False
bill_tree = None
current_customer = {
    "id": None,
    "name": "",
    "phone": "",
    "address": "",
    "points": 0
}


import tkinter as tk
from tkinter import ttk
import subprocess
from tkinter import messagebox


WORK_BG = "#F8FAFC"
ACCENT = "#3B82F6"
TITLE_COLOR = "#1E293B"
SELECTED_COLOR = "#BFDBFE"
bill_window_alive = False


# -------------------------------------------------------------------
entry_bill_no = None
entry_customer_name = None
entry_customer_phone = None
entry_total = None
entry_given = None
selected_customer_id = None
# ------------------------------------------
def open_billing_window(workspace,shop_id):
    workspace.unbind_all("<MouseWheel>")
    workspace.unbind_all("<Button-4>")
    workspace.unbind_all("<Button-5>")
    root = workspace.winfo_toplevel()
    bill_no = entry_bill_no.get().strip()

    customer_id = selected_customer_id      # confirm this exists
    customer_name = entry_customer_name.get().strip()
    customer_phone = entry_customer_phone.get().strip()

    total = float(entry_total.get())
    given = float(entry_given.get())


    # ❗ REMOVE EVERYTHING INSIDE WORKSPACE
    for child in workspace.winfo_children():
        child.destroy()

    # ✅ SINGLE ROOT CONTAINER
    content = tk.Frame(workspace, bg=WORK_BG)
    content.pack(fill="both", expand=True)

    # optional resize support
    content.rowconfigure(0, weight=1)
    content.columnconfigure(0, weight=1)

    # ✅ MAIN CARD (ONLY ONE BILL WINDOW)
    card = tk.Frame(
        content,
        bg="white",
        highlightbackground=ACCENT,
        highlightthickness=3
    )
    card.pack(fill="both", expand=True, padx=20, pady=20)
    root = workspace.winfo_toplevel()
    root = workspace.winfo_toplevel()
    global bill_window_alive, bill_tree
    bill_window_alive = True


    card.pack(fill="both", expand=True, padx=20, pady=20)

    toolbar = tk.Frame(card, bg="#F1F5F9")
    toolbar.pack(fill="x", padx=5, pady=(10, 5))

    payment_mode = tk.StringVar(value="")  # Cash / Credit

    top_frame = tk.Frame(card, bg="white")
    top_frame.pack(fill="x", padx=0, pady=0)
   


    def field(parent, text, w):
        f = tk.Frame(parent, bg="white")
        tk.Label(f, text=text, bg="white", fg=TITLE_COLOR, font=("Segoe UI", 11)).pack(anchor="w")
        e = tk.Entry(f, width=w, bg=WORK_BG, fg="#0F172A", relief="solid", bd=1, font=("Segoe UI", 11))
        e.pack()
        f.pack(side="left", padx=12)
        return e

    def clear_top():
        for w in top_frame.winfo_children():
            w.destroy()

    def show_product_fields():
        clear_top()
        global entry_barcode, entry_pid, entry_qty, edit_mode, edit_item

        edit_mode = False
        edit_item = None

        entry_barcode = field(top_frame, "Barcode / Name", 22)
        entry_pid     = field(top_frame, "Product ID", 14)
        entry_qty     = field(top_frame, "Quantity", 10)

        entry_barcode.bind("<Return>", lambda e: add_product("barcode"))
        entry_pid.bind("<Return>", lambda e: add_product("pid"))
        entry_qty.bind("<Return>", lambda e: add_product("barcode"))

        entry_barcode.focus_set()



    def show_customer_fields():
        clear_top()

        global entry_cid, entry_cname, entry_phone, entry_points, entry_address

        entry_phone   = field(top_frame, "Phone", 16)
        entry_cname   = field(top_frame, "Customer Name", 18)
        entry_cid     = field(top_frame, "Customer ID", 14)
        entry_address = field(top_frame, "Address", 18)
        entry_points  = field(top_frame, "Current Points", 14)

        # 🔥 ENTER triggers same search
        entry_phone.bind("<Return>", lambda e: search_customer())
        entry_cname.bind("<Return>", lambda e: search_customer())
        entry_cid.bind("<Return>", lambda e: search_customer())

        entry_phone.focus_set()



        

    def search_customer():
        cid   = entry_cid.get().strip()
        phone = entry_phone.get().strip()
        name  = entry_cname.get().strip()

        if not cid and not phone and not name:
            return

        conn = get_connection()
        cur = conn.cursor()

        row = None

       # 1️⃣ Search by Customer ID
        if cid:
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, current_points
                FROM customers
                WHERE shop_id=%s AND customer_id=%s AND status='ACTIVE'
                LIMIT 1
            """, (shop_id, cid))
            row = cur.fetchone()

        # 2️⃣ Search by Phone
        elif phone:
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, current_points
                FROM customers
                WHERE shop_id=%s AND phone_1=%s AND status='ACTIVE'
                LIMIT 1
            """, (shop_id, phone))
            row = cur.fetchone()

        # 3️⃣ Search by Name
        elif name:
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, current_points
                FROM customers
                WHERE shop_id=%s
                AND customer_name LIKE %s
                AND status='ACTIVE'
                ORDER BY customer_id DESC
                LIMIT 1
            """, (shop_id, f"%{name}%"))
            row = cur.fetchone()

        conn.close()

        if row:
            fill_customer_fields(row)
            return

        # ---- NOT FOUND ----
        if phone:
            open_add_customer_popup(phone)
        else:
            messagebox.showinfo("Not Found", "Customer not found")


            

        if row:
            fill_customer_fields(row)
        else:
            open_add_customer_popup(phone)
    
    def fill_customer_fields(row):
        entry_cid.delete(0, tk.END)
        entry_cname.delete(0, tk.END)
        entry_phone.delete(0, tk.END)
        entry_address.delete(0, tk.END)
        entry_points.delete(0, tk.END)

        entry_cid.insert(0, row[0])
        entry_cname.insert(0, row[1])
        entry_phone.insert(0, row[2])
        entry_address.insert(0, row[3] or "")
        entry_points.insert(0, row[4] or 0)


    from tkinter import messagebox

    def open_add_customer_popup(phone):
        parent = workspace.winfo_toplevel()

        win = tk.Toplevel(parent)
        win.title("Add Customer")
        win.resizable(False, False)
        win.configure(bg="white")

        # =========================
        # CENTER WINDOW
        # =========================
        win.update_idletasks()
        popup_w, popup_h = 380, 260

        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        x = px + (pw // 2) - (popup_w // 2)
        y = py + (ph // 2) - (popup_h // 2)

        win.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
        win.focus_force()

        # =========================
        # SAFE CLOSE
        # =========================
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.bind("<Escape>", lambda e: win.destroy())

        # =========================
        # CARD UI
        # =========================
        card = tk.Frame(win, bg="white",
                        highlightbackground=ACCENT,
                        highlightthickness=2)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(
            card,
            text="Add Customer",
            bg="white",
            fg=ACCENT,
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(4, 14))

        def row(label, default=""):
            f = tk.Frame(card, bg="white")
            f.pack(fill="x", pady=6)

            tk.Label(
                f, text=label, width=10, anchor="w",
                bg="white", fg="#000000",
                font=("Segoe UI", 9)
            ).pack(side="left")

            e = tk.Entry(f, font=("Segoe UI", 9),
                        bg="white", fg="#000000")
            e.pack(side="left", fill="x", expand=True)
            e.insert(0, default)
            return e

        e_phone = row("Phone", phone)
        e_phone.config(state="readonly")

        e_name = row("Name")
        e_addr = row("Address")

        # =========================
        # ENTER KEY FLOW 🔥
        # =========================
        e_name.bind("<Return>", lambda e: e_addr.focus_set())
        e_addr.bind("<Return>", lambda e: save_customer())

        e_name.focus_set()

        # =========================
        # SAVE LOGIC
        # =========================
        def save_customer():
            name = e_name.get().strip()
            addr = e_addr.get().strip()

            if not phone or not name:
                messagebox.showwarning(
                    "Missing Details",
                    "Please fill Phone and Name"
                )
                return

            conn = get_connection()
            cur = conn.cursor()

            # INSERT CUSTOMER
            cur.execute("""
                INSERT INTO customers
                (shop_id, customer_name, phone_1, address, status)
                VALUES (%s,%s,%s,%s,'ACTIVE')
            """, (
                shop_id,
                name,
                phone,
                addr
            ))

            customer_id = cur.lastrowid   # ✅ VERY IMPORTANT

            conn.commit()

            # 🔥 FETCH SAME CUSTOMER IMMEDIATELY
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, total_points
                FROM customers
                WHERE customer_id = %s
            """, (customer_id,))

            row = cur.fetchone()
            conn.close()

            messagebox.showinfo("Success", "Customer saved successfully")

            win.destroy()

            # ✅ DIRECTLY FILL BILLING FIELDS
            if row:
                fill_customer_fields(row)

        tk.Button(
            card,
            text="Save",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            width=12,
            command=save_customer
        ).pack(pady=14)

# customer  details show until  bill print
    # =========================
    # GLOBAL STATE
    # =========================
    current_customer = {
        "id": None,
        "name": "",
        "phone": "",
        "address": "",
        "points": 0
    }


    def show_customer_fields():
        """
        Customer button click:
        - UI recreate pannum
        - Global current_customer data irundha fill pannum
        """

        clear_top()          # 🔥 recreate UI safely
        create_customer_fields()

        if current_customer["id"] is None:
            return   # no customer yet

        entry_phone.insert(0, current_customer["phone"])
        entry_cname.insert(0, current_customer["name"])
        entry_cid.insert(0, current_customer["id"])
        entry_address.insert(0, current_customer["address"])
        entry_points.insert(0, current_customer["points"])

    def create_customer_fields():
        global entry_cid, entry_cname, entry_phone, entry_points, entry_address

        entry_phone   = field(top_frame, "Phone", 16)
        entry_cname   = field(top_frame, "Customer Name", 18)
        entry_cid     = field(top_frame, "Customer ID", 14)
        entry_address = field(top_frame, "Address", 18)
        entry_points  = field(top_frame, "Current Points", 14)

        entry_phone.bind("<Return>", lambda e: search_customer())
        entry_cname.bind("<Return>", lambda e: search_customer())
        entry_cid.bind("<Return>", lambda e: search_customer())



    def fill_customer_fields(row):
        current_customer["id"] = row[0]
        current_customer["name"] = row[1]
        current_customer["phone"] = row[2]
        current_customer["address"] = row[3] or ""
        current_customer["points"] = row[4] or 0

        show_customer_fields()



    # =========================
    # CLEAR FUNCTIONS
    # =========================
    def clear_customer_fields():
        for e in (entry_cid, entry_cname, entry_phone, entry_address, entry_points):
            e.delete(0, tk.END)

    def clear_product_fields():
        entry_barcode.delete(0, tk.END)
        entry_pid.delete(0, tk.END)
        entry_qty.delete(0, tk.END)
        entry_barcode.focus_set()


    # =========================
    # PRODUCT ADD
    # =========================
    def add_product():
        # 🚫 customer select pannama product allow panna koodaadhu
        if current_customer["id"] is None:
            messagebox.showwarning("Select Customer", "Please select customer first")
            return

        pid = entry_pid.get().strip()
        barcode = entry_barcode.get().strip()
        qty = entry_qty.get().strip()

        qty = int(qty) if qty else 1

        conn = get_connection()
        cur = conn.cursor()

        if pid:
            cur.execute("""
                SELECT product_id, product_name, selling_price
                FROM products
                WHERE product_id=%s AND status='ACTIVE'
            """, (pid,))
        else:
            cur.execute("""
                SELECT product_id, product_name, selling_price
                FROM products
                WHERE barcode=%s AND status='ACTIVE'
            """, (barcode,))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "Product not found")
            return

        pid, name, price = row
        total = qty * price

        bill_tree.insert(
            "", "end",
            values=(pid, name, price, qty, total)
        )

        clear_product_fields()   # ✅ ONLY PRODUCT CLEAR




    # =========================
    # Cash / Credit toggle with tick
    # =========================
    def toggle_payment(mode):
        if payment_mode.get() == mode:
            payment_mode.set("")
        else:
            payment_mode.set(mode)
        update_payment_buttons()

    def update_payment_buttons():
        if payment_mode.get() == "Cash":
            cash_btn.config(bg=SELECTED_COLOR, text="✔ Cash")
            credit_btn.config(bg="#E5E7EB", text="Credit")
        elif payment_mode.get() == "Credit":
            credit_btn.config(bg=SELECTED_COLOR, text="✔ Credit")
            cash_btn.config(bg="#E5E7EB", text="Cash")
        else:
            cash_btn.config(bg="#E5E7EB", text="Cash")
            credit_btn.config(bg="#E5E7EB", text="Credit")

    # =========================
    # Toolbar buttons sequence
    # =========================
    btn_product = tk.Button(toolbar, text="Product", bg="#E5E7EB", fg="#0F172A",
                            font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                            padx=14, pady=4, command=show_product_fields)
    btn_product.pack(side="left", padx=4)

    btn_customer = tk.Button(toolbar, text="Customer", bg="#E5E7EB", fg="#0F172A",
                             font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                             padx=14, pady=4, command=show_customer_fields)
    btn_customer.pack(side="left", padx=4)


    # 🔥 EDIT BUTTON (CENTER)
    btn_customer = tk.Button(
        toolbar, text="Customer",
        bg="#E5E7EB", fg="#0F172A",
        font=("Segoe UI", 10, "bold"),
        relief="solid", bd=1,
        padx=14, pady=4,
        command=show_customer_fields   # 🔥 NOT recreate
    )
    edit_btn = tk.Button(toolbar, text="Edit", bg="#E5E7EB", fg="#0F172A",
                         font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                         padx=14, pady=4, command=lambda:None)
    edit_btn.pack(side="left", padx=4)

    cash_btn = tk.Button(toolbar, text="Cash", bg="#E5E7EB", fg="#0F172A",
                         font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                         padx=14, pady=4, command=lambda: toggle_payment("Cash"))
    cash_btn.pack(side="left", padx=4)

    credit_btn = tk.Button(toolbar, text="Credit", bg="#E5E7EB", fg="#0F172A",
                           font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                           padx=14, pady=4, command=lambda: toggle_payment("Credit"))
    credit_btn.pack(side="left", padx=4)

    top_row = tk.Frame(card, bg="white")
    top_row.pack(fill="x", padx=20, pady=(5, 10))

    spacer = tk.Frame(toolbar, bg="#F1F5F9")
    spacer.pack(side="left", expand=True, fill="x")

    status_frame = tk.Frame(toolbar, bg="#F1F5F9")
    status_frame.pack(side="right", padx=(0, 6))



    right_status = tk.Frame(top_row, bg="white")
    right_status.pack(side="right", anchor="e", padx=10)


    

    import socket

    def is_network_connected():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    net_canvas = tk.Canvas(
        status_frame,
        width=28,
        height=28,
        bg="#F1F5F9",
        highlightthickness=0
    )
    net_canvas.pack(side="left", padx=(0, 8))

    square = net_canvas.create_rectangle(2, 2, 26, 26, outline="")
    icon = net_canvas.create_text(
        14, 14,
        font=("Segoe UI", 12, "bold")
    )

    def update_network_status():
        if is_network_connected():
            net_canvas.itemconfig(square, fill="#22c55e")
            net_canvas.itemconfig(icon, text="✔", fill="white")
        else:
            net_canvas.itemconfig(square, fill="#ef4444")
            net_canvas.itemconfig(icon, text="✖", fill="white")

        net_canvas.after(3000, update_network_status)

    update_network_status()




    # -------------------------------
    # 🔘 MODERN TOGGLE (BORDER FIXED)
    # -------------------------------
    sms_enabled = load_sms_state()



    toggle = tk.Canvas(
        status_frame,
        width=90,
        height=30,
        bg="#F1F5F9",
        highlightthickness=0
    )
    toggle.pack(side="left")

    bg = toggle.create_rectangle(
        1, 1, 89, 29,
        outline="#9ca3af",
        fill="#e5e7eb"
    )

    knob = toggle.create_oval(
        4, 4, 26, 26,
        fill="white",
        outline="#9ca3af"
    )

    label = toggle.create_text(
        45, 15,
        font=("Segoe UI", 9, "bold")
    )

    def draw_toggle():
        if sms_enabled:
            toggle.itemconfig(bg, fill="#2563eb")
            toggle.coords(knob, 62, 4, 86, 26)
            toggle.itemconfig(label, text="ON", fill="white")
        else:
            toggle.itemconfig(bg, fill="#e5e7eb")
            toggle.coords(knob, 4, 4, 26, 26)
            toggle.itemconfig(label, text="OFF", fill="#111827")

    



    def toggle_sms(event=None):
        nonlocal sms_enabled
        sms_enabled = not sms_enabled
        save_sms_state(sms_enabled)

        if sms_enabled:
            enable_sms_sending()
        else:
            disable_sms_sending()

        draw_toggle()

    toggle.bind("<Button-1>", toggle_sms)
    draw_toggle()


    # -------------------------------
    # SMS METHODS (YOUR REAL LOGIC HERE)
    # -------------------------------
    def enable_sms_sending():
        print("✅ SMS SENDING ENABLED")

    def disable_sms_sending():
        print("❌ SMS SENDING DISABLED")
    
    # =============================
    # TABLE FRAME
    # =============================
    table_frame = tk.Frame(card, bg="white", bd=1, relief="solid")
    table_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=(10, 0)
    )

    # 🔥 IMPORTANT: stop auto resize
    table_frame.pack_propagate(False)

    # =============================
    # INNER CONTAINER (FOR SCROLL)
    # =============================
    table_container = tk.Frame(table_frame, bg="white")
    table_container.pack(fill="both", expand=True)

    # =============================
    # TREEVIEW
    # =============================
    columns = ("no", "pid", "name", "mrp", "price", "qty", "amount", "delete", "edit")

    tree = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings"
    )

    headings = {
        "no": "No",
        "pid": "P.ID",
        "name": "Name",
        "mrp": "MRP",
        "price": "Price",
        "qty": "Qty",
        "amount": "Amount",
        "delete": "Delete",
        "edit": "Edit"
    }

    for c in columns:
        tree.heading(c, text=headings[c])
        tree.column(c, anchor="center", width=90)

    tree.column("name", width=220)

    # =============================
    # SCROLLBAR
    # =============================
    table_scroll = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=tree.yview
    )

    tree.configure(yscrollcommand=table_scroll.set)

    # =============================
    # PACK ORDER (VERY IMPORTANT)
    # =============================
    tree.pack(side="left", fill="both", expand=True)
    table_scroll.pack(side="right", fill="y")


    # =============================
    # TABLE CLICK LOGIC
    # =============================
    def on_table_click(event):
        global inline_edit_active, editing_from_icon

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not row_id:
            return

        values = list(tree.item(row_id, "values"))
        col_index = int(col.replace("#", "")) - 1
        cell_value = values[col_index]

        # ❌ DELETE (disable during inline edit)
        if cell_value == "❌":
            if inline_edit_active:
                return
            tree.delete(row_id)
            refresh_row_numbers()
            calculate_total()
            return

        # ✏ EDIT BUTTON CLICK
        if cell_value == "✏":
            inline_edit_active = True        # 🔒 BLOCK PANEL
            editing_from_icon = True
            tree.selection_set(row_id)
            start_inline_edit(row_id)
            return


    def start_inline_edit(row_id):
        global editing_row, edit_entries, inline_edit_active

        inline_edit_active = True
        editing_row = row_id
        edit_entries = {}
        values = list(tree.item(row_id, "values"))

        for col_index in range(7):  # No → Amount
            bbox = tree.bbox(row_id, f"#{col_index+1}")
            if not bbox:
                continue

            x, y, w, h = bbox
            e = tk.Entry(tree, font=("Segoe UI", 10))
            e.place(x=x, y=y, width=w, height=h)
            e.insert(0, values[col_index])
            e.focus()

            e.bind("<Return>", save_inline_edit)
            e.bind("<FocusOut>", save_inline_edit)

            edit_entries[col_index] = e


    def save_inline_edit(event=None):
        global editing_row, edit_entries, inline_edit_active, editing_from_icon

        if not editing_row:
            return

        values = list(tree.item(editing_row, "values"))

        for i, e in edit_entries.items():
            values[i] = e.get()
            e.destroy()

        try:
            price = float(values[4])
            qty = int(values[5])
            values[6] = round(price * qty, 2)
        except:
            values[6] = 0

        values[7] = "❌"
        values[8] = "✏"

        tree.item(editing_row, values=values)

        editing_row = None
        edit_entries = {}
        inline_edit_active = False      # 🔓 UNLOCK PANEL
        editing_from_icon = False

        calculate_total()

    def on_row_select(event=None):
        global inline_edit_active

        if inline_edit_active:
            return    # 🚫 STOP TOP PANEL WHEN ✏ EDITING

        sel = tree.selection()
        if not sel:
            return

        item = sel[0]
        vals = tree.item(item, "values")

        clear_top()

        global entry_pid, entry_barcode, entry_qty
        entry_pid = field(top_frame, "Product ID", 14)
        entry_barcode = field(top_frame, "Product Name", 22)
        entry_qty = field(top_frame, "Quantity", 10)

        entry_pid.insert(0, vals[1])
        entry_barcode.insert(0, vals[2])
        entry_qty.insert(0, vals[5])

        entry_qty.focus_set()
        entry_qty.bind("<KeyRelease>", live_qty_update)
        entry_qty.bind("<Return>", finish_qty_edit)

    def refresh_row_numbers():
        for i, item in enumerate(tree.get_children(), start=1):
            vals = list(tree.item(item, "values"))
            vals[0] = i
            tree.item(item, values=vals)


    def calculate_total():
        total = 0
        for item in tree.get_children():
            vals = tree.item(item, "values")
            total += float(vals[6])

        entry_total.delete(0, tk.END)
        entry_total.insert(0, f"{total:.2f}")


    # ✅ BIND MUST BE LAST
    tree.bind("<Button-1>", on_table_click)

    # default fields
    show_product_fields()


    def center_window(win, parent):
        win.update_idletasks()

        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        ww = win.winfo_width()
        wh = win.winfo_height()

        x = px + (pw // 2) - (ww // 2)
        y = py + (ph // 2) - (wh // 2)

        win.geometry(f"+{x}+{y}")


    # ===============================
    # DB CONNECTION
    # ===============================
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="billing",
            password="billing123",
            database="billing_db"
        )

    # ===============================
    # FETCH PRODUCT
    # ===============================
    def fetch_product(by):
        db = get_db()
        cur = db.cursor(dictionary=True)

        if by == "barcode":
            val = entry_barcode.get().strip()

            # ❌ EMPTY → STOP
            if not val:
                db.close()
                return None

            cur.execute("""
                SELECT *
                FROM products
                WHERE barcode1=%s
                OR barcode2=%s
                OR barcode3=%s
                OR product_name LIKE %s
                LIMIT 1
            """, (val, val, val, f"%{val}%"))

        else:
            pid = entry_pid.get().strip()

            # ❌ EMPTY → STOP
            if not pid:
                db.close()
                return None

            cur.execute(
                "SELECT * FROM products WHERE product_id=%s",
                (pid,)
            )

        row = cur.fetchone()
        db.close()
        return row
    
    def find_existing_row(product_id):
        for item in tree.get_children():
            vals = tree.item(item, "values")
            if str(vals[1]) == str(product_id):
                return item
        return None




    # ===============================
    # ADD PRODUCT TO BILL TABLE
    # ===============================
   

    def add_product(by):
        product = fetch_product(by)
 # ✅ ONLY product clear


        # ❌ PRODUCT NOT FOUND
        if not product:
            ask_add_product()
            return

        try:
            qty = int(entry_qty.get() or 1)
        except:
            qty = 1

        price = float(product["selling_price"])
        existing = find_existing_row(product["product_id"])

        if existing:
            vals = list(tree.item(existing, "values"))
            vals[5] = int(vals[5]) + qty
            vals[6] = vals[5] * price
            tree.item(existing, values=vals)
        else:
            tree.insert("", "end", values=(
                len(tree.get_children()) + 1,   # row_no
                product["product_id"],          # pid
                product["product_name"],        # name
                product["mrp_rate"],            # mrp
                price,                          # price
                qty,                            # qty
                qty * price,                    # amount
                "❌",                            # delete
                            "✏"                             # edit
            ))


        entry_barcode.delete(0, tk.END)
        entry_pid.delete(0, tk.END)
        entry_qty.delete(0, tk.END)
        entry_barcode.focus_set()
        recalc_total()


    def open_add_product_minimized(root, shop_id):

        if hasattr(root, "add_product_win") and root.add_product_win.winfo_exists():
            root.add_product_win.deiconify()
            root.add_product_win.lift()
            return

        win = tk.Toplevel(root)
        root.add_product_win = win

        win.title("Add Product")
        win.geometry("800x500")
        win.minsize(800, 500)
        win.transient(root)

        # ❌ DO NOT USE grab_set()

        topbar = tk.Frame(win, bg="#1E293B", height=36)
        topbar.pack(fill="x")

        tk.Label(
            topbar,
            text="Add Product",
            bg="#1E293B",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=10)

        tk.Button(topbar, text="—", command=win.withdraw,
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)

        tk.Button(topbar, text="▢", command=lambda: win.state("zoomed"),
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)

        tk.Button(topbar, text="✕", command=win.destroy,
                bg="#EF4444", fg="white", width=3).pack(side="right", padx=4)

        container = tk.Frame(win)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scroll.set,
                        xscrollcommand=h_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        open_add_product_window(scroll_frame, shop_id)

  

        # =============================
        # CUSTOM TOP BAR
        # =============================
        topbar = tk.Frame(win, bg="#1E293B", height=36)
        topbar.pack(fill="x")

        tk.Label(
            topbar,
            text="Add Product",
            bg="#1E293B",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=10)

        def hide_win():
            win.withdraw()

        def maximize_win():
            win.state("zoomed")

        def close_win():
            win.destroy()

        tk.Button(topbar, text="—", command=hide_win,
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)
        tk.Button(topbar, text="▢", command=maximize_win,
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)
        tk.Button(topbar, text="✕", command=close_win,
                bg="#EF4444", fg="white", width=3).pack(side="right", padx=4)

        # =============================
        # SCROLLABLE BODY
        # =============================
        container = tk.Frame(win)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scroll.set,
                        xscrollcommand=h_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        # 🔥 IMPORTANT: load your EXISTING add product UI here
        open_add_product_window(scroll_frame, shop_id)

        center_window(win, root)



    def ask_add_product():
        popup = tk.Toplevel(root)
        popup.title("Product Not Found")
        popup.geometry("360x160")
        popup.resizable(False, False)
        popup.transient(root)
        popup.grab_set()

        tk.Label(
            popup,
            text="❌ Product not found",
            font=("Segoe UI", 12, "bold"),
            pady=25
        ).pack()

        tk.Label(
            popup,
            text="Please add product first",
            font=("Segoe UI", 10)
        ).pack()

        def close_popup(event=None):
            popup.destroy()
            entry_barcode.focus_set()

        tk.Button(
            popup,
            text="OK",
            width=12,
            bg="#2563EB",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=close_popup
        ).pack(pady=15)

        # 🔥 Enter / Esc key support
        popup.bind("<Return>", close_popup)
        popup.bind("<Escape>", close_popup)

        center_window(popup, root)

    
    def on_barcode_enter(event=None):
        if entry_barcode.get().strip() == "":
            return
        add_product("barcode")

    def on_pid_enter(event=None):
        if entry_pid.get().strip() == "":
            return
        add_product("pid")
    
  
    

    def confirm_qty_edit(event=None):
        global edit_mode, edit_item
        edit_mode = False
        edit_item = None
        show_product_fields()


    def recalc_total():
        total = 0.0
        for item in tree.get_children():
            vals = tree.item(item, "values")
            try:
                total += float(vals[6])  # amount column
            except:
                pass

        entry_total.delete(0, tk.END)
        entry_total.insert(0, f"{total:.2f}")

    # ===============================
    # LIVE QTY UPDATE
    # ===============================
    def live_qty_update(event=None):
        sel = tree.selection()
        if not sel:
            return
        try:
            qty = int(entry_qty.get())
        except:
            return

        item = sel[0]
        vals = list(tree.item(item, "values"))
        vals[5] = qty
        vals[6] = qty * float(vals[4])
        tree.item(item, values=vals)
        calculate_total()   # 🔥 TOTAL LIVE UPDATE




    tree.column("name", width=220)
    tree.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", on_row_select)



    bottom = tk.Frame(card, bg="white")
    bottom.pack(side="bottom", fill="x", padx=20, pady=12)


    def finish_qty_edit(event=None):
        calculate_total()              # 🔥 FINAL TOTAL UPDATE
        tree.selection_remove(tree.selection())
        show_product_fields()          # back to barcode / pid / qty
                # back to add product mode
  

    def total_box(parent, text):
        f = tk.Frame(parent, bg="white")

        lbl = tk.Label(
            f,
            text=text,
            bg="white",
            fg=TITLE_COLOR,
            font=("Segoe UI", 12, "bold")
        )
        lbl.pack(anchor="e")

        e = tk.Entry(
            f,
            width=16,
            font=("Segoe UI", 12, "bold"),
            bg="#BDC9D4",
            fg="black",
            relief="solid",
            bd=1,
            justify="right"
        )
        e.pack()

        return f, lbl, e

    box_total,  lbl_total,  entry_total  = total_box(bottom, "TOTAL")
    box_give,   lbl_give,   entry_give   = total_box(bottom, "Customer Give")
    box_return, lbl_return, entry_return = total_box(bottom, "Return")

    box_return.pack(side="right", padx=12)
    box_give.pack(side="right", padx=12)
    box_total.pack(side="right", padx=12)

    def validate_given_against_total(event=None):
        try:
            total_text = entry_total.get().strip()
            give_text = entry_give.get().strip()

            if total_text == "" or give_text == "":
                stop_blink(entry_give, lbl_give)
                return

            total = float(total_text)
            given = float(give_text)

            if given < total:
                start_blink(entry_give, lbl_give)
            else:
                stop_blink(entry_give, lbl_give)

        except ValueError:
            start_blink(entry_give, lbl_give)

    # =============================
    # BLINK ERROR
    # =============================
    def start_blink(entry, label):
        global blink_running

        if blink_running:
            return  # already blinking

        blink_running = True

        def blink():
            if not blink_running:
                entry.config(bg="#D4D5E3")
                label.config(fg=TITLE_COLOR)
                return

            current = entry.cget("bg")
            new = "red" if current != "red" else "#CBD3DC"

            entry.config(bg=new)
            label.config(fg=new)

            entry.after(300, blink)

        blink()


    def stop_blink(entry, label):
        global blink_running
        blink_running = False
        entry.config(bg="#C8C8DC")
        label.config(fg=TITLE_COLOR)




    # =============================
    # CALCULATE RETURN
    # =============================
    def calculate_return(event=None):
        try:
            total_text = entry_total.get().strip()
            give_text = entry_give.get().strip()

            if total_text == "" or give_text == "":
                entry_return.delete(0, tk.END)
                stop_blink(entry_give, lbl_give)
                return

            total = float(total_text)
            given = float(give_text)

            # ❌ INVALID → BLINK
            if given < 0 or given < total:
                entry_return.delete(0, tk.END)
                start_blink(entry_give, lbl_give)
                return

            # ✅ VALID (THIS IS WHAT YOU WANT)
            # total == given  OR  given > total
            stop_blink(entry_give, lbl_give)

            ret = given - total
            entry_return.delete(0, tk.END)
            entry_return.insert(0, f"{ret:.2f}")
            entry_return.focus_set()

        except ValueError:
            entry_return.delete(0, tk.END)
            start_blink(entry_give, lbl_give)

    entry_total.bind("<Return>", lambda e: entry_give.focus_set())

    entry_give.bind("<KeyRelease>", calculate_return)
    entry_give.bind("<Return>", calculate_return)
    entry_total.bind("<KeyRelease>", validate_given_against_total)
    entry_total.bind("<FocusOut>", validate_given_against_total)


    entry_total.focus_set()

    def is_printer_connected():
        try:
            out = subprocess.check_output(["lpstat", "-r"], stderr=subprocess.STDOUT)
            text = out.decode().lower()

            # scheduler must be running
            if "scheduler is running" not in text:
                return False

            # check at least one enabled printer
            out2 = subprocess.check_output(["lpstat", "-p"], stderr=subprocess.STDOUT)
            lines = out2.decode().lower().splitlines()

            for line in lines:
                if "enabled" in line:
                    return True

            return False
        except:
            return False
    

    def save_and_print(event=None):

        # -----------------------------
        # 1️⃣ PRODUCT CHECK
        # -----------------------------
        if len(tree.get_children()) == 0:
            messagebox.showwarning("Add Product", "Please add product")
            return

        # -----------------------------
        # 2️⃣ TOTAL / GIVEN / RETURN
        # -----------------------------
        try:
            total = float(entry_total.get().strip())
            given = float(entry_give.get().strip())
            ret = float(entry_return.get().strip())
        except:
            messagebox.showwarning("Missing Amount", "Enter Total / Given / Return")
            return

        if total <= 0:
            messagebox.showwarning("Invalid Bill", "Bill total is zero")
            return

        if given < total:
            messagebox.showwarning("Payment Incomplete", "Given amount is less than total")
            return

        # -----------------------------
        # 3️⃣ COLLECT ITEMS
        # -----------------------------
        items = []
        bill_total = 0

        for row in tree.get_children():
            vals = tree.item(row, "values")

            pid = vals[1]
            name = vals[2]
            price = float(vals[4])
            qty = int(vals[5])
            amount = float(vals[6])

            bill_total += amount
            items.append((pid, name, price, qty, amount))

        # -----------------------------
        # 4️⃣ DB CONNECT
        # -----------------------------
        db = get_db()
        cur = db.cursor()

        customer_id = current_customer.get("id")

        has_customer = customer_id is not None

        # -----------------------------
        # 5️⃣ FETCH OLD CUSTOMER POINTS (SAFE)
        # -----------------------------
        if has_customer:
            cur.execute("""
                SELECT current_points, spent_points, total_points
                FROM customers
                WHERE customer_id = %s
            """, (customer_id,))
            row = cur.fetchone()

            if row:
                old_current = row[0] or 0
                old_spent = row[1] or 0
                old_total = row[2] or 0
            else:
                old_current = old_spent = old_total = 0
        else:
            old_current = old_spent = old_total = 0


        # -----------------------------
        # 6️⃣ POINT CALCULATION
        # -----------------------------
        earned_points = int(bill_total // 100) if has_customer else 0

        try:
            used_points = int(entry_points.get()) if has_customer else 0
        except:
            used_points = 0

        if used_points > old_current:
            used_points = old_current

        new_current = old_current + earned_points - used_points
        new_spent = old_spent + used_points
        new_total = old_total + earned_points


        # -----------------------------
        # 7️⃣ INSERT BILL (SALES)
        # -----------------------------
        cur.execute("""
            INSERT INTO sales (
                shop_id,
                customer_id,
                total_amount,
                given_amount,
                return_amount,
                points_added,
                date_time
            )
            VALUES (%s,%s,%s,%s,%s,%s,NOW())
        """, (
            shop_id,
            customer_id,
            bill_total,
            given,
            ret,
            earned_points
        ))

        sale_id = cur.lastrowid

        # -----------------------------
        # 8️⃣ INSERT BILL ITEMS
        # -----------------------------
        for pid, name, price, qty, amount in items:
            cur.execute("""
                INSERT INTO sales_items
                (sale_id, product_id, name, price, quantity, subtotal)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (sale_id, pid, name, price, qty, amount))
        
        
    
        save_transaction(
            bill_no=bill_no,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            bill_total=total,
            amount_given=given
        )


        # -----------------------------
        # 9️⃣ UPDATE CUSTOMER TOTALS
        # -----------------------------
        cur.execute("""
            UPDATE customers
            SET
                last_purchase_datetime = NOW(),
                last_purchase_amount = %s,
                lifetime_total = lifetime_total + %s,
                total_points = %s,
                current_points = %s,
                spent_points = %s
            WHERE customer_id = %s
        """, (
            bill_total,
            bill_total,
            new_total,
            new_current,
            new_spent,
            customer_id
        ))

        db.commit()
        cur.close()
        db.close()

        # -----------------------------
        # 10️⃣ CLEAR BILL UI
        # -----------------------------
        tree.delete(*tree.get_children())

        current_customer.update({
            "id": None,
            "name": "",
            "phone": "",
            "address": "",
            "points": 0
        })

        for w in (entry_total, entry_give, entry_return):
            try:
                w.delete(0, "end")
            except:
                pass

        # 🔥 clear points only if it exists
        try:
            entry_points.delete(0, "end")
        except NameError:
            pass
        except:
            pass


    def save_transaction(
        bill_no,
        customer_id,
        customer_name,
        customer_phone,
        bill_total,
        amount_given
    ):
        conn = get_db()
        cur = conn.cursor()

        payment = payment_mode.get()   # "Cash" or "Credit"

        return_amount = amount_given - bill_total

        status = "PAID" if payment == "Cash" else "UNPAID"

        cur.execute("""
            INSERT INTO transactions (
                bill_no,
                customer_id,
                customer_name,
                customer_phone,
                transaction_type,
                bill_total,
                amount_given,
                return_amount,
                status,
                trans_date,
                trans_time
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            bill_no,
            customer_id,
            customer_name,
            customer_phone,
            payment.upper(),         # CASH / CREDIT
            bill_total,
            amount_given,
            return_amount,
            status,
            date.today(),
            datetime.now().strftime("%H:%M:%S")
        ))

        conn.commit()
        conn.close()

        # -----------------------------
        # PRINTER INFO (ALWAYS SHOW)
        # -----------------------------
        def show_printer_popup():
            popup = tk.Toplevel(root)
            popup.title("Printer Not Connected")
            popup.resizable(False, False)
            popup.transient(root)
            popup.grab_set()

            w, h = 360, 160
            x = root.winfo_rootx() + (root.winfo_width() // 2) - (w // 2)
            y = root.winfo_rooty() + (root.winfo_height() // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")

            frame = tk.Frame(popup, bg="white", highlightbackground="red", highlightthickness=2)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            tk.Label(
                frame,
                text="⚠ PLEASE CONNECT THE PRINTER",
                fg="red",
                bg="white",
                font=("Segoe UI", 13, "bold")
            ).pack(pady=(25, 10))

            tk.Label(
                frame,
                text="Bill saved successfully",
                fg="#1f2937",
                bg="white",
                font=("Segoe UI", 10)
            ).pack(pady=(0, 15))

            ok_btn = tk.Button(
                frame,
                text="OK",
                width=10,
                bg="#ef4444",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                command=popup.destroy
            )
            ok_btn.pack()

            # ✅ ENTER KEY CLOSE SUPPORT
            popup.bind("<Return>", lambda e: popup.destroy())
            popup.bind("<Escape>", lambda e: popup.destroy())

            ok_btn.focus_set()

        root.after(100, show_printer_popup)

        # ----------------------------- 
        # 7️⃣ CLEAR BILL UI
        # -----------------------------
        tree.delete(*tree.get_children())

        current_customer.update({
            "id": None,
            "name": "",
            "phone": "",
            "address": "",
            "points": 0
        })

        for w in (entry_total, entry_give, entry_return):
            try:
                w.delete(0, "end")
            except:
                pass

        try:
            entry_cid.delete(0, "end")
            entry_cname.delete(0, "end")
            entry_phone.delete(0, "end")
            entry_address.delete(0, "end")
            entry_points.delete(0, "end")
        except:
            pass






    root.bind("<Shift-Return>", save_and_print)




all_customer_items = []


def open_update_product_window(workspace, shop_id):
    import tkinter as tk
    from tkinter import ttk, messagebox

    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    card = tk.Frame(workspace, bg="white",
                    highlightbackground=ACCENT, highlightthickness=3)
    card.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(card, text="Update Product",
             font=("Segoe UI", 22, "bold"),
             fg=ACCENT, bg="white").pack(pady=(15, 10))

    # ================= SEARCH STATE =================
    search_results = {} # ✅ MUST BE DICT
    product_id = None

    # ================= SEARCH =================
    search_frame = tk.Frame(card, bg="white")
    search_frame.pack(anchor="w", padx=40, pady=(0, 5))

    tk.Label(
        search_frame,
        text="Search (Barcode / Name)",
        bg="white",
        fg=TITLE_COLOR,
        font=("Segoe UI", 11)
    ).pack(anchor="w")

    search_var = tk.StringVar()

    entry_search = tk.Entry(
        search_frame,
        width=42,
        bg=WORK_BG,
        fg="#0F172A",
        insertbackground="#0F172A",
        font=("Segoe UI", 11),
        relief="solid",
        bd=1,
        textvariable=search_var
    )
    entry_search.pack(anchor="w")
    entry_search.focus()

    # ================= LISTBOX (DROPDOWN STYLE) =================
    listbox = tk.Listbox(
        search_frame,          # 🔥 IMPORTANT CHANGE
        width=42,
        height=6,
        bg="#1F2933",
        fg="white",
        selectbackground="#38BDF8",
        font=("Segoe UI", 10),
        activestyle="none"
    )

    listbox.pack_forget()      # hidden by default


    
    # ================= FORM =================
    form = tk.Frame(card, bg="white")
    form.pack(pady=10)

    left = tk.Frame(form, bg="white")
    right = tk.Frame(form, bg="white")
    left.grid(row=0, column=0, padx=60, sticky="n")
    right.grid(row=0, column=1, padx=60, sticky="n")

    def load_categories():
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT category_id, category_name
            FROM categories
            WHERE status='Active'
            ORDER BY category_name
        """)
        rows = cur.fetchall()
        conn.close()
        return rows


    categories_data = load_categories()

    category_map = {r["category_name"]: r["category_id"] for r in categories_data}
    category_reverse_map = {r["category_id"]: r["category_name"] for r in categories_data}

    category_var = tk.StringVar()   # ✅ DEFINE EARLY


    def make_entry(p, label, r):
        tk.Label(
            p, text=label,
            bg="white", fg="#0F172A",
            font=("Segoe UI", 11)
        ).grid(row=r, column=0, sticky="e", pady=6, padx=10)

        e = tk.Entry(
            p,
            width=30,
            bg="white",            # 🔥 IMPORTANT
            fg="#000000",          # 🔥 IMPORTANT
            insertbackground="#000000",
            relief="solid",
            bd=1,
            font=("Segoe UI", 11)
        )
        e.grid(row=r, column=1, sticky="w", pady=6)
        return e


    entry_name = make_entry(left, "Product Name", 0)
    entry_print = make_entry(left, "Product Print Name", 1)
    entry_barcode1 = make_entry(left, "Barcode 1", 2)
    entry_barcode2 = make_entry(left, "Barcode 2", 3)
    entry_barcode3 = make_entry(left, "Barcode 3", 4)
    entry_mrp = make_entry(left, "MRP Rate", 5)
    entry_purchase = make_entry(left, "Purchase Rate", 6)
    entry_wholesale = make_entry(right, "Wholesale", 0)
    entry_selling = make_entry(right, "Selling Rate", 1)
    entry_stock = make_entry(right, "Stock", 2)
    entry_gst_sgst = make_entry(right, "GST SGST %", 3)
    entry_gst_cgst = make_entry(right, "GST CGST %", 4)
    entry_hsn = make_entry(right, "HSN Code", 5)

    # ================= LOAD PRODUCT =================

 
    def fill_product(pid):
        nonlocal product_id
        # ✅ CATEGORY SET
        cat_id = row.get("category_id")
        if cat_id in category_reverse_map:
            category_var.set(category_reverse_map[cat_id])
        else:
            category_var.set("")

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT
                product_name,
                product_print_name,
                barcode1,
                barcode2,
                barcode3,
                mrp_rate,
                purchase_rate,
                sale_wholesale,
                selling_price,
                stock,
                gst_sgst,
                gst_cgst,
                hsn
            FROM products
            WHERE product_id=%s AND shop_id=%s
        """, (pid, shop_id))

        row = cur.fetchone()
        conn.close()

        if not row:
            return

        product_id = pid

        # clear first
        for e in [
            entry_name, entry_print, entry_barcode1, entry_barcode2,
            entry_barcode3, entry_mrp, entry_purchase,
            entry_stock, entry_gst_sgst, entry_gst_cgst, entry_hsn
        ]:
            e.delete(0, "end")

        # fill
        entry_name.insert(0, row["product_name"])
        entry_print.insert(0, row["product_print_name"] or "")
        entry_barcode1.insert(0, row["barcode1"] or "")
        entry_barcode2.insert(0, row["barcode2"] or "")
        entry_barcode3.insert(0, row["barcode3"] or "")
        entry_mrp.insert(0, row["mrp_rate"] or 0)
        entry_purchase.insert(0, row["purchase_rate"] or 0)
        entry_wholesale.insert(0, row["sale_wholesale"] or 0)
        entry_selling.insert(0, row["selling_price"] or 0)
        entry_stock.insert(0, row["stock"] or 0)
        entry_gst_sgst.insert(0, row["gst_sgst"] or 0)
        entry_gst_cgst.insert(0, row["gst_cgst"] or 0)
        entry_hsn.insert(0, row["hsn"] or "")


    # ================= SEARCH LOGIC =================
    # ================= SEARCH LOGIC =================
    

   

    def on_typing(*args):
        text = search_var.get().strip()

        listbox.delete(0, tk.END)
        search_results.clear()

        if not text:
            listbox.pack_forget()
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT product_id, product_name, barcode1
            FROM products
            WHERE shop_id=%s
            AND (
                product_name LIKE %s
                OR barcode1 LIKE %s
                OR barcode2 LIKE %s
                OR barcode3 LIKE %s
            )
            LIMIT 10
        """, (
            shop_id,
            f"%{text}%", f"%{text}%",
            f"%{text}%", f"%{text}%"
        ))

        rows = cur.fetchall()
        conn.close()

        if not rows:
            listbox.pack_forget()
            return

        for pid, name, bc in rows:
            display = f"{bc or ''} | {name}"
            listbox.insert(tk.END, display)
            search_results[display] = pid   # ✅ SAFE

        listbox.place(
            x=entry_search.winfo_x(),
            y=entry_search.winfo_y() + entry_search.winfo_height(),
            width=entry_search.winfo_width()
        )
        listbox.place_forget()


    def on_listbox_select(event):
        if not listbox.curselection():
            return

        index = listbox.curselection()[0]
        display = listbox.get(index)

        pid = search_results.get(display)
        if pid:
            fill_product(pid)

        listbox.pack_forget()


    listbox.bind("<<ListboxSelect>>", on_listbox_select)


   

    def on_enter(event):
        text = search_var.get().strip()
        if not text:
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT product_id
            FROM products
            WHERE shop_id=%s
            AND (
                barcode1=%s OR barcode2=%s OR barcode3=%s
                OR product_name=%s
            )
            LIMIT 1
        """, (shop_id, text, text, text, text))

        row = cur.fetchone()
        conn.close()

        if row:
            fill_product(row[0])
            listbox.pack_forget()
            search_var.set("")


    search_var.trace_add("write", on_typing)
    listbox.bind("<<ListboxSelect>>", on_listbox_select)
    listbox.bind("<ButtonRelease-1>", on_listbox_select)
    entry_search.bind("<Return>", on_enter)


    # def on_list_click(event):
    #     listbox.focus_set()          # 🔥 MOST IMPORTANT LINE
    #     index = listbox.nearest(event.y)
    #     if index < 0:
    #         return
    #     pid = search_results.get(index)
    #     if pid:
    #         fill_product(pid)
    #     listbox.place_forget()

    def clear_form():
        nonlocal product_id
        product_id = None

        # 🔹 Clear search
        search_var.set("")
        listbox.place_forget()

        # 🔹 Clear ALL entry fields (LEFT + RIGHT)
        for e in [
            entry_name,
            entry_print,
            entry_barcode1,
            entry_barcode2,
            entry_barcode3,
            entry_mrp,
            entry_purchase,
            entry_wholesale,     # ✅ FIX
            entry_selling,       # ✅ FIX
            entry_stock,
            entry_gst_sgst,
            entry_gst_cgst,
            entry_hsn
        ]:
            e.delete(0, "end")

        # 🔹 Clear CATEGORY dropdown
        category_var.set("")     # ✅ FIX

        # 🔹 Clear RADIO (Company / Other)
        type_var.set("")         # ✅ FIX

        # 🔹 Focus back to search
        entry_search.focus_set()


    # =============================
    # CATEGORY DROPDOWN
    # =============================
    tk.Label(right, text="Category", bg="white",
             fg=TITLE_COLOR, font=("Segoe UI", 11))\
        .grid(row=6, column=0, sticky="e", pady=6, padx=10)

    category_var = tk.StringVar()
    categories = [
        "All", "Bathing", "Biscuits", "Child Items", "Chocolates",
        "Cool Drinks", "Detergents", "Fairness", "General",
        "Masalas", "Medicals", "Milk Mixers", "Mosquito Coils",
        "Napkins", "Oils", "Perfumes", "Rice & Dhalls",
        "Salt", "School Needs", "Semeya", "Snacks",
        "Swamy Items", "Tooth Paste / Brush", "Vegetables"
    ]

    ttk.Combobox(right, textvariable=category_var,
                 values=categories, width=28,
                 state="readonly").grid(row=6, column=1, pady=6)

    # =============================
    # ENTER KEY → NEXT FIELD MOVE
    # =============================
    entries = [
        entry_name,
        entry_print,
        entry_barcode1,
        entry_barcode2,
        entry_barcode3,
        entry_mrp,
        entry_purchase,
        entry_wholesale,
        entry_selling,
        entry_stock,
        entry_gst_sgst,
        entry_gst_cgst,
        entry_hsn
    ]

    for i in range(len(entries) - 1):
        entries[i].bind(
            "<Return>",
            lambda e, nxt=entries[i+1]: nxt.focus_set()
        )

    # last field Enter → UPDATE button click (optional)
    entries[-1].bind("<Return>", lambda e: update_product())

    # =============================
    # RADIO BUTTONS (GREY → SKY BLUE)
    # =============================
    radio_frame = tk.Frame(card, bg="white")
    radio_frame.pack(pady=10)

    type_var = tk.StringVar()

    def styled_radio(text, value):
        return tk.Radiobutton(
            radio_frame,
            text=text,
            variable=type_var,
            value=value,
            bg="white",
            fg="#04122E",            # grey before
            selectcolor="#7DD3FC",   # sky blue after
            activebackground="white",
            activeforeground="#0F172A",
            font=("Segoe UI", 12, "bold"),
            indicatoron=True,
            padx=5
        )

    styled_radio("Company", "Company").pack(side="left", padx=25)
    styled_radio("Other", "Other").pack(side="left", padx=25)
  
  
    # ================= UPDATE BUTTON =================
    def update_product():
        if not product_id:
            messagebox.showerror("Error", "Select product first")
            return

        # ✅ GET CATEGORY AT CLICK TIME (🔥 IMPORTANT FIX)
        selected_category = category_var.get()
        category_id = category_map.get(selected_category)

        if not category_id:
            messagebox.showerror("Error", "Please select valid category")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE products SET
                    product_name=%s,
                    product_print_name=%s,
                    barcode1=%s,
                    barcode2=%s,
                    barcode3=%s,
                    mrp_rate=%s,
                    purchase_rate=%s,
                    sale_wholesale=%s,
                    selling_price=%s,
                    stock=%s,
                    gst_sgst=%s,
                    gst_cgst=%s,
                    hsn=%s,
                    category_id=%s,
                    type=%s
                WHERE product_id=%s AND shop_id=%s
            """, (
                entry_name.get(),
                entry_print.get(),
                entry_barcode1.get(),
                entry_barcode2.get(),
                entry_barcode3.get(),
                entry_mrp.get() or 0,
                entry_purchase.get() or 0,
                entry_wholesale.get() or 0,
                entry_selling.get() or 0,
                entry_stock.get() or 0,
                entry_gst_sgst.get() or 0,
                entry_gst_cgst.get() or 0,
                entry_hsn.get(),
                category_id,          # ✅ CORRECT CATEGORY ID
                type_var.get(),
                product_id,
                shop_id
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "✅ Product updated successfully")
            clear_form()

        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    tk.Button(
        card, text="UPDATE PRODUCT",
        bg=ACCENT, fg="white",
        font=("Segoe UI", 13, "bold"),
        padx=70, pady=15,
        relief="flat",
        command=update_product
    ).pack(pady=15)  

    def fill_product(pid):
        nonlocal product_id
        product_id = pid

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT p.*, c.category_name
            FROM products p
            LEFT JOIN categories c
                ON p.category_id = c.category_id
            WHERE p.product_id=%s AND p.shop_id=%s
        """, (pid, shop_id))

        row = cur.fetchone()
        conn.close()
        if not row:
            return

        def set_entry(e, v):
            e.delete(0, tk.END)
            e.insert(0, v if v is not None else "")

        set_entry(entry_name, row["product_name"])
        set_entry(entry_print, row["product_print_name"])
        set_entry(entry_barcode1, row["barcode1"])
        set_entry(entry_barcode2, row["barcode2"])
        set_entry(entry_barcode3, row["barcode3"])
        set_entry(entry_mrp, row["mrp_rate"])
        set_entry(entry_purchase, row["purchase_rate"])
        set_entry(entry_wholesale, row["sale_wholesale"])
        set_entry(entry_selling, row["selling_price"])
        set_entry(entry_stock, row["stock"])
        set_entry(entry_gst_sgst, row["gst_sgst"])
        set_entry(entry_gst_cgst, row["gst_cgst"])
        set_entry(entry_hsn, row["hsn"])

        # ✅ CATEGORY
        # ❌ OLD
        # category_var.set(row.get("category_name", ""))

        # ✅ NEW SAFE VERSION
        cat_name = row.get("category_name")
        if cat_name and cat_name in category_map:
            category_var.set(cat_name)
        else:
            category_var.set("General")


        # ✅ TYPE
        type_var.set(row["type"] if row["type"] in ("Company", "Other") else "")





categoryless_mode = False
checked_rows = set()
all_selected = False
drag_selecting = False
active_editors = {}     # 🔥 MUST be dict  # 🔥 MUST BE DICT
bulk_edit_mode = False



def open_product_details_page(workspace, shop_id):
    # 🔥 SAFETY: REMOVE OLD GLOBAL SCROLL BINDS
    checked_rows = set()
    all_selected = False
    drag_selecting = False
    bulk_edit_mode = False
    edit_entry = None
    edit_col_index = None
    edit_row = None

    active_editors = {}     # 🔥 MUST be dict
    
    # {row_id: [(entry, col_index), ...]}





    workspace.unbind_all("<MouseWheel>")
    workspace.unbind_all("<Button-4>")
    workspace.unbind_all("<Button-5>")

    import tkinter as tk
    from tkinter import ttk

    # ===============================
    # CLEAR WORKSPACE
    # ===============================
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ===============================
    # MAIN CARD
    # ===============================
    card = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0118EA",
        highlightthickness=2
    )
    card.pack(fill="both", expand=True, padx=20, pady=20)

    # ===============================
    # TITLE
    # ===============================
    title = tk.Label(
        card,
        text="Product Details",
        font=("Segoe UI", 10, "bold"),
        bg="white",
        fg="#1108FF"
    )
    title.pack(pady=(15, 10))

 
    # ===============================
    # TOP TOOL BAR (SEARCH + FILTER)
    # # ===============================
    # top_bar = tk.Frame(card, bg="white")
    # top_bar.pack(fill="x", padx=15, pady=(5, 8))

    # ===============================
    # TOP TOOL BAR (EXACT ALIGNMENT)
    # ===============================
    top_bar = tk.Frame(card, bg="white")
    top_bar.pack(fill="x", padx=15, pady=(6, 10))

    # ---- Search label ----
    tk.Label(
        top_bar,
        text="Search",
        bg="white",
        fg="#0F172A",
        font=("Segoe UI", 11, "bold")
    ).grid(row=0, column=0, padx=(0, 6), sticky="w")

    # ---- Search entry ----
    search_var = tk.StringVar()
    search_entry = tk.Entry(
        top_bar,
        textvariable=search_var,
        font=("Segoe UI", 11),
        width=26,
        bg="white",
        fg="#0F172A",
        insertbackground="#0F172A",
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground="#CBD5E1",
        highlightcolor="#2563EB"
    )
    search_entry.grid(row=0, column=1, padx=(0, 14), ipady=4, sticky="w")

    # ---- Bulk Update ----
    tk.Button(
        top_bar,
        text="Bulk Update",
        bg="#2563EB",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=6
    ).grid(row=0, column=2, padx=(0, 10), sticky="w")

    # ---- Update ----
    tk.Button(
        top_bar,
        text="Update",
        bg="#16A34A",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=6
    ).grid(row=0, column=3, padx=(0, 18), sticky="w")

    # ---- Category label ----
    tk.Label(
        top_bar,
        text="Category",
        bg="white",
        fg="#0F172A",
        font=("Segoe UI", 11)
    ).grid(row=0, column=4, padx=(0, 6), sticky="w")

    # ---- Category combo ----
    category_var = tk.StringVar(value="All")
    category_combo = ttk.Combobox(
        top_bar,
        textvariable=category_var,
        values=[
            "All", "Bathing", "Biscuits", "Child Items", "Chocolates",
            "Cool Drinks", "Detergents", "Fairness", "General",
            "Masalas", "Medicals", "Milk Mixers", "Mosquito Coils",
            "Napkins", "Oils", "Perfumes", "Rice & Dhalls",
            "Salt", "School Needs", "Semeya", "Snacks",
            "Swamy Items", "Tooth Paste / Brush", "Vegetables"
        ],
        width=22,
        state="readonly"
    )
    category_combo.grid(row=0, column=5, padx=(0, 14), sticky="w")
    category_combo.current(0)


    def clear_filters_and_selection():
        # 1️⃣ Category back to ALL
        category_var.set("All")
        category_combo.current(0)

        # 2️⃣ Clear checked rows + checkbox UI
        checked_rows.clear()

        for item in tree.get_children():
            # uncheck checkbox
            values = list(tree.item(item, "values"))
            values[-1] = "☐"
            tree.item(item, values=values, tags=())

        # 3️⃣ Reload full table (All products)
        load_products()


    tk.Button(
        top_bar,
        text="Clear",
        bg="#DC2626",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=6,
        command=clear_filters_and_selection
    ).grid(row=0, column=6, sticky="w")



    # ===============================
    # TABLE FRAME
    # ===============================
    table_frame = tk.Frame(card, bg="black", bd=1)
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    table_container = tk.Frame(table_frame, bg="white")
    table_container.pack(fill="both", expand=True)

    

    # ===============================
    # TREEVIEW
    # ===============================
    columns = (
        "product_id",
        "product_name",
        "hsn",
        "mrp",
        "purchase_price",
        "price",
        "cgst",
        "sgst",
        "company",
        "select"
    )

    tree = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings",
        height=15,
        selectmode="none"   # 🔥 MUST
    )

    tree.focus_set()

    scroll_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=tree.yview
    )
    tree.configure(yscrollcommand=scroll_y.set)

    tree.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    # ===============================
    # HEADINGS
    # ===============================
    tree.heading("product_id", text="Product ID")
    tree.heading("product_name", text="Product Name")
    tree.heading("hsn", text="HSN Code")
    tree.heading("mrp", text="MRP ₹")
    tree.heading("purchase_price", text="Purchase ₹")
    tree.heading("price", text="Selling ₹")
    tree.heading("cgst", text="CGST %")
    tree.heading("sgst", text="SGST %")
    tree.heading("company", text="Company")
    tree.heading("select", text="Select")

    # ===============================
    # COLUMNS
    # ===============================
    tree.column("product_id", width=90, anchor="center", stretch=False)
    tree.column("product_name", width=180, anchor="w")
    tree.column("hsn", width=110, anchor="center")
    tree.column("mrp", width=90, anchor="e")
    tree.column("purchase_price", width=110, anchor="e")
    tree.column("price", width=90, anchor="e")
    tree.column("cgst", width=80, anchor="center")
    tree.column("sgst", width=80, anchor="center")
    tree.column("company", width=140, anchor="w")
    tree.column("select", width=80, anchor="center")

    # ===============================
    # TAGS
    # ===============================
    tree.tag_configure("odd", background="white")
    tree.tag_configure("even", background="#94EFE5")

    tree.tag_configure("checked", background="#D1DEEF") 

    # ===============================
    # SAMPLE DATA (REMOVE LATER)
    # ===============================
    def fetch_products(shop_id, category=None, search_text="", categoryless=False):
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        query = """
            SELECT
                p.product_id,
                p.product_name,
                p.hsn,
                p.mrp_rate,
                p.purchase_rate,
                p.selling_price,
                p.gst_cgst,
                p.gst_sgst,
                c.category_name
            FROM products p
            LEFT JOIN categories c
                ON p.category_id = c.category_id
            WHERE p.shop_id = %s
        """

        params = [shop_id]

        if category and category != "All":
            query += " AND c.category_name = %s"
            params.append(category)

        if search_text:
            query += " AND p.product_name LIKE %s"
            params.append(f"%{search_text}%")

        cur.execute(query, params)
        rows = cur.fetchall()

        conn.close()
        return rows


    def load_products():
        global all_selected

        products = fetch_products(
            shop_id,
            category=category_var.get(),
            search_text=search_var.get().strip(),
            categoryless=categoryless_mode
        )

        tree.delete(*tree.get_children())
        checked_rows.clear()
        all_selected = False

        for i, p in enumerate(products):
            tree.insert(
                "",
                "end",
                values=(
                    p["product_id"],
                    p["product_name"],
                    p["hsn"],
                    p["mrp_rate"],
                    p["purchase_rate"],
                    p["selling_price"],
                    p["gst_cgst"],
                    p["gst_sgst"],
                    p["category_name"],   # ✅ FIXED
                    "☐"
                ),
                tags=("even" if i % 2 == 0 else "odd",)
            )





    def on_search_change(*args):
        load_products()

    search_var.trace_add("write", on_search_change)

    

    def on_category_change(event=None):
        load_products()
        
        selected_category = category_var.get()
        products = fetch_products(shop_id, selected_category)

        tree.delete(*tree.get_children())

        for i, p in enumerate(products):
            tree.insert(
                "",
                "end",
                values=(
                    p["product_id"],
                    p["product_name"],
                    p["hsn"],
                    p["mrp_rate"],
                    p["purchase_rate"],
                    p["selling_price"],
                    p["gst_cgst"],
                    p["gst_sgst"],
                    p["category"],
                    "☐"
                )
            )
    category_combo.bind("<<ComboboxSelected>>", on_category_change)


 # light blue

    def on_search_enter(event=None):
        children = tree.get_children()
        if not children:
            return

        first_row = children[0]

        tree.selection_set(first_row)      # select
        tree.focus(first_row)              # focus
        tree.see(first_row)                # scroll into view
    
    search_entry.bind("<Return>", on_search_enter)


    # category_var.set("All")   # default
    load_products()           # 🔥 THIS WAS MISSING

    def set_checkbox(item, checked=True):
        values = list(tree.item(item, "values"))
        values[-1] = "☑" if checked else "☐"
        tree.item(item, values=values)

    def is_checked(item):
        return tree.item(item, "values")[-1] == "☑"


    def on_heading_click(event):
        global all_selected

        region = tree.identify_region(event.x, event.y)
        if region != "heading":
            return

        col = tree.identify_column(event.x)
        col_name = tree["columns"][int(col[1:]) - 1]

        if col_name != "select":
            return

        all_selected = not all_selected
        checked_rows.clear()

        for item in tree.get_children():
            set_checkbox(item, all_selected)
            if all_selected:
                checked_rows.add(item)


    # tree.bind("<Button-1>", on_heading_click, add="+")

    def set_checkbox(item, checked):
        values = list(tree.item(item, "values"))
        values[-1] = "☑" if checked else "☐"
        tree.item(item, values=values)

    def is_checked(item):
        return tree.item(item, "values")[-1] == "☑"



    def update_row_color(item, index=None):
        if is_checked(item):
            tree.item(item, tags=("checked",))
        else:
            # fallback to zebra striping
            if index is None:
                index = tree.index(item)

            tag = "even" if index % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

    def refresh_row_tag(item):
        if is_checked(item):
            tree.item(item, tags=("checked",))
        else:
            index = tree.index(item)
            tree.item(
                item,
                tags=("even" if index % 2 == 0 else "odd",)
            )



    def on_tree_click(event):
        global all_selected

        region = tree.identify_region(event.x, event.y)

        # ---------- HEADER CLICK (SELECT ALL) ----------
        if region == "heading":
            col = tree.identify_column(event.x)
            col_name = tree["columns"][int(col[1:]) - 1]

            if col_name == "select":
                all_selected = not all_selected
                checked_rows.clear()

                for item in tree.get_children():
                    set_checkbox(item, all_selected)
                    if all_selected:
                        checked_rows.add(item)
                    refresh_row_tag(item)

                return "break"

        # ---------- ROW CLICK ----------
        if region in ("cell", "tree"):
            row = tree.identify_row(event.y)
            if not row:
                return "break"

            if is_checked(row):
                set_checkbox(row, False)
                checked_rows.discard(row)
            else:
                set_checkbox(row, True)
                checked_rows.add(row)

            refresh_row_tag(row)
            return "break"



    tree.bind("<Button-1>", on_tree_click)


    def on_search_enter(event=None):
        rows = tree.get_children()
        if not rows:
            return

        row = rows[0]

        set_checkbox(row, True)
        checked_rows.clear()
        checked_rows.add(row)

        tree.item(row, tags=("checked",))
        tree.see(row)

    search_entry.bind("<Return>", on_search_enter)


    # tree.bind("<Button-1>", on_tree_click)

    def on_mouse_press(event):
        nonlocal drag_selecting, all_selected

        region = tree.identify_region(event.x, event.y)

        # ----- HEADER CLICK (SELECT ALL) -----
        if region == "heading":
            col = tree.identify_column(event.x)
            col_name = tree["columns"][int(col[1:]) - 1]

            if col_name == "select":
                all_selected = not all_selected
                checked_rows.clear()

                for item in tree.get_children():
                    set_checkbox(item, all_selected)
                    if all_selected:
                        checked_rows.add(item)

                return

        # ----- ROW CLICK -----
        if region in ("cell", "tree"):
            row = tree.identify_row(event.y)
            if not row:
                return

            if is_checked(row):
                set_checkbox(row, False)
                checked_rows.discard(row)
            else:
                set_checkbox(row, True)
                checked_rows.add(row)

            drag_selecting = True   # 🔥 START DRAG



    def on_drag_start(event):
        global drag_selecting
        drag_selecting = True




    def on_mouse_drag(event):
        nonlocal drag_selecting

        if not drag_selecting:
            return

        row = tree.identify_row(event.y)
        if row and not is_checked(row):
            set_checkbox(row, True)
            checked_rows.add(row)
    def on_mouse_release(event):
        nonlocal drag_selecting
        drag_selecting = False
    tree.bind("<ButtonPress-1>", on_mouse_press)
    tree.bind("<B1-Motion>", on_mouse_drag)
    tree.bind("<ButtonRelease-1>", on_mouse_release)

    def on_ctrl_a(event):
        nonlocal all_selected

        all_selected = not all_selected
        checked_rows.clear()

        for item in tree.get_children():
            set_checkbox(item, all_selected)
            if all_selected:
                checked_rows.add(item)

        return "break"
    # 🔥 stop default select-all
    
    workspace.bind_all("<Control-a>", on_ctrl_a)
    workspace.bind_all("<Control-A>", on_ctrl_a)

    # ===============================
    # FULL ROW INLINE EDIT (SINGLE CLICK)
    # ===============================

# 🔥 FORCE active_editors AS DICT (ANTI-BUG)
    if "active_editors" not in globals() or not isinstance(active_editors, dict):
        active_editors = {}

    bulk_edit_mode = False

    def close_active_editors():
        global active_editors
        for e, _ in active_editors:
            e.destroy()
        active_editors = []


    def open_bulk_row_edit():
        global active_editors

        close_all_editors()

        for row in checked_rows:
            values = list(tree.item(row, "values"))
            editors = []

            for col_index, col in enumerate(tree["columns"]):
                if col in ("product_id", "select"):
                    continue

                bbox = tree.bbox(row, f"#{col_index+1}")
                if not bbox:
                    continue

                x, y, w, h = bbox
                e = tk.Entry(tree, font=("Segoe UI", 10))
                e.insert(0, values[col_index])
                e.place(x=x, y=y, width=w, height=h)

                editors.append((e, col_index))

            active_editors[row] = editors

            # 🔥 SAVE KEYS
            for e, _ in editors:
                e.bind("<Return>", lambda ev: (save_bulk_update_db(), "break"))
                e.bind("<Escape>", lambda ev: close_all_editors())


        # # 🔥 CANCEL ON ESC
        # def cancel_row(event=None):
        #     close_active_editors()

        # for e, _ in active_editors:
        #     e.bind("<Return>", save_row)
        #     e.bind("<Escape>", cancel_row)


    # def on_row_single_click(event):
    #     region = tree.identify_region(event.x, event.y)
    #     if region not in ("cell", "tree"):
    #         return

    #     row = tree.identify_row(event.y)
    #     if not row:
    #         return

    #     # 🔥 ONLY EDIT IF ROW IS SELECTED
    #     if row not in checked_rows:
    #         return

    #     open_full_row_edit(row)

    #     return "break"


    # tree.bind("<Button-1>", on_row_single_click)

    def close_all_editors():
        global active_editors

        if not isinstance(active_editors, dict):
            active_editors = {}
            return

        for editors in active_editors.values():
            for e, _ in editors:
                e.destroy()

        active_editors.clear()


    
    def apply_editors_to_tree():
        global active_editors

        if not isinstance(active_editors, dict):
            active_editors = {}
            return

        for row, editors in active_editors.items():
            vals = list(tree.item(row, "values"))
            for e, idx in editors:
                vals[idx] = e.get()
            tree.item(row, values=vals)





    def enable_bulk_edit():
        global bulk_edit_mode

        if not checked_rows:
            messagebox.showwarning("No Selection", "Select rows first")
            return

        bulk_edit_mode = True
        open_bulk_row_edit()

        messagebox.showinfo(
            "Bulk Edit Enabled",
            "Selected rows are editable.\n"
            "Edit & press Enter / Ctrl+S / Update."
        )

    def open_bulk_row_edit():
        global active_editors

        if not isinstance(active_editors, dict):
            active_editors = {}

        close_all_editors()

        for row in checked_rows:
            values = list(tree.item(row, "values"))
            editors = []

            for col_index, col in enumerate(tree["columns"]):
                if col in ("product_id", "select"):
                    continue

                bbox = tree.bbox(row, f"#{col_index+1}")
                if not bbox:
                    continue

                x, y, w, h = bbox
                e = tk.Entry(tree, font=("Segoe UI", 10))
                e.insert(0, values[col_index])
                e.place(x=x, y=y, width=w, height=h)

                editors.append((e, col_index))

            active_editors[row] = editors

            for e, _ in editors:
                e.bind("<Return>", lambda ev: (save_bulk_update_db(), "break"))
                e.bind("<Escape>", lambda ev: close_all_editors())


    def save_bulk_update_db():
        global bulk_edit_mode, active_editors

        if not checked_rows:
            messagebox.showwarning("No Selection", "Select products first")
            return

        if not isinstance(active_editors, dict):
            active_editors = {}

        apply_editors_to_tree()
        close_all_editors()

        conn = mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )
        cursor = conn.cursor()

        for row in checked_rows:
            vals = tree.item(row, "values")

            cursor.execute("""
                UPDATE products SET
                    product_name=%s,
                    hsn_code=%s,
                    mrp_rate=%s,
                    purchase_rate=%s,
                    selling_price=%s,
                    gst_cgst=%s,
                    gst_sgst=%s,
                    category=%s
                WHERE product_id=%s
            """, (
                vals[1], vals[2], vals[3], vals[4],
                vals[5], vals[6], vals[7], vals[8],
                vals[0]
            ))

        conn.commit()
        conn.close()

        bulk_edit_mode = False
        messagebox.showinfo("Success", "Bulk update saved")



    workspace.bind_all("<Control-s>", lambda e: save_bulk_update_db())
    workspace.bind_all("<Control-S>", lambda e: save_bulk_update_db())

    tk.Button(
        top_bar,
        text="Bulk Update",
        bg="#2563EB",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=6,
        command=enable_bulk_edit
    ).grid(row=0, column=2, padx=(0, 10), sticky="w")

    tk.Button(
        top_bar,
        text="Update",
        bg="#16A34A",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=6,
        command=save_bulk_update_db
    ).grid(row=0, column=3, padx=(0, 18), sticky="w")

    def on_ctrl_s(event=None):
        save_bulk_update_db()
        return "break"

    workspace.bind("<Control-s>", on_ctrl_s)
    workspace.bind("<Control-S>", on_ctrl_s)



sort_high_to_low = False

from datetime import datetime, date
from tkcalendar import DateEntry

# 🔐 GLOBAL SMS STATE (PERSIST ACROSS REFRESH)
SMS_ENABLED_STATE = False
edit_entry = None
editing_info = {}

all_customer_rows = []
edit_entry = None
date_filter_active = False

# -------------------------------
# Customer List Window (Premium)
# -------------------------------
def open_customer_window(workspace, shop_id):
    

    import tkinter as tk
    from tkinter import ttk
    from datetime import datetime
    from tkcalendar import DateEntry
    import socket

    # -------------------------------
    # CLEAR WORKSPACE
    # -------------------------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)
    pass

    # -------------------------------
    # CARD
    # -------------------------------
    card = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=ACCENT,
        highlightthickness=3
    )
    card.pack(fill="both", expand=True, padx=10, pady=10)

    tk.Label(
        card,
        text="Customer Details (Premium View)",
        font=("Segoe UI", 10, "bold"),
        fg=ACCENT,
        bg="white"
    ).pack(pady=(7, 6))

    # -------------------------------
    # TOP ROW
    # -------------------------------
    top_row = tk.Frame(card, bg="white")
    top_row.pack(fill="x", padx=20, pady=(5, 10))

    # -------------------------------
    # SEARCH
    # -------------------------------
    tk.Label(
        top_row,
        text="Search:",
        bg="white",
        fg="black",
    ).pack(side="left", padx=(0, 6))

    search_var = tk.StringVar()

    search_entry = tk.Entry(
        top_row,
        textvariable=search_var,
        width=26,
        bg="white",          # ✅ white background
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left", padx=(0, 12))


    # -------------------------------
    # LOAD CUSTOMERS (DUMMY)
    # -------------------------------
    def load_customers(start_date=None, end_date=None):
        print("📥 Load customers")
        print("From:", start_date, "To:", end_date)

    # -------------------------------
    # NETWORK CHECK
    # -------------------------------
    def is_network_connected():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    # ===============================
    # ACTION ROW (FIXED ALIGNMENT)
    # ===============================
    action_row = tk.Frame(top_row, bg="white")
    action_row.pack(side="left", padx=6)


    def fixed_box(parent, w=90, h=30):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box


    # -------------------------------
    # ADD CUSTOMER
    # -------------------------------
    box_add = fixed_box(action_row, 120, 30)

    tk.Button(
        box_add,
        text="➕ Add Customer",
        bg="#27caef",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        command=lambda: open_add_customer_window(workspace, shop_id)
    ).pack(fill="both", expand=True)


    # -------------------------------
    # HIGH ↔ LOW TOGGLE BUTTON
    # -------------------------------
    sort_high_to_low = False

    box_sort = fixed_box(action_row, 90, 30)

    def toggle_sort_by_points():
        global sort_high_to_low
        sort_high_to_low = not sort_high_to_low

        if sort_high_to_low:
            btn_sort.config(text="Clear", bg="#dc2626")
            load_customers(order_by_points=True)
        else:
            btn_sort.config(text="High → Low", bg="#2e28a7")
            load_customers(order_by_points=False)

    btn_sort = tk.Button(
        box_sort,
        text="High → Low",
        bg="#2e28a7",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        command=toggle_sort_by_points
    )
    btn_sort.pack(fill="both", expand=True)


    # -------------------------------
    # FROM DATE
    # -------------------------------
    from datetime import datetime

    # -------------------------------
    # FROM DATE
    # -------------------------------
    box_from = fixed_box(action_row, 130, 30)

    tk.Label(box_from, text="From", bg="black", fg="white").pack(side="left", padx=3)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")


    # -------------------------------
    # TO DATE
    # -------------------------------
    box_to = fixed_box(action_row, 130, 30)

    tk.Label(box_to, text="To", bg="black", fg="white").pack(side="left", padx=3)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")



    # -------------------------------
    # APPLY / CLEAR BUTTON (FIXED SIZE)
    # -------------------------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False  # toggle state

    def toggle_date_filter():
        global date_filter_active

        if not date_filter_active:
            # ✅ APPLY FILTER
            load_customers(
                start_date.get_date(),
                end_date.get_date()
            )

            btn_apply.config(
                text="Clear",
                bg="#dc2626"   # red
            )

            date_filter_active = True

        else:
            # ✅ CLEAR FILTER
            load_customers()   # normal full list

            btn_apply.config(
                text="🔍 Apply",
                bg="#198754"
            )

            date_filter_active = False


    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#198754",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        command=toggle_date_filter
    )

    btn_apply.pack(fill="both", expand=True)



    

       # -------------------------------
    # STATUS FRAME (RIGHT SIDE)
    # -------------------------------
    status_frame = tk.Frame(top_row, bg="white")
    status_frame.pack(side="left", padx=(25, 5))

    import socket

    # -------------------------------
    # NETWORK CHECK
    # -------------------------------
    def is_network_connected():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    # -------------------------------
    # NETWORK STATUS SQUARE
    # -------------------------------
    net_canvas = tk.Canvas(
        status_frame,
        width=28,
        height=28,
        bg="white",
        highlightthickness=0
    )
    net_canvas.pack(side="left", padx=(0, 10))

    square = net_canvas.create_rectangle(2, 2, 26, 26, outline="")
    icon = net_canvas.create_text(14, 14, font=("Segoe UI", 12, "bold"))

    def update_network_status():
        if is_network_connected():
            net_canvas.itemconfig(square, fill="#28a745")
            net_canvas.itemconfig(icon, text="✔", fill="white")
        else:
            net_canvas.itemconfig(square, fill="#dc3545")
            net_canvas.itemconfig(icon, text="✖", fill="white")

        # 🔁 refresh every 3 sec
        net_canvas.after(3000, update_network_status)

    update_network_status()

    # -------------------------------
    # 🔘 MODERN TOGGLE (FIXED & PERMANENT)
    # -------------------------------
    sms_enabled = load_sms_state()   # 🔐 load once

    # -------------------------------
    # 🔘 MODERN TOGGLE (BORDER FIXED)
    # -------------------------------
    sms_enabled = load_sms_state()   # 🔐 persistent state

    toggle_canvas = tk.Canvas(
        status_frame,
        width=90,          # ✅ FIXED WIDTH
        height=30,
        bg="white",
        highlightthickness=0
    )
    toggle_canvas.pack(side="left", padx=(8, 0))

    # background (pill with full border)
    bg = toggle_canvas.create_rectangle(
        2, 2, 88, 28,      # ✅ inside canvas
        outline="black",
        width=1,
        fill="#e5e7eb"
    )

    # knob
    knob = toggle_canvas.create_oval(
        4, 4, 28, 26,
        fill="white",
        outline="#9ca3af"
    )

    # ON / OFF text
    label = toggle_canvas.create_text(
        45, 15,
        font=("Segoe UI", 9, "bold"),
        text=""
    )

    def draw_toggle():
        if sms_enabled:
            toggle_canvas.itemconfig(bg, fill="#2563eb")  # blue
            toggle_canvas.coords(knob, 60, 4, 84, 26)     # 👉 right
            toggle_canvas.itemconfig(label, text="ON", fill="white")
        else:
            toggle_canvas.itemconfig(bg, fill="#e5e7eb")  # grey
            toggle_canvas.coords(knob, 4, 4, 28, 26)      # 👉 left
            toggle_canvas.itemconfig(label, text="OFF", fill="#111827")

    def toggle_sms(event=None):
        nonlocal sms_enabled
        sms_enabled = not sms_enabled
        save_sms_state(sms_enabled)

        if sms_enabled:
            enable_sms_sending()
        else:
            disable_sms_sending()

        draw_toggle()

    toggle_canvas.bind("<Button-1>", toggle_sms)

    draw_toggle()





    # -------------------------------
    # SMS METHODS (YOUR REAL LOGIC HERE)
    # -------------------------------
    def enable_sms_sending():
        print("✅ SMS SENDING ENABLED")

    def disable_sms_sending():
        print("❌ SMS SENDING DISABLED")


    style = ttk.Style()
    style.theme_use("default")

    # ===== TREE BODY =====
    style.configure(
        "Treeview",
        background="white",
        foreground="black",
        rowheight=28,
        fieldbackground="white",

        # 🔥 EXCEL GRID LINES
        rowseparatorcolor="black",
        rowseparatorwidth=1,
        columnseparatorcolor="black",
        columnseparatorwidth=1,

        bordercolor="black",
        borderwidth=1,
        relief="solid"
    )

    # ===== HEADER =====
    style.configure(
        "Treeview.Heading",
        background="#e6e6e6",
        foreground="black",
        font=("Segoe UI", 9, "bold"),
        borderwidth=1,
        relief="solid"
    )

    # ===== SELECTION =====
    style.map(
        "Treeview",
        background=[("selected", "#f0ed3d")],
        foreground=[("selected", "white")]
    )

    #  tree overview
    # =============================
    # TABLE FRAME
    # =============================
    table_frame = tk.Frame(card, bg="black", bd=1)
    table_frame.pack(fill="both", expand=True, padx=10, pady=6)

    # 🔥 INNER CONTAINER (IMPORTANT)
    table_container = tk.Frame(table_frame, bg="white")
    table_container.pack(fill="both", expand=True)

    # =============================
    # TREEVIEW
    # =============================
    tree_customers = ttk.Treeview(
        table_container,
        columns=(
            "customer_id",
            "name",
            "phone",
            "address",
            "last_purchase",
            "lifetime_total",
            "current_points",
            "details"
        ),
        show="headings"
    )

    # =============================
    # SCROLLBAR
    # =============================
    scroll_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=tree_customers.yview
    )

    tree_customers.configure(yscrollcommand=scroll_y.set)

    # 🔥 PACK ORDER (VERY IMPORTANT)
    tree_customers.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    # =============================
    # HEADINGS
    # =============================
    tree_customers.heading("customer_id", text="Cust ID")
    tree_customers.heading("name", text="Name")
    tree_customers.heading("phone", text="Phone")
    tree_customers.heading("address", text="Address")
    tree_customers.heading("last_purchase", text="Last Purchase")
    tree_customers.heading("lifetime_total", text="Lifetime Total ₹")
    tree_customers.heading("current_points", text="Points")
    tree_customers.heading("details", text="Details")

    # =============================
    # COLUMN WIDTHS
    # =============================
    tree_customers.column("customer_id", width=100, anchor="center", stretch=False)
    tree_customers.column("name", width=160, anchor="w")
    tree_customers.column("phone", width=130, anchor="center")
    tree_customers.column("address", width=220, anchor="w")
    tree_customers.column("last_purchase", width=160, anchor="center")
    tree_customers.column("lifetime_total", width=140, anchor="e")
    tree_customers.column("current_points", width=90, anchor="center")
    tree_customers.column("details", width=80, anchor="center", stretch=False)

    # =============================
    # TAG STYLES
    # =============================
    tree_customers.tag_configure(
        "group",
        background="#a9d8ef",
        font=("Segoe UI", 10, "bold")
    )
    tree_customers.tag_configure("row", background="white")


    
    from datetime import datetime, time

    from datetime import datetime, date, timedelta

    from datetime import date, timedelta

    def load_customers(start_dt=None, end_dt=None, order_by_points=False):
        tree_customers.delete(*tree_customers.get_children())

        conn = get_connection()
        cur = conn.cursor()

        search_text = search_entry.get().strip()

        base_query = """
            SELECT
                c.customer_id,
                c.customer_name,
                c.phone_1,
                c.address,

                -- ✅ LAST PURCHASE AMOUNT
                COALESCE(
                    (
                        SELECT s2.total_amount
                        FROM sales s2
                        WHERE s2.customer_id = c.customer_id
                        AND s2.shop_id = c.shop_id
                        ORDER BY s2.date_time DESC
                        LIMIT 1
                    ), 0
                ) AS last_purchase_amount,

                -- ✅ LIFETIME TOTAL
                c.lifetime_total,

                -- ✅ CURRENT POINTS
                c.current_points,

                -- ✅ LAST BILL DATE (for sorting)
                MAX(s.date_time) AS last_bill_date

            FROM customers c
            LEFT JOIN sales s
                ON s.customer_id = c.customer_id
                AND s.shop_id = c.shop_id
            WHERE c.shop_id = %s
            AND c.status = 'ACTIVE'
        """


        params = [shop_id]

        # 🔍 SEARCH FILTER
        if search_text:
            base_query += """
                AND (
                    c.customer_name LIKE %s
                    OR c.phone_1 LIKE %s
                )
            """
            like = f"%{search_text}%"
            params.extend([like, like])

        # 📅 DATE FILTER
        filter_active = False
        if start_dt and end_dt:
            filter_active = True
            base_query += " AND DATE(s.date_time) BETWEEN %s AND %s"
            params.extend([start_dt, end_dt])

        base_query += """
            GROUP BY
                c.customer_id,
                c.customer_name,
                c.phone_1,
                c.address,
                
                c.lifetime_total,
                c.current_points
        """

        # 🔥 SORT
        if order_by_points:
            base_query += " ORDER BY c.current_points DESC"
        else:
            base_query += " ORDER BY last_bill_date DESC"

        cur.execute(base_query, params)
        rows = cur.fetchall()
        conn.close()

        today = date.today()
        yesterday = today - timedelta(days=1)

        # =====================================================
        # 🔥 HIGH → LOW MODE (NO DATE GROUPING)
        # =====================================================
        if order_by_points:
            for r in rows:
                tree_customers.insert(
                    "",
                    "end",
                    iid=str(r[0]),
                    values=(
                        r[0],              # customer_id
                        r[1],              # name
                        r[2],              # phone
                        r[3] or "-",       # address
                        f"₹ {r[4]:.2f}",   # total spent
                        f"₹ {r[5]:.2f}",   # lifetime total
                        r[6],              # ✅ CURRENT POINTS
                        "View"
                    ),
                    tags=("row",)
                )
            return

        # =====================================================
        # NORMAL DATE GROUP MODE
        # =====================================================
        grouped = {}

        for r in rows:
            last_dt = r[7]

            if last_dt:
                bill_date = last_dt.date()
                if filter_active:
                    label = bill_date.strftime("%d-%m-%Y")
                else:
                    if bill_date == today:
                        label = "TODAY"
                    elif bill_date == yesterday:
                        label = "YESTERDAY"
                    else:
                        label = bill_date.strftime("%d-%m-%Y")
            else:
                label = "NO BILL"

            grouped.setdefault(label, []).append(r)

        for label, customers in grouped.items():
            tree_customers.insert(
                "",
                "end",
                values=(label, "", "", "", "", "", "", ""),
                tags=("group",)
            )

            for r in customers:
                tree_customers.insert(
                    "",
                    "end",
                    iid=str(r[0]),
                    values=(
                        r[0],
                        r[1],
                        r[2],
                        r[3] or "-",
                        f"₹ {r[4]:.2f}",
                        f"₹ {r[5]:.2f}",
                        r[6],              # ✅ CURRENT POINTS
                        "View"
                    ),
                    tags=("row",)
                )


    search_entry.bind("<KeyRelease>", lambda e: load_customers())


    def refresh_table(data):
        tree_customers.delete(*tree_customers.get_children())

        for i, vals in enumerate(data):
            tag = "even" if i % 2 == 0 else "odd"
            tree_customers.insert(
                "",
                "end",
                values=vals,
                tags=(tag,)
            )



    # INITIAL LOAD
    load_customers()


    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview",
        rowheight=28,
        font=("Segoe UI", 10)
    )

    style.map(
        "Treeview",
        background=[("selected", "#3aaed8")],
        foreground=[("selected", "white")]
    )

    def search_and_refresh(*_):
        q = search_var.get().strip().lower()

        if not q:
            refresh_table(all_customer_rows)
            return

        matched = []
        others = []

        for row in all_customer_rows:
            name  = str(row[1]).lower()
            phone = str(row[2]).lower()

            if q in name or q in phone:
                matched.append(row)
            else:
                others.append(row)

        refresh_table(matched + others)


    search_var.trace_add("write", search_and_refresh)



    def select_first(event=None):
        items = tree_customers.get_children()
        if items:
            tree_customers.selection_set(items[0])
            tree_customers.focus(items[0])

    search_entry.bind("<Return>", select_first)

# row eduted functions

    EDITABLE_COLS = {
        1: "customer_name",   # Name
        2: "phone_1",         # Phone
        3: "address"          # Address
    }

    def start_inline_edit(event):
        global edit_entry, editing_info

        region = tree_customers.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree_customers.identify_row(event.y)
        col_id = tree_customers.identify_column(event.x)

        col_index = int(col_id.replace("#", "")) - 1

        # 🔒 only allow Name / Phone / Address
        if col_index not in (1, 2, 3):
            return

        bbox = tree_customers.bbox(row_id, col_id)
        if not bbox:
            return

        x, y, w, h = bbox
        value = tree_customers.item(row_id, "values")[col_index]

        edit_entry = tk.Entry(tree_customers)
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.insert(0, value)
        edit_entry.focus()

        editing_info = {
            "row": row_id,
            "col": col_index
        }

        edit_entry.bind("<Return>", save_inline_edit)
        edit_entry.bind("<Escape>", cancel_inline_edit)
        edit_entry.bind("<FocusOut>", cancel_inline_edit)

            

    def save_inline_edit(event=None):
        global edit_entry, editing_info

        if not edit_entry:
            return

        new_value = edit_entry.get().strip()
        row_id = editing_info["row"]
        col = editing_info["col"]

        values = list(tree_customers.item(row_id, "values"))
        values[col] = new_value
        tree_customers.item(row_id, values=values)

        customer_id = values[0]

        # 🔥 UPDATE DB
        conn = get_connection()
        cur = conn.cursor()

        if col == 1:
            cur.execute(
                "UPDATE customers SET customer_name=%s WHERE customer_id=%s",
                (new_value, customer_id)
            )
        elif col == 2:
            cur.execute(
                "UPDATE customers SET phone_1=%s WHERE customer_id=%s",
                (new_value, customer_id)
            )
        elif col == 3:
            cur.execute(
                "UPDATE customers SET address=%s WHERE customer_id=%s",
                (new_value, customer_id)
            )

        conn.commit()
        conn.close()

        edit_entry.destroy()
        edit_entry = None



    def cancel_inline_edit(event=None):
        global edit_entry
        if edit_entry:
            edit_entry.destroy()
            edit_entry = None
            
    tree_customers.bind("<Double-1>", start_inline_edit)

    def on_customer_click(event):
        region = tree_customers.identify_region(event.x, event.y)
        if region != "cell":
            return

        row_id = tree_customers.identify_row(event.y)
        col_id = tree_customers.identify_column(event.x)

        if not row_id:
            return

        # only "Details" column
        if col_id != f"#{len(tree_customers['columns'])}":
            return

        values = tree_customers.item(row_id, "values")
        if not values:
            return

        try:
            customer_id = int(values[0])   # ✅ CORRECT
        except:
            return

        open_customer_detail(workspace, shop_id, customer_id)



    tree_customers.bind("<ButtonRelease-1>", on_customer_click)
    

        # customer view 
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta

sort_high_to_low = False

# =====================================================
# LOAD CUSTOMER LIST
# =====================================================
def load_customers(tree, shop_id):
    tree.delete(*tree.get_children())

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.customer_id,
            c.customer_name,
            c.phone_1,
            c.address,
            COALESCE(SUM(s.total_amount), 0) AS total_spent,
            c.lifetime_total,
            c.current_points,          -- ✅ USE CURRENT POINTS
            MAX(s.date_time)
        FROM customers c
        LEFT JOIN sales s 
            ON s.customer_id = c.customer_id
            AND s.shop_id = c.shop_id
        WHERE c.shop_id = %s
        GROUP BY
            c.customer_id,
            c.customer_name,
            c.phone_1,
            c.address,
            c.lifetime_total,
            c.current_points
        ORDER BY MAX(s.date_time) DESC
    """, (shop_id,))

    rows = cur.fetchall()
    conn.close()

    for r in rows:
        tree.insert(
            "",
            "end",
            iid=str(r[0]),  # ✅ customer_id
            values=(
                r[0],              # customer_id
                r[1],              # name
                r[2],              # phone
                r[3] or "-",       # address
                f"₹ {r[4]:.2f}",   # total spent
                f"₹ {r[5]:.2f}",   # lifetime total
                r[6],              # ✅ CURRENT POINTS
                "View"
            )
        )

def open_customer_detail(workspace, shop_id, customer_id):
    import tkinter as tk
    from tkinter import ttk
    from datetime import datetime

    # clear old screen
    for w in workspace.winfo_children():
        w.destroy()

    # ================= ROOT =================
    root = tk.Frame(workspace, bg="#F8FAFC")
    root.pack(fill="both", expand=True)

    # ================= HEADER =================
    header = tk.Frame(root, bg="#1e293b", height=45)
    header.pack(fill="x")

    tk.Label(
        header,
        text="👤 Customer Details",
        bg="#1e293b",
        fg="white",
        font=("Segoe UI", 14, "bold")
    ).pack(side="left", padx=15)

    tk.Button(
        header,
        text="✖",
        bg="#1e293b",
        fg="white",
        font=("Segoe UI", 12, "bold"),
        bd=0,
        command=lambda: open_customer_window(workspace, shop_id)
    ).pack(side="right", padx=12)

    # ================= SCROLL AREA =================
   # ================= SCROLL AREA =================
    container = tk.Frame(root, bg="#F8FAFC")
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg="#F8FAFC", highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    # frame inside canvas
    scroll_frame = tk.Frame(canvas, bg="#F8FAFC")

    canvas_window = canvas.create_window(
        (0, 0),
        window=scroll_frame,
        anchor="nw"
    )

    # ---------- FIX: update scroll region properly ----------
    def on_frame_configure(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)

    # force layout update (VERY IMPORTANT)
    scroll_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.yview_moveto(0)

        # ================= MOUSE SCROLL SUPPORT =================
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_linux_up(event):
        canvas.yview_scroll(-1, "units")

    def _on_linux_down(event):
        canvas.yview_scroll(1, "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", _on_linux_up)
    canvas.bind_all("<Button-5>", _on_linux_down)

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    scroll_frame.bind("<Configure>", on_frame_configure)

    # ================= FETCH CUSTOMER =================
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            customer_name,
            phone_1,
            phone_2,
            address,
            email,
            last_purchase_datetime,
            last_purchase_amount,
            lifetime_total,
            total_points,
            current_points,
            spent_points,
            created_at,
            updated_at
        FROM customers
        WHERE customer_id=%s AND shop_id=%s
    """, (customer_id, shop_id))

    row = cur.fetchone()
    conn.close()

    if not row:
        tk.Label(scroll_frame, text="Customer not found", fg="red").pack()
        return

    (
        name, phone1, phone2, address, email,
        last_dt, last_amt,
        lifetime_total,
        total_points,
        current_points,
        spent_points,
        created_at, updated_at
    ) = row

    # ================= PROFILE CARD =================
    card = tk.Frame(
        scroll_frame,
        bg="white",
        highlightbackground="#CBD5E1",
        highlightthickness=1
    )
    card.pack(fill="x", padx=25, pady=20)

    tk.Label(
        card,
        text="CUSTOMER PROFILE",
        bg="white",
        fg="#eb0404",
        font=("Segoe UI", 12, "bold")
    ).grid(row=0, column=0, columnspan=4, pady=(12, 15))

    def field(label, value, r, c):
        tk.Label(
            card,
            text=label,
            bg="white",
            fg="#475569",
            font=("Segoe UI", 10, "bold")
        ).grid(row=r, column=c*2, sticky="w", padx=25, pady=6)

        tk.Label(
            card,
            text=value if value not in ("", None) else "-",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10)
        ).grid(row=r, column=c*2 + 1, sticky="w", padx=6)

    # ===== GRID DATA =====
    field("Customer ID", customer_id, 1, 0)
    field("Phone 1", phone1, 1, 1)

    field("Customer Name", name, 2, 0)
    field("Phone 2", phone2, 2, 1)

    field("Email", email, 3, 0)
    field("Status", "ACTIVE", 3, 1)

    field("Address", address, 4, 0)

    field("Total Points", total_points, 5, 0)
    field("Current Points", current_points, 5, 1)

    field("Spent Points", spent_points, 6, 0)
    field("Lifetime Total", f"₹ {lifetime_total:.2f}", 6, 1)

    field("Last Purchase", f"₹ {last_amt:.2f}", 7, 0)
    field(
        "Last Purchase Date",
        last_dt.strftime("%d-%m-%Y %I:%M %p") if last_dt else "-",
        7, 1
    )

    field("Created At", created_at.strftime("%d-%m-%Y %I:%M %p"), 8, 0)
    field("Updated At", updated_at.strftime("%d-%m-%Y %I:%M %p"), 8, 1)

    # ================= BILL HISTORY TITLE =================
    tk.Label(
        scroll_frame,
        text="CUSTOMER BILL HISTORY",
        bg="#F8FAFC",
        fg="#e00404",
        font=("Segoe UI", 13, "bold")
    ).pack(anchor="w", padx=20, pady=(15, 6))


    # ================= FILTER BAR (BELOW TITLE) =================
    filter_row = tk.Frame(scroll_frame, bg="white")
    filter_row.pack(fill="x", padx=20, pady=(5, 10))


    tk.Label(
        filter_row,
        text="Search:",
        bg="white",
        fg="black"
    ).grid(row=0, column=0, padx=(0, 6), sticky="w")


    search_var = tk.StringVar()

    search_entry = tk.Entry(
        filter_row,
        textvariable=search_var,
        width=26,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.grid(row=0, column=1, padx=(0, 12), sticky="w")


    def fixed_box(parent, w=90, h=30):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.grid_propagate(False)
        return box
    
    from datetime import datetime
    import re

    def normalize_date(text):
        if not text:
            return None

        # remove all non-numeric characters
        digits = re.sub(r"\D", "", text)

        # -------------------------
        # 8 DIGITS CASE
        # -------------------------
        if len(digits) == 8:
            # YYYYMMDD
            try:
                return datetime.strptime(digits, "%Y%m%d").strftime("%Y-%m-%d")
            except:
                pass

            # DDMMYYYY
            try:
                return datetime.strptime(digits, "%d%m%Y").strftime("%Y-%m-%d")
            except:
                pass

        # -------------------------
        # 7 DIGITS CASE
        # -------------------------
        if len(digits) == 7:
            # DMMYYYY → 1122026 → 1-12-2026
            try:
                d = digits[0]
                m = digits[1:3]
                y = digits[3:]
                return datetime.strptime(f"{d}-{m}-{y}", "%d-%m-%Y").strftime("%Y-%m-%d")
            except:
                pass

            # DD MYYYY → 212026 → 21-2-026 ❌ invalid → skip safely
            try:
                d = digits[:2]
                m = digits[2]
                y = digits[3:]
                return datetime.strptime(f"{d}-{m}-{y}", "%d-%m-%Y").strftime("%Y-%m-%d")
            except:
                pass

        # -------------------------
        # 6 DIGITS CASE
        # -------------------------
        if len(digits) == 6:
            # DDMMYY → 010126
            try:
                d = digits[:2]
                m = digits[2:4]
                y = "20" + digits[4:]
                return datetime.strptime(f"{d}-{m}-{y}", "%d-%m-%Y").strftime("%Y-%m-%d")
            except:
                pass

            # D M YYYY → 112026
            try:
                d = digits[0]
                m = digits[1]
                y = digits[2:]
                return datetime.strptime(f"{d}-{m}-{y}", "%d-%m-%Y").strftime("%Y-%m-%d")
            except:
                pass

        return None



    def auto_search_bill(event=None):
        global sort_high_to_low   # 🔥 MUST

        query = search_var.get().strip()

        digits = re.sub(r"\D", "", query)
        date_value = normalize_date(query)

        conn = get_connection()
        cur = conn.cursor()

        sql = """
            SELECT sale_id, date_time, total_amount,
                given_amount, return_amount, points_added
            FROM sales
            WHERE customer_id=%s AND shop_id=%s
        """
        params = [customer_id, shop_id]

        # ---------- SEARCH ----------
        if query:
            if digits and not date_value:
                sql += " AND sale_id LIKE %s"
                params.append(f"%{digits}%")
            elif date_value:
                sql += " AND DATE(date_time)=%s"
                params.append(date_value)

        # ---------- SORT ----------
        if sort_high_to_low:
            sql += " ORDER BY total_amount DESC"
        else:
            sql += " ORDER BY date_time DESC"

        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        bill_tree.delete(*bill_tree.get_children())

        for r in rows:
            bill_tree.insert(
                "",
                "end",
                values=(
                    r[0],
                    r[1].strftime("%d-%m-%Y %I:%M %p"),
                    f"₹ {r[2]:.2f}",
                    f"₹ {r[3]:.2f}",
                    f"₹ {r[4]:.2f}",
                    f"+{r[5]}",
                    "👁"
                )
            )


        

    def load_bill_history():
        global sort_high_to_low
        sort_high_to_low = False
        btn_sort.config(text="High → Low", bg="#2e28a7")
        search_var.set("")      # clear search
        auto_search_bill()


        for item in bill_tree.get_children():
            bill_tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT sale_id, date_time, total_amount,
                given_amount, return_amount, points_added
            FROM sales
            WHERE customer_id=%s AND shop_id=%s
            ORDER BY date_time DESC
        """, (customer_id, shop_id))

        for r in cur.fetchall():
            bill_tree.insert(
                "",
                "end",
                values=(
                    r[0],
                    r[1].strftime("%d-%m-%Y %I:%M %p"),
                    f"₹ {r[2]:.2f}",
                    f"₹ {r[3]:.2f}",
                    f"₹ {r[4]:.2f}",
                    f"+{r[5]}",
                    "👁"
                )
            )

        conn.close()

    search_var.trace_add("write", lambda *args: auto_search_bill())

        

    # ---------- ACTION ROW ----------
    action_row = tk.Frame(filter_row, bg="white")
    action_row.grid(row=0, column=2, sticky="w")


    # High → Low
    box_sort = fixed_box(action_row, 90, 30)
    box_sort.grid(row=0, column=0, padx=4)

    sort_high_to_low = False
    sort_text = tk.StringVar(value="High → Low")  # 🔥 KEY FIX

    def toggle_sort_by_points():
        global sort_high_to_low
        sort_high_to_low = not sort_high_to_low

        if sort_high_to_low:
            sort_text.set("Clear")
            btn_sort.config(bg="#dc2626")
        else:
            sort_text.set("High → Low")
            btn_sort.config(bg="#2e28a7")

        auto_search_bill()

    btn_sort = tk.Button(
        box_sort,
        textvariable=sort_text,
        width=10,              # 🔥 FIXED WIDTH (IMPORTANT)
        bg="#2e28a7",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_sort_by_points
    )
    btn_sort.pack(expand=True)



    # From Date
    box_from = fixed_box(action_row, 130, 30)
    box_from.grid(row=0, column=1, padx=4)

    tk.Label(box_from, text="From", bg="black", fg="white").pack(side="left", padx=3)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")


    # To Date
    box_to = fixed_box(action_row, 130, 30)
    box_to.grid(row=0, column=2, padx=4)

    tk.Label(box_to, text="To", bg="black", fg="white").pack(side="left", padx=3)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")


    # Apply button
    box_apply = fixed_box(action_row, 90, 30)
    box_apply.grid(row=0, column=3, padx=4)
  

    date_filter_active = False  # toggle state

    box_apply = fixed_box(action_row, 90, 30)
    box_apply.grid(row=0, column=3, padx=4)

    date_filter_active = False
    apply_text = tk.StringVar(value="🔍 Apply")

    def toggle_date_filter():
        global date_filter_active

        if not date_filter_active:
            # ✅ APPLY DATE FILTER
            from_dt = start_date.get_date()
            to_dt = end_date.get_date()

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT sale_id, date_time, total_amount,
                    given_amount, return_amount, points_added
                FROM sales
                WHERE customer_id=%s AND shop_id=%s
                AND DATE(date_time) BETWEEN %s AND %s
                ORDER BY date_time DESC
            """, (customer_id, shop_id, from_dt, to_dt))

            rows = cur.fetchall()
            conn.close()

            # clear table
            bill_tree.delete(*bill_tree.get_children())

            for r in rows:
                bill_tree.insert(
                    "",
                    "end",
                    values=(
                        r[0],
                        r[1].strftime("%d-%m-%Y %I:%M %p"),
                        f"₹ {r[2]:.2f}",
                        f"₹ {r[3]:.2f}",
                        f"₹ {r[4]:.2f}",
                        f"+{r[5]}",
                        "👁"
                    )
                )

            apply_text.set("Clear")
            btn_apply.config(bg="#dc2626")
            date_filter_active = True

        else:
            # ✅ CLEAR DATE FILTER (NORMAL STATE)
            apply_text.set("🔍 Apply")
            btn_apply.config(bg="#198754")
            date_filter_active = False

            load_bill_history()   # 🔥 THIS IS THE KEY

    btn_apply = tk.Button(
        box_apply,
        textvariable=apply_text,
        width=10,          # 🔥 FIXED WIDTH
        bg="#198754",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(expand=True)






    # ================= BILL TABLE =================
    bill_box = tk.Frame(scroll_frame, bg="white", highlightbackground="#CBD5E1", highlightthickness=1)
    bill_box.pack(fill="both", expand=True, padx=20, pady=10)

    cols = ("Bill No", "Date", "Total", "Given", "Return", "Points", "View")

    bill_tree = ttk.Treeview(bill_box, columns=cols, show="headings", height=10)
    bill_tree.pack(fill="both", expand=True)

    for c in cols:
        bill_tree.heading(c, text=c)
        bill_tree.column(c, anchor="center", width=120)



    # ---------------- LOAD BILL DATA ----------------
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT sale_id, date_time, total_amount,
            given_amount, return_amount, points_added
        FROM sales
        WHERE customer_id=%s AND shop_id=%s
        ORDER BY date_time DESC
    """, (customer_id, shop_id))


    for r in cur.fetchall():
        bill_tree.insert("", "end", values=(
            r[0],
            r[1].strftime("%d-%m-%Y %I:%M %p"),
            f"₹ {r[2]:.2f}",
            f"₹ {r[3]:.2f}",
            f"₹ {r[4]:.2f}",
            f"+{r[5]}",
            "👁"
        ))


    conn.close()

    # 🔥 IMMEDIATELY AFTER CREATE

    def on_bill_tree_click(event):
        tree = event.widget

        # heading / scrollbar click ignore
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 👁 View column = last column
        if col_id != f"#{len(tree['columns'])}":
            return

        values = tree.item(row_id, "values")
        if not values:
            return

        try:
            sale_id = int(values[0])   # ✅ Bill No
        except:
            return

        open_bill_detail_window(workspace,sale_id,shop_id,customer_id)


    bill_tree.bind("<ButtonRelease-1>", on_bill_tree_click)




import subprocess
from tkinter import messagebox
import tempfile
import os

def open_bill_detail_window(workspace, sale_id, shop_id,customer_id):
    # 🔥 SAFETY: REMOVE OLD GLOBAL SCROLL BINDS
    workspace.unbind_all("<MouseWheel>")
    workspace.unbind_all("<Button-4>")
    workspace.unbind_all("<Button-5>")

    import tkinter as tk
    from tkinter import ttk

    # 🔥 CLEAR WORKSPACE
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")
    # ================= FIXED HEADER =================
    header = tk.Frame(workspace, bg="#1e293b", height=42)
    header.pack(fill="x")

    tk.Label(
        header,
        text="🧾 Bill Details",
        bg="#1e293b",
        fg="white",
        font=("Segoe UI", 13, "bold")
    ).pack(side="left", padx=15)

    tk.Button(
        header,
        text="✖",
        bg="#1e293b",
        fg="white",
        font=("Segoe UI", 12, "bold"),
        bd=0,
        activebackground="#dc2626",
        activeforeground="white",
        command=lambda: open_customer_detail(
            workspace, shop_id, bill["customer_id"]
        )
    ).pack(side="right", padx=15)


    # ================= FETCH DATA =================
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            s.sale_id,
            s.customer_id,
            s.date_time,
            s.total_amount,
            s.given_amount,
            s.return_amount,
            s.points_added,
            c.customer_name,
            c.phone_1
        FROM sales s
        JOIN customers c ON c.customer_id = s.customer_id
        WHERE s.sale_id = %s AND s.shop_id = %s
    """, (sale_id, shop_id))
    bill = cur.fetchone()

    cur.execute("""
        SELECT
            si.product_id,
            si.name,
            p.mrp_rate AS mrp,
            si.price,
            si.quantity,
            si.subtotal
        FROM sales_items si
        JOIN products p ON p.product_id = si.product_id
        WHERE si.sale_id = %s
    """, (sale_id,))
    items = cur.fetchall()
    conn.close()

    # ================= STYLE =================
    style = ttk.Style()
    style.configure("Treeview.Heading",
        font=("Segoe UI", 11, "bold"),
        background="#0EA5E9",
        foreground="white"
    )
    style.configure("Treeview",
        font=("Segoe UI", 10),
        rowheight=28
    )



    # ================= MAIN CARD =================
    card = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#22D3EE",
        highlightthickness=2
    )
    card.pack(fill="both", expand=True, padx=20, pady=20)

    # grid layout inside card
    card.rowconfigure(2, weight=1)   # ONLY table row expands
    card.columnconfigure(0, weight=1)

    # ================= INFO BOX =================
    info_box = tk.Frame(
        card,
        bg="white",
        highlightbackground="#CBD5E1",
        highlightthickness=1
    )
    info_box.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))

    info_box.columnconfigure(1, weight=1)
    info_box.columnconfigure(3, weight=1)

    def info_row(label, value, r, c):
        tk.Label(
            info_box, text=label,
            bg="white", fg="#475569",
            font=("Segoe UI", 10, "bold")
        ).grid(row=r, column=c*2, sticky="w", padx=15, pady=6)

        tk.Label(
            info_box, text=value,
            bg="white", fg="#0F172A",
            font=("Segoe UI", 10)
        ).grid(row=r, column=c*2+1, sticky="w", padx=6, pady=6)

    info_row("Bill No", bill["sale_id"], 0, 0)
    info_row("Date & Time", bill["date_time"].strftime("%d-%m-%Y %I:%M %p"), 0, 1)
    info_row("Customer", bill["customer_name"], 1, 0)
    info_row("Phone", bill["phone_1"], 1, 1)

    # ================= TABLE =================
    table_box = tk.Frame(card, bg="white")
    table_box.grid(row=2, column=0, sticky="nsew", padx=30, pady=10)

    table_box.rowconfigure(0, weight=1)
    table_box.columnconfigure(0, weight=1)

    cols = ("no", "pid", "name", "mrp", "price", "qty", "amount")

    bill_items_tree = ttk.Treeview(
        table_box,
        columns=cols,
        show="headings"
    )

    scroll = ttk.Scrollbar(
        table_box,
        orient="vertical",
        command=bill_items_tree.yview
    )

    bill_items_tree.configure(yscrollcommand=scroll.set)

    bill_items_tree.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    for c, t in zip(
        cols,
        ["No", "P.ID", "Product Name", "MRP", "Price", "Qty", "Amount"]
    ):
        bill_items_tree.heading(c, text=t)

    bill_items_tree.column("no", width=60, anchor="center", stretch=False)
    bill_items_tree.column("pid", width=80, anchor="center", stretch=False)
    bill_items_tree.column("name", anchor="w")
    bill_items_tree.column("mrp", width=120, anchor="e")
    bill_items_tree.column("price", width=120, anchor="e")
    bill_items_tree.column("qty", width=80, anchor="center")
    bill_items_tree.column("amount", width=140, anchor="e")

    bill_items_tree.tag_configure("odd", background="white")
    bill_items_tree.tag_configure("even", background="#F1F5F9")

    for i, it in enumerate(items, start=1):
        bill_items_tree.insert(
            "",
            "end",
            values=(
                i,
                it["product_id"],
                it["name"],
                f"₹ {it['mrp']:.2f}",
                f"₹ {it['price']:.2f}",
                it["quantity"],
                f"₹ {it['subtotal']:.2f}"
            ),
            tags=("even" if i % 2 == 0 else "odd",)
        )

    # ================= TOTAL BAR (HORIZONTAL – LIKE IMAGE) =================
    # ================= HORIZONTAL TOTAL STRIP (EXACT FORMAT) =================
    total_strip = tk.Frame(
        card,
        bg="#F8FAFC",
        highlightbackground="#CBD5E1",
        highlightthickness=1,
        height=45
    )
    total_strip.grid(row=3, column=0, sticky="ew", padx=30, pady=(8, 12))
    total_strip.grid_propagate(False)

    # 3 sections in one line
    total_strip.columnconfigure(0, weight=1)
    total_strip.columnconfigure(1, weight=1)
    total_strip.columnconfigure(2, weight=1)

    def strip_item(col, label, value):
        frame = tk.Frame(total_strip, bg="#F8FAFC")
        frame.grid(row=0, column=col, sticky="w", padx=15)

        tk.Label(
            frame,
            text=f"{label} :",
            font=("Segoe UI", 10, "bold"),
            fg="#334155",
            bg="#F8FAFC"
        ).pack(side="left")

        tk.Label(
            frame,
            text=value,
            font=("Segoe UI", 11),
            fg="#0F172A",
            bg="#F8FAFC"
        ).pack(side="left", padx=(6, 0))

    strip_item(0, "TOTAL", f"₹ {bill['total_amount']:.2f}")
    strip_item(1, "Customer Give", f"₹ {bill['given_amount']:.2f}")
    strip_item(2, "Return", f"₹ {bill['return_amount']:.2f}")




    # ================= ACTION BUTTONS =================
    # ================= ACTION BUTTONS =================

    # ================= ACTION BUTTONS =================
    actions = tk.Frame(card, bg="white")
    actions.grid(row=4, column=0, sticky="ew", padx=30, pady=15)

    # card grid setup
    card.rowconfigure(2, weight=1)   # table only expand
    card.columnconfigure(0, weight=1)

    info_box.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
    table_box.grid(row=2, column=0, sticky="nsew", padx=30, pady=10)
    # footer.grid(row=3, column=0, sticky="ew", padx=30, pady=10)
    actions.grid(row=4, column=0, sticky="ew", padx=30, pady=15)
    


    # ---------------- DB ----------------
  
    def print_bill():
        import os, subprocess, tempfile
        from tkinter import messagebox

        try:
            # ===============================
            # 🔍 HARD PRINTER VALIDATION (LINUX)
            # ===============================
            if os.name != "nt":

                # 1️⃣ CUPS running?
                cups = subprocess.run(
                    ["lpstat", "-r"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if b"running" not in cups.stdout.lower():
                    raise Exception("CUPS_NOT_RUNNING")

                # 2️⃣ Default printer exists?
                default = subprocess.run(
                    ["lpstat", "-d"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if b"no system default destination" in default.stdout.lower():
                    raise Exception("NO_DEFAULT_PRINTER")

                # 3️⃣ Printer enabled + accepting?
                printers = subprocess.run(
                    ["lpstat", "-p"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                text = printers.stdout.decode().lower()
                if "disabled" in text or "rejecting jobs" in text:
                    raise Exception("PRINTER_DISABLED")

            # ===============================
            # 🧾 CREATE BILL CONTENT
            # ===============================
            content = ""
            content += "==========================================\n"
            content += f"BILL NO : {bill['sale_id']}\n"
            content += f"DATE    : {bill['date_time'].strftime('%d-%m-%Y %I:%M %p')}\n"
            content += f"CUSTOMER: {bill['customer_name']}\n"
            content += f"PHONE   : {bill['phone_1']}\n"
            content += "==========================================\n"

            # ---------- ITEMS HEADER ----------
            content += "No  Product        MRP  Price Qty Amount\n"
            content += "------------------------------------------\n"

            # ---------- ITEMS ----------
            for i, it in enumerate(items, start=1):
                content += (
                    f"{i:<3} "
                    f"{it['name'][:12]:<12} "
                    f"{int(it['mrp']):>4} "
                    f"{int(it['price']):>5} "
                    f"{it['quantity']:>3} "
                    f"{int(it['subtotal']):>6}\n"
                )

            content += "------------------------------------------\n"
            content += f"TOTAL  : ₹{bill['total_amount']}\n"
            content += f"GIVEN  : ₹{bill['given_amount']}\n"
            content += f"RETURN : ₹{bill['return_amount']}\n"
            content += f"POINTS : +{bill['points_added']}\n"
            content += "==========================================\n"

            # ===============================
            # 🖨 WRITE TO TEMP FILE
            # ===============================
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            temp.write(content.encode())
            temp.close()

            # ===============================
            # 🖨 SEND TO PRINTER
            # ===============================
            if os.name == "nt":
                os.startfile(temp.name, "print")
            else:
                subprocess.run(["lp", temp.name], check=True)

            messagebox.showinfo("Printed", "🖨 Bill sent to printer")

        except Exception:
            messagebox.showerror(
                "Printer Error",
                "❌ Please connect the printer and try again"
            )

            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            temp.write(content.encode())
            temp.close()

            # ===============================
            # 🖨 SEND TO PRINTER
            # ===============================
            if os.name == "nt":
                import win32print
                printer = win32print.GetDefaultPrinter()
                if not printer:
                    raise Exception("NO_PRINTER")
                os.startfile(temp.name, "print")
            else:
                result = subprocess.run(
                    ["lp", temp.name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # 🔥 FINAL SAFETY
                if result.returncode != 0:
                    raise Exception("PRINT_FAILED")

            messagebox.showinfo("Printed", "🖨 Bill sent to printer")

        except Exception:
            messagebox.showerror(
                "Printer Error",
                "❌ Printer not connected / disabled\nPlease connect printer and try again"
            )

    tk.Button(
        actions,
        text="🖨 Print Bill",
        width=14,
        bg="#16A34A",
        fg="white",
        command=print_bill
    ).pack(side="right")

    workspace.bind_all("<Shift-Return>", lambda e: print_bill())

    


  
mode = "ADD"
def open_add_customer_window(workspace, shop_id):
    import tkinter as tk
    from tkinter import messagebox
    current_customer_id = tk.IntVar(value=0)

  # customer_id

    
    ERROR = "#dc2626"
    SELECTED = "#"#ffffff"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"


    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="your_password",
            database="billing_db"
        )

    # -------------------------------
    # CLEAR WORKSPACE
    # -------------------------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="#ffffff")

    # -------------------------------
    # MAIN WINDOW (CENTER)
    # -------------------------------
    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#2563eb",
        highlightthickness=2
    )
    win.place(relx=0.5, rely=0.5, anchor="center", width=520, height=560)

    is_maximized = False
    mode = tk.StringVar(value="ADD")
    selected_customer_id = None

    # -------------------------------
    # TOP TITLE BAR (RIGHT CONTROLS)
    # -------------------------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def minimize():
        win.destroy()
        open_customer_window(workspace, shop_id)


    def toggle_zoom():
        nonlocal is_maximized
        if not is_maximized:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=workspace.winfo_width()-40,
                      height=workspace.winfo_height()-40)
            is_maximized = True
        else:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=520, height=560)
            is_maximized = False

    def close_window():
        win.destroy()
        open_customer_window(workspace, shop_id)

    tk.Button(
        title_bar, text="✖", width=3, bd=0,
        bg="black", fg="red",
        command=close_window
    ).pack(side="right")

    tk.Button(
        title_bar, text="⛶", width=3, bd=0,
        bg="black",
        command=toggle_zoom
    ).pack(side="right")

    tk.Button(
        title_bar, text="➖", width=3, bd=0,
        bg="black",
        command=minimize
    ).pack(side="right")

    
    def clear_customer_form():
        name_var.set("")
        phone1_var.set("")
        phone2_var.set("")
        email_var.set("")

        address_txt.delete("1.0", tk.END)


    # -------------------------------
    # TOP MODE BUTTONS
    # -------------------------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_buttons():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Customer")
            search_row.pack_forget()

            clear_customer_form(reset_id=True)

            add_btn.config(bg=SELECTED_COLOR, fg="white", text="✔ Add Customer")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR, text="Update Customer")
            save_btn.config(text="💾 Save Customer")

        else:
            header_lbl.config(text="Update Customer")

            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))

            clear_customer_form(reset_id=False)

            upd_btn.config(bg=SELECTED_COLOR, fg="white", text="✔ Update Customer")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR, text="Add Customer")
            save_btn.config(text="💾 Update Customer")



    add_btn = tk.Button(
        top_bar, text="Add Customer",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        relief="solid", bd=1,
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_buttons()]
    )
    add_btn.pack(side="left", padx=6)

# update button
    upd_btn = tk.Button(
        top_bar, text="Update Customer",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        relief="solid", bd=1,
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_buttons()]
    )
    upd_btn.pack(side="left", padx=6)

#  search bar 

     # -------------------------------
    # SEARCH
    # -------------------------------
    search_var = tk.StringVar()
    search_row = tk.Frame(win, bg="white")

    tk.Label(search_row, text="Search (Phone / Name)",
             width=18, anchor="w", bg="white").pack(side="left")

    search_entry = tk.Entry(search_row, textvariable=search_var,
                            width=30, relief="solid", bd=1)
    search_entry.pack(side="left")
    search_var = tk.StringVar()

    search_row = tk.Frame(win, bg="white")

    tk.Label(
        search_row,
        text="Search (Phone / Name):",
        bg="white",
        fg="black",
        font=("Segoe UI", 9),
        width=20,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",        # ✅ background white
        fg="black",        # ✅ text black
        insertbackground="black",  # ✅ cursor black (IMPORTANT)
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")
    



    # -------------------------------
    # HEADER
    # -------------------------------
    header_lbl = tk.Label(
        win,
        text="Add Customer",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))

    # -------------------------------
    # FORM CARD
    # -------------------------------
    card = tk.Frame(win, bg="white")
    card.pack(fill="both", expand=True, padx=22)

    entry_widgets = []   # 🔥 global list inside function

    def field(label):
        var = tk.StringVar()

        row = tk.Frame(card, bg="white")
        row.pack(fill="x", pady=6)

        tk.Label(
            row, text=label,
            bg="white", fg="black",
            width=18, anchor="w"
        ).pack(side="left")

        entry = tk.Entry(
            row,
            textvariable=var,
            width=30,
            bg="white",
            relief="solid",
            bd=1,
            fg="black"   # ✅ text always black
        )
        entry.pack(side="left", padx=6)

        entry_widgets.append(entry)   # ⭐ store order

        return var, entry





    # -------------------------------
    # FORM FIELDS
    # -------------------------------
    name_var, name_entry     = field("Customer Name")
    phone1_var, phone1_entry = field("Phone 1")
    phone2_var, phone2_entry = field("Phone 2")
    email_var, email_entry   = field("Email ID")

    # -------------------------------
    # ADDRESS ROW (FIXED ALIGNMENT)
    # -------------------------------
    addr_row = tk.Frame(card, bg="white")
    addr_row.pack(fill="x", pady=(10, 4))

    tk.Label(
        addr_row,
        text="Address",
        bg="white",
        fg="black",
        width=18,          # 🔥 SAME AS OTHER LABELS
        anchor="nw"
    ).pack(side="left")

    address_txt = tk.Text(
        addr_row,
        height=4,
        width=30,
        bg="white",
        fg="black",                 # ✅
        insertbackground="black",   # ✅
        relief="solid",
        bd=1
    )

    address_txt.pack(side="left", padx=6)

    error_lbl = tk.Label(card, text="", fg=ERROR, bg="white")
    error_lbl.pack()

        # -------------------------------
    # DB FUNCTIONS
    # -------------------------------
    def clear_customer_form(reset_id=True):
        if reset_id:
            current_customer_id.set(0)

        name_var.set("")
        phone1_var.set("")
        phone2_var.set("")
        email_var.set("")
        address_txt.delete("1.0", "end")
        error_lbl.config(text="")


    def load_customer(data):
        nonlocal selected_customer_id
        selected_customer_id = data["customer_id"]
        name_var.set(data["customer_name"])
        phone1_var.set(data["phone_1"])
        phone2_var.set(data["phone_2"] or "")
        email_var.set(data["email"] or "")
        address_txt.delete("1.0", "end")
        address_txt.insert("1.0", data["address"] or "")
    def search_customer(*_):
        text = search_var.get().strip()

        if not text:
            return

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM customers
            WHERE shop_id=%s
            AND (phone_1 LIKE %s OR customer_name LIKE %s)
            LIMIT 1
        """, (shop_id, f"%{text}%", f"%{text}%"))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showinfo("Not Found", "Customer not found")
            return

        # ✅ VERY IMPORTANT LINE
        current_customer_id.set(row["customer_id"])

        name_var.set(row["customer_name"])
        phone1_var.set(row["phone_1"])
        phone2_var.set(row.get("phone_2") or "")
        email_var.set(row.get("email") or "")
        address_txt.delete("1.0", "end")
        address_txt.insert("1.0", row.get("address") or "")

        mode.set("UPDATE")
        update_mode_buttons()


    # focus 
    def focus_next_from_search(event=None):
        name_entry.focus_set()
        return "break"


    def focus_next(event):
        widget = event.widget

        if widget in entry_widgets:
            idx = entry_widgets.index(widget)

            if idx + 1 < len(entry_widgets):
                entry_widgets[idx + 1].focus_set()
            else:
                address_txt.focus_set()

        return "break"

   
    
    def save_customer():
        name = name_var.get().strip()
        phone1 = phone1_var.get().strip()
        phone2 = phone2_var.get().strip()
        email = email_var.get().strip()
        address = address_txt.get("1.0", "end").strip()

        if not name or not phone1:
            messagebox.showwarning("Missing", "Customer Name & Phone required")
            return

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            # 🔍 check existing customer by phone
            cur.execute("""
                SELECT customer_id
                FROM customers
                WHERE shop_id = %s AND phone_1 = %s
            """, (shop_id, phone1))

            row = cur.fetchone()

            if row:
                # ✅ UPDATE existing customer
                customer_id = row["customer_id"]

                cur.execute("""
                    UPDATE customers
                    SET
                        customer_name=%s,
                        phone_2=%s,
                        email=%s,
                        address=%s
                    WHERE customer_id=%s AND shop_id=%s
                """, (
                    name,
                    phone2 or None,
                    email or None,
                    address or None,
                    customer_id,
                    shop_id
                ))

                messagebox.showinfo("Success", "✅ Customer updated successfully")

            else:
                # ✅ INSERT new customer
                cur.execute("""
                    INSERT INTO customers
                    (shop_id, customer_name, phone_1, phone_2, email, address)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    shop_id,
                    name,
                    phone1,
                    phone2 or None,
                    email or None,
                    address or None
                ))

                messagebox.showinfo("Success", "✅ Customer added successfully")

            conn.commit()

            # reset form
            current_customer_id.set(0)
            name_var.set("")
            phone1_var.set("")
            phone2_var.set("")
            email_var.set("")
            address_txt.delete("1.0", "end")

            mode.set("ADD")
            update_mode_buttons()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            cur.close()
            conn.close()


            

        clear_customer_form()

    # -------------------------------
    # SAVE BUTTON
    # -------------------------------
    save_btn = tk.Button(
        win,
        text="💾 Save Customer",
        bg=SELECTED_COLOR,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18,
        pady=6,
        command=save_customer
    )
    save_btn.pack(pady=10)

    win.bind("<Control-s>", lambda e: save_customer())


   

    update_mode_buttons()
    def auto_search_customer(event=None):
        text = search_var.get().strip()

        if len(text) < 3:
            return   # 3 letters-ku mela type panna thaan search

        conn = get_connection()
        if not conn:
            return

        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT customer_name, phone_1, phone_2, email, address
            FROM customers
            WHERE shop_id = %s
            AND (phone_1 LIKE %s OR customer_name LIKE %s)
            LIMIT 1
        """, (
            shop_id,
            f"%{text}%",
            f"%{text}%"
        ))

        row = cur.fetchone()
        conn.close()

        if row:
            name_var.set(row["customer_name"])
            phone1_var.set(row["phone_1"])
            phone2_var.set(row["phone_2"] or "")
            email_var.set(row["email"] or "")

            address_txt.delete("1.0", tk.END)
            address_txt.insert("1.0", row["address"] or "")


    search_entry.bind("<KeyRelease>", auto_search_customer)




def open_suppliers(workspace, shop_id):
    import tkinter as tk
    from tkinter import ttk
    import mysql.connector

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ===== CLEAR WORKSPACE =====
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="#F8FAFC")

    # ===== PAGE BORDER =====
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#20C4E5",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ===== TITLE =====
    tk.Label(
        main,
        text="Suppliers Details",
        font=("Arial", 12, "bold"),
        fg="#20C4E5",
        bg="white"
    ).pack(pady=(15, 8))

    # ===== SEARCH BAR + ADD BUTTON =====
    top_bar = tk.Frame(main, bg="white")
    top_bar.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(
        top_bar,
        text="Search :",
        bg="white",
        fg="black",
        font=("Arial", 10, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        top_bar,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black"
    )
    search_entry.pack(side="left", padx=10)

    tk.Button(
        top_bar,
        text="Add Supplier",
        bg="#20C4E5",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12,
        relief="flat",
        command=lambda: open_add_supplier_window(workspace, shop_id)
    ).pack(side="left")


    # ===== TABLE =====
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    columns = (
        "ID", "Name", "Phone 1", "Phone 2",
        "Email ID", "Address", "Company", "Join Date"
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    widths = [60, 120, 120, 120, 180, 180, 150, 110]
    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tree.tag_configure("odd", background="#F8FAFC")
    tree.tag_configure("even", background="#80C4E7")
    tree.tag_configure("search_hit", background="#53EA88")


    # ===== LOAD SUPPLIERS FROM MYSQL =====
    def load_suppliers(search=""):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        if search:
            cur.execute("""
                SELECT supplier_id, supplier_name, phone1, phone2,
                    supplier_email, address, company_name, join_date
                FROM suppliers
                WHERE shop_id=%s
                AND (supplier_name LIKE %s OR phone1 LIKE %s)
                ORDER BY supplier_id DESC
            """, (shop_id, f"%{search}%", f"%{search}%"))
        else:
            cur.execute("""
                SELECT supplier_id, supplier_name, phone1, phone2,
                    supplier_email, address, company_name, join_date
                FROM suppliers
                WHERE shop_id=%s
                ORDER BY supplier_id DESC
            """, (shop_id,))

        rows = cur.fetchall()
        conn.close()

        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))


    def on_search_key(event):
        # 🚫 ENTER press panninaa reload panna koodadhu
        if event.keysym == "Return":
            return

        load_suppliers(search_var.get().strip())
    search_entry.bind("<KeyRelease>", on_search_key)

    load_suppliers()

    def on_search_enter(event):
        items = tree.get_children()
        if not items:
            return

        # zebra reset
        for i, item in enumerate(items):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        first = items[0]

        tree.selection_set(first)
        tree.focus(first)
        tree.item(first, tags=("search_hit",))


    search_entry.bind("<Return>", on_search_enter)

    def restore_zebra(event):
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


    edit_entry = None

    def on_double_click(event):
        nonlocal edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if not row_id or col == "#1":  # ❌ ID editable illa
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black")
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.insert(0, value)
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get()
            tree.set(row_id, col, new_val)
            edit_entry.destroy()
            update_db(row_id, col, new_val)

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())

    tree.bind("<Double-1>", on_double_click)


    def update_db(row_id, col, value):
        col_map = {
            "#2": "supplier_name",
            "#3": "phone1",
            "#4": "phone2",
            "#5": "supplier_email",
            "#6": "address",
            "#7": "company_name"
        }

        db_col = col_map.get(col)
        if not db_col:
            return

        supplier_id = tree.set(row_id, "#1")

        conn = get_db()
        cur = conn.cursor()

        cur.execute(f"""
            UPDATE suppliers
            SET {db_col}=%s
            WHERE supplier_id=%s AND shop_id=%s
        """, (value, supplier_id, shop_id))

        conn.commit()
        conn.close()

def open_add_supplier_window(workspace, shop_id):
    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date

    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------
    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )
    win.place(relx=0.5, rely=0.5, anchor="center", width=520, height=580)


    is_maximized = False
    mode = tk.StringVar(value="ADD")
    current_supplier_id = tk.IntVar(value=0)

    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_suppliers(workspace,shop_id)

    def toggle_zoom():
        nonlocal is_maximized
        if not is_maximized:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=workspace.winfo_width()-40,
                      height=workspace.winfo_height()-40)
            is_maximized = True
        else:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=520, height=580)
            is_maximized = False

    tk.Button(title_bar, text="✖", width=3, bd=0,
              bg="black", fg="red",
              command=close_window).pack(side="right")

    tk.Button(title_bar, text="⛶", width=3, bd=0,
              bg="black",
              command=toggle_zoom).pack(side="right")

    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Supplier")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Supplier")
            clear_form(reset_id=True)
        else:
            header_lbl.config(text="Update Supplier")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Supplier")

    add_btn = tk.Button(
        top_bar, text="Add Supplier",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Supplier",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    search_var = tk.StringVar()
    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))   # ✅ VERY IMPORTANT

    tk.Label(
        search_row,
        text="Search (Phone / Name):",
        bg="white", fg="black",               # ✅ FIXED
        font=("Segoe UI", 9),
        width=20,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")

   
    # ---------------- HEADER ----------------
    header_lbl = tk.Label(
        win,
        text="Add Supplier",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))

    # ---------------- FORM CARD ----------------
    card = tk.Frame(win, bg="white")
    card.pack(fill="both", expand=True, padx=22, pady=10)   # ✅ extra padding


    def field(label):
        var = tk.StringVar()

        row = tk.Frame(card, bg="white")
        row.pack(fill="x", pady=6)

        tk.Label(
            row,
            text=label,
            bg="white",
            fg="black",        # ✅ force black
            width=18,
            anchor="w",
            font=("Segoe UI", 9)
        ).pack(side="left")

        ent = tk.Entry(
            row,
            textvariable=var,
            width=30,
            bg="white",
            fg="black",
            insertbackground="black",
            relief="solid",
            bd=1
        )
        ent.pack(side="left", padx=6)

        return var


    supplier_name = field("Supplier Name")
    phone1        = field("Phone 1")
    phone2        = field("Phone 2")
    email         = field("Email ID")
    company       = field("Company Name")


    # ---------------- ADDRESS ----------------
    addr_row = tk.Frame(card, bg="white")
    addr_row.pack(fill="x", pady=(10, 4))

    tk.Label(
        addr_row,
        text="Address",
        bg="white",
        fg="black",
        width=18,
        anchor="nw",
        font=("Segoe UI", 9)
    ).pack(side="left")

    address_txt = tk.Text(
        addr_row,
        height=4,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    address_txt.pack(side="left", padx=6)


    # ---------------- HELPERS ----------------
    def clear_form(reset_id=True):
        if reset_id:
            current_supplier_id.set(0)
        supplier_name.set("")
        phone1.set("")
        phone2.set("")
        email.set("")
        company.set("")
        address_txt.delete("1.0", "end")
    

    def search_supplier(*_):
        text = search_var.get().strip()
        if not text:
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM suppliers
            WHERE shop_id=%s
            AND (supplier_name LIKE %s OR phone1 LIKE %s)
            LIMIT 1
        """, (shop_id, f"%{text}%", f"%{text}%"))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showinfo("Not Found", "Supplier not found")
            return

        current_supplier_id.set(row["supplier_id"])
        supplier_name.set(row["supplier_name"])
        phone1.set(row["phone1"])
        phone2.set(row["phone2"] or "")
        email.set(row["supplier_email"] or "")
        company.set(row["company_name"] or "")
        address_txt.delete("1.0", "end")
        address_txt.insert("1.0", row["address"] or "")

        mode.set("UPDATE")
        update_mode_ui()

    search_entry.bind("<KeyRelease>", search_supplier)

    # ---------------- SAVE ----------------
    def save_supplier():
        if not supplier_name.get() or not phone1.get():
            messagebox.showwarning("Missing", "Supplier Name & Phone required")
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            if mode.get() == "UPDATE" and current_supplier_id.get() != 0:
                cur.execute("""
                    UPDATE suppliers SET
                        supplier_name=%s,
                        phone1=%s,
                        phone2=%s,
                        supplier_email=%s,
                        company_name=%s,
                        address=%s
                    WHERE supplier_id=%s AND shop_id=%s
                """, (
                    supplier_name.get(),
                    phone1.get(),
                    phone2.get() or None,
                    email.get() or None,
                    company.get() or None,
                    address_txt.get("1.0", "end").strip() or None,
                    current_supplier_id.get(),
                    shop_id
                ))
                messagebox.showinfo("Success", "✅ Supplier updated")

            else:
                cur.execute("""
                    INSERT INTO suppliers
                    (shop_id, supplier_name, phone1, phone2,
                     supplier_email, company_name, address, join_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    shop_id,
                    supplier_name.get(),
                    phone1.get(),
                    phone2.get() or None,
                    email.get() or None,
                    company.get() or None,
                    address_txt.get("1.0", "end").strip() or None,
                    date.today()
                ))
                messagebox.showinfo("Success", "✅ Supplier added")

            conn.commit()
            clear_form()
            mode.set("ADD")
            update_mode_ui()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()

    # ---------------- SAVE BUTTON ----------------
    save_btn = tk.Button(
        win,
        text="💾 Save Supplier",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18, pady=6,
        command=save_supplier
    )
    save_btn.pack(pady=10)

    update_mode_ui()



def open_staff(workspace, shop_id):
    import tkinter as tk
    from tkinter import ttk
    import mysql.connector

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ===== CLEAR WORKSPACE =====
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="#F8FAFC")

    # ===== PAGE BORDER =====
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#20C4E5",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ===== TITLE =====
    tk.Label(
        main,
        text="Staff Details",
        font=("Arial", 12, "bold"),
        fg="#20C4E5",
        bg="white"
    ).pack(pady=(15, 8))

    # ===== SEARCH BAR + ADD BUTTON =====
    top_bar = tk.Frame(main, bg="white")
    top_bar.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(
        top_bar,
        text="Search :",
        bg="white",
        fg="black",
        font=("Arial", 10, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        top_bar,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black"
    )
    search_entry.pack(side="left", padx=10)

    tk.Button(
        top_bar,
        text="Add Staff",
        bg="#20C4E5",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12,
        relief="flat",
        command=lambda: open_add_staff_window(workspace, shop_id)
    ).pack(side="left")


    # ===== TABLE =====
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    columns = (
        "ID",
        "Name",
        "Password",
        "Phone 1",
        "Phone 2",
        "Email ID",
        "Address",
        "Join Date"
    )


    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    widths = [60, 150, 100, 120, 120, 180, 200, 120]

    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tree.tag_configure("odd", background="#F8FAFC")
    tree.tag_configure("even", background="#80C4E7")
    tree.tag_configure("search_hit", background="#53EA88")


    # ===== LOAD SUPPLIERS FROM MYSQL =====
    def load_staff(search=""):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        if search:
            cur.execute("""
                SELECT staff_id,
                    staff_name,
                    password,
                    phone1,
                    phone2,
                    email,
                    address,
                    join_date
                FROM staff
                WHERE shop_id=%s
                AND (staff_name LIKE %s OR phone1 LIKE %s)
                ORDER BY staff_id DESC
            """, (shop_id, f"%{search}%", f"%{search}%"))
        else:
            cur.execute("""
                SELECT staff_id,
                    staff_name,
                    password,
                    phone1,
                    phone2,
                    email,
                    address,
                    join_date
                FROM staff
                WHERE shop_id=%s
                ORDER BY staff_id DESC
            """, (shop_id,))

        rows = cur.fetchall()
        conn.close()

        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))


    def on_search_key(event):
        # 🚫 ENTER press panninaa reload panna koodadhu
        if event.keysym == "Return":
            return

        load_staff(search_var.get().strip())
    search_entry.bind("<KeyRelease>", on_search_key)

    load_staff()

    def on_search_enter(event):
        items = tree.get_children()
        if not items:
            return

        # zebra reset
        for i, item in enumerate(items):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        first = items[0]

        tree.selection_set(first)
        tree.focus(first)
        tree.item(first, tags=("search_hit",))


    search_entry.bind("<Return>", on_search_enter)

    def restore_zebra(event):
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


    edit_entry = None

    def on_double_click(event):
        nonlocal edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if not row_id or col == "#1":  # ❌ ID editable illa
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black")
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.insert(0, value)
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get()
            tree.set(row_id, col, new_val)
            edit_entry.destroy()
            update_db(row_id, col, new_val)

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())

    tree.bind("<Double-1>", on_double_click)


    def update_db(row_id, col, value):
        col_map = {
            "#2": "staff_name",
            "#3": "password",
            "#4": "phone1",
            "#5": "phone2",
            "#6": "email",
            "#7": "address"
        }

        
        db_col = col_map.get(col)
        if not row_id or col == "#1":
            return

        if not db_col:
            return

        supplier_id = tree.set(row_id, "#1")

        conn = get_db()
        cur = conn.cursor()

        cur.execute(f"""
            UPDATE suppliers
            SET {db_col}=%s
            WHERE supplier_id=%s AND shop_id=%s
        """, (value, supplier_id, shop_id))

        conn.commit()
        conn.close()


def open_add_staff_window(workspace, shop_id):
    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date

    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------
    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )
    win.place(relx=0.5, rely=0.5, anchor="center", width=520, height=580)


    is_maximized = False
    mode = tk.StringVar(value="ADD")
    current_staff_id = tk.IntVar(value=0)  

    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_staff(workspace,shop_id)

    def toggle_zoom():
        nonlocal is_maximized
        if not is_maximized:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=workspace.winfo_width()-40,
                      height=workspace.winfo_height()-40)
            is_maximized = True
        else:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=520, height=580)
            is_maximized = False

    tk.Button(title_bar, text="✖", width=3, bd=0,
              bg="black", fg="red",
              command=close_window).pack(side="right")

    tk.Button(title_bar, text="⛶", width=3, bd=0,
              bg="black",
              command=toggle_zoom).pack(side="right")

    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Staff")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Staff")
            clear_form(reset_id=True)
        else:
            header_lbl.config(text="Update Staff")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Staff")

    add_btn = tk.Button(
        top_bar, text="Add staff",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Staff",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    search_var = tk.StringVar()
    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))   # ✅ VERY IMPORTANT

    tk.Label(
        search_row,
        text="Search (Phone / Name):",
        bg="white", fg="black",               # ✅ FIXED
        font=("Segoe UI", 9),
        width=20,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")

   
    # ---------------- HEADER ----------------
    header_lbl = tk.Label(
        win,
        text="Add Staff",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))

    # ---------------- FORM CARD ----------------
    card = tk.Frame(win, bg="white")
    card.pack(fill="both", expand=True, padx=22, pady=10)   # ✅ extra padding


    def field(label):
        var = tk.StringVar()

        row = tk.Frame(card, bg="white")
        row.pack(fill="x", pady=6)

        tk.Label(
            row,
            text=label,
            bg="white",
            fg="black",        # ✅ force black
            width=18,
            anchor="w",
            font=("Segoe UI", 9)
        ).pack(side="left")

        ent = tk.Entry(
            row,
            textvariable=var,
            width=30,
            bg="white",
            fg="black",
            insertbackground="black",
            relief="solid",
            bd=1
        )
        ent.pack(side="left", padx=6)

        return var


    staff_name = field("Staff Name")
    password   = field("Password")
    phone1     = field("Phone 1")
    phone2     = field("Phone 2")
    email      = field("Email ID")
    


    # ---------------- ADDRESS ----------------
    addr_row = tk.Frame(card, bg="white")
    addr_row.pack(fill="x", pady=(10, 4))

    tk.Label(
        addr_row,
        text="Address",
        bg="white",
        fg="black",
        width=18,
        anchor="nw",
        font=("Segoe UI", 9)
    ).pack(side="left")

    address_txt = tk.Text(
        addr_row,
        height=4,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    address_txt.pack(side="left", padx=6)


    # ---------------- HELPERS ----------------
    def clear_form(reset_id=True):
        if reset_id:
            current_staff_id.set(0)

        staff_name.set("")
        password.set("")
        phone1.set("")
        phone2.set("")
        email.set("")
        address_txt.delete("1.0", "end")


    def search_staff(*_):
        text = search_var.get().strip()
        if not text:
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM staff
            WHERE shop_id=%s
            AND (staff_name LIKE %s OR phone1 LIKE %s)
            LIMIT 1
        """, (shop_id, f"%{text}%", f"%{text}%"))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showinfo("Not Found", "Staff not found")
            return

        current_staff_id.set(row["staff_id"])
        staff_name.set(row["staff_name"])
        password.set(row["password"])
        phone1.set(row["phone1"])
        phone2.set(row["phone2"] or "")
        email.set(row["email"] or "")

        address_txt.delete("1.0", "end")
        address_txt.insert("1.0", row["address"] or "")

        mode.set("UPDATE")
        update_mode_ui()


    search_entry.bind("<KeyRelease>", search_staff)

    # ---------------- SAVE ----------------
    def save_staff():
        if not staff_name.get() or not phone1.get():
            messagebox.showwarning("Missing", "Staff Name & Phone required")
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            # -------- UPDATE STAFF --------
            if mode.get() == "UPDATE" and current_staff_id.get() != 0:
                cur.execute("""
                    UPDATE staff SET
                        staff_name=%s,
                        password=%s,
                        phone1=%s,
                        phone2=%s,
                        email=%s,
                        address=%s
                    WHERE staff_id=%s AND shop_id=%s
                """, (
                    staff_name.get(),
                    password.get(),
                    phone1.get(),
                    phone2.get() or None,
                    email.get() or None,
                    address_txt.get("1.0", "end").strip() or None,
                    current_staff_id.get(),
                    shop_id
                ))

                messagebox.showinfo("Success", "✅ Staff updated successfully")

            # -------- INSERT STAFF --------
            else:
                cur.execute("""
                    INSERT INTO staff
                    (shop_id, staff_name, password, phone1, phone2,
                    email, address, join_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    shop_id,
                    staff_name.get(),
                    password.get(),
                    phone1.get(),
                    phone2.get() or None,
                    email.get() or None,
                    address_txt.get("1.0", "end").strip() or None,
                    date.today()
                ))

                messagebox.showinfo("Success", "✅ Staff added successfully")

            conn.commit()

            clear_form()
            mode.set("ADD")
            update_mode_ui()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()


    # ---------------- SAVE BUTTON ----------------
    save_btn = tk.Button(
        win,
        text="💾 Save Staff",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18, pady=6,
        command=save_staff
    )
    save_btn.pack(pady=10)

    update_mode_ui()


def open_admin(workspace, shop_id):
    import tkinter as tk
    from tkinter import ttk
    import mysql.connector

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ===== CLEAR WORKSPACE =====
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="#F8FAFC")

    # ===== PAGE BORDER =====
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#20C4E5",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ===== TITLE =====
    tk.Label(
        main,
        text="Admin Details",
        font=("Arial", 12, "bold"),
        fg="#20C4E5",
        bg="white"
    ).pack(pady=(15, 8))

    # ===== SEARCH BAR + ADD BUTTON =====
    top_bar = tk.Frame(main, bg="white")
    top_bar.pack(fill="x", padx=20, pady=(0, 10))

    tk.Label(
        top_bar,
        text="Search :",
        bg="white",
        fg="black",
        font=("Arial", 10, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        top_bar,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black"
    )
    search_entry.pack(side="left", padx=10)

    tk.Button(
        top_bar,
        text="Add Admin",
        bg="#20C4E5",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12,
        relief="flat",
        command=lambda: open_add_admin_window(workspace, shop_id)
    ).pack(side="left")


    # ===== TABLE =====
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    columns = (
        "Admin ID",
        "Admin Name",
        "Username",
        "Password",
        "Phone",
        "Email ID",
        "Address"
    )


    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    widths = [60, 150, 100, 120, 120, 180, 200, 120]

    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    tree.tag_configure("odd", background="#F8FAFC")
    tree.tag_configure("even", background="#80C4E7")
    tree.tag_configure("search_hit", background="#53EA88")


    # ===== LOAD SUPPLIERS FROM MYSQL =====
    def load_admin(search=""):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        if search:
            cur.execute("""
                SELECT
                    admin_id,
                    admin_name,
                    username,
                    password,
                    phone,
                    email,
                    address
                FROM admin
                WHERE admin_name LIKE %s
                OR username LIKE %s
                OR phone LIKE %s
                ORDER BY admin_id DESC
            """, (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            cur.execute("""
                SELECT
                    admin_id,
                    admin_name,
                    username,
                    password,
                    phone,
                    email,
                    address
                FROM admin
                ORDER BY admin_id DESC
            """)

        rows = cur.fetchall()
        conn.close()

        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))


    def on_search_key(event):
        # 🚫 ENTER press panninaa reload panna koodadhu
        if event.keysym == "Return":
            return

        load_admin(search_var.get().strip())
    search_entry.bind("<KeyRelease>", on_search_key)

    load_admin()

    def on_search_enter(event):
        items = tree.get_children()
        if not items:
            return

        # zebra reset
        for i, item in enumerate(items):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        first = items[0]

        tree.selection_set(first)
        tree.focus(first)
        tree.item(first, tags=("search_hit",))


    search_entry.bind("<Return>", on_search_enter)

    def restore_zebra(event):
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


    edit_entry = None

    def on_double_click(event):
        nonlocal edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if not row_id or col == "#1":  # ❌ ID editable illa
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black")
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.insert(0, value)
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get()
            tree.set(row_id, col, new_val)
            edit_entry.destroy()
            update_db(row_id, col, new_val)

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())

    tree.bind("<Double-1>", on_double_click)


    def update_db(row_id, col, value):
        # Treeview column → DB column mapping (ADMIN)
        col_map = {
            "#2": "admin_name",
            "#3": "username",
            "#4": "password",
            "#5": "phone",
            "#6": "email",
            "#7": "address"
        }

        # ID column editable illa
        if not row_id or col == "#1":
            return

        db_col = col_map.get(col)
        if not db_col:
            return

        admin_id = tree.set(row_id, "#1")

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE admin
            SET {db_col}=%s
            WHERE admin_id=%s
            """,
            (value, admin_id)
        )

        conn.commit()
        conn.close()



def open_add_admin_window(workspace, shop_id):
    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date

    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------
    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )
    win.place(relx=0.5, rely=0.5, anchor="center", width=520, height=580)


    is_maximized = False
    mode = tk.StringVar(value="ADD")
    current_admin_id = tk.IntVar(value=0)  

    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_admin(workspace,shop_id)

    def toggle_zoom():
        nonlocal is_maximized
        if not is_maximized:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=workspace.winfo_width()-40,
                      height=workspace.winfo_height()-40)
            is_maximized = True
        else:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=520, height=580)
            is_maximized = False

    tk.Button(title_bar, text="✖", width=3, bd=0,
              bg="black", fg="red",
              command=close_window).pack(side="right")

    tk.Button(title_bar, text="⛶", width=3, bd=0,
              bg="black",
              command=toggle_zoom).pack(side="right")

    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Admin")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Admin")
            clear_form(reset_id=True)
        else:
            header_lbl.config(text="Update Admin")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Staff")

    add_btn = tk.Button(
        top_bar, text="Add Admin",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Admin",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    search_var = tk.StringVar()
    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))   # ✅ VERY IMPORTANT

    tk.Label(
        search_row,
        text="Search (Phone / Name):",
        bg="white", fg="black",               # ✅ FIXED
        font=("Segoe UI", 9),
        width=20,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")

   
    # ---------------- HEADER ----------------
    header_lbl = tk.Label(
        win,
        text="Add Staff",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))

    # ---------------- FORM CARD ----------------
    card = tk.Frame(win, bg="white")
    card.pack(fill="both", expand=True, padx=22, pady=10)   # ✅ extra padding


    def field(label):
        var = tk.StringVar()

        row = tk.Frame(card, bg="white")
        row.pack(fill="x", pady=6)

        tk.Label(
            row,
            text=label,
            bg="white",
            fg="black",        # ✅ force black
            width=18,
            anchor="w",
            font=("Segoe UI", 9)
        ).pack(side="left")

        ent = tk.Entry(
            row,
            textvariable=var,
            width=30,
            bg="white",
            fg="black",
            insertbackground="black",
            relief="solid",
            bd=1
        )
        ent.pack(side="left", padx=6)

        return var

    admin_name = field("Admin Name")
    username   = field("Username")
    password   = field("Password")
    phone      = field("Phone")
    email      = field("Email ID")

    


    # ---------------- ADDRESS ----------------
    addr_row = tk.Frame(card, bg="white")
    addr_row.pack(fill="x", pady=(10, 4))

    tk.Label(
        addr_row,
        text="Address",
        bg="white",
        fg="black",
        width=18,
        anchor="nw",
        font=("Segoe UI", 9)
    ).pack(side="left")

    address_txt = tk.Text(
        addr_row,
        height=4,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    address_txt.pack(side="left", padx=6)


    # ---------------- HELPERS ----------------
    def clear_form(reset_id=True):
        if reset_id:
            current_admin_id.set(0)

        admin_name.set("")
        username.set("")
        password.set("")
        phone.set("")
        email.set("")
        address_txt.delete("1.0", "end")


    def search_admin(*_):
        text = search_var.get().strip()
        if not text:
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM admin
            WHERE admin_name LIKE %s
            OR username LIKE %s
            OR phone LIKE %s
            LIMIT 1
        """, (f"%{text}%", f"%{text}%", f"%{text}%"))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showinfo("Not Found", "Admin not found")
            return

        current_admin_id.set(row["admin_id"])
        admin_name.set(row["admin_name"])
        username.set(row["username"])
        password.set(row["password"])
        phone.set(row["phone"] or "")
        email.set(row["email"] or "")

        address_txt.delete("1.0", "end")
        address_txt.insert("1.0", row["address"] or "")

        mode.set("UPDATE")
        update_mode_ui()



    search_entry.bind("<KeyRelease>", search_admin)


   # ---------------- SAVE ADMIN ----------------
    def save_admin():
        if not admin_name.get() or not username.get():
            messagebox.showwarning("Missing", "Admin Name & Username required")
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            # -------- UPDATE ADMIN --------
            if mode.get() == "UPDATE" and current_admin_id.get() != 0:
                cur.execute("""
                    UPDATE admin SET
                        admin_name=%s,
                        username=%s,
                        password=%s,
                        phone=%s,
                        email=%s,
                        address=%s
                    WHERE admin_id=%s
                """, (
                    admin_name.get(),
                    username.get(),
                    password.get(),
                    phone.get() or None,
                    email.get() or None,
                    address_txt.get("1.0", "end").strip() or None,
                    current_admin_id.get()
                ))

                messagebox.showinfo("Success", "✅ Admin updated successfully")

            # -------- INSERT ADMIN --------
            else:
                cur.execute("""
                    INSERT INTO admin
                    (admin_name, username, password, phone, email, address)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    admin_name.get(),
                    username.get(),
                    password.get(),
                    phone.get() or None,
                    email.get() or None,
                    address_txt.get("1.0", "end").strip() or None
                ))

                messagebox.showinfo("Success", "✅ Admin added successfully")

            conn.commit()

            clear_form()
            mode.set("ADD")
            update_mode_ui()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()



    # ---------------- SAVE BUTTON ----------------
    save_btn = tk.Button(
        win,
        text="💾 Save Staff",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18, pady=6,
        command=save_admin
    )
    save_btn.pack(pady=10)

    update_mode_ui()



def open_shop_details(workspace):
    import tkinter as tk

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="#F8FAFC")

    # ---------------- MAIN ----------------
    main = tk.Frame(workspace, bg="white")
    main.pack(fill="both", expand=True, padx=30, pady=25)


    shop_exists = tk.BooleanVar(value=False)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="SHOP DETAILS",
        font=("Segoe UI", 15, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(0, 20))

    # ---------------- COLUMN CONTAINER ----------------
    cols = tk.Frame(main, bg="white")
    cols.pack(fill="both", expand=True)

    # create 3 equal columns
    col1 = tk.Frame(cols, bg="white")
    col2 = tk.Frame(cols, bg="white")
    col3 = tk.Frame(cols, bg="white")

    col1.pack(side="left", fill="both", expand=True, padx=15)
    col2.pack(side="left", fill="both", expand=True, padx=15)
    col3.pack(side="left", fill="both", expand=True, padx=15)

    # ---------------- HELPERS ----------------
    def section(parent, title):
        tk.Label(
            parent,
            text=title.upper(),
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="white"
        ).pack(anchor="w", pady=(0, 6))

        tk.Frame(parent, bg="#E5E7EB", height=1).pack(fill="x", pady=(0, 10))

    def field(parent, label, readonly=False):
        tk.Label(
            parent,
            text=label,
            font=("Segoe UI", 8),
            fg="#000000",
            bg="white"
        ).pack(anchor="w")

        var = tk.StringVar()
        ent = tk.Entry(
            parent,
            textvariable=var,
            font=("Segoe UI", 10),
            relief="flat",
            bg="white",
            fg="black"
        )
        ent.pack(fill="x", pady=(0, 6))

        tk.Frame(parent, bg="#CBD5E1", height=1).pack(fill="x", pady=(0, 10))

        if readonly:
            ent.config(state="readonly")

        return var

    # ---------------- BASIC DETAILS ----------------
    section(col1, "Basic Details")
    shop_id   = field(col1, "Shop ID", readonly=True)
    shop_name = field(col1, "Shop Name")
    shop_code = field(col1, "Shop Code")
    gst       = field(col1, "GST Number")

    # ---------------- CONTACT DETAILS ----------------
    section(col2, "Contact Details")
    phone1  = field(col2, "Phone 1")
    phone2  = field(col2, "Phone 2")
    phone3  = field(col2, "Phone 3")
    email1  = field(col2, "Email 1")
    email2  = field(col2, "Email 2")
    website = field(col2, "Website")
    fax     = field(col2, "Fax")

    # ---------------- ADDRESS DETAILS ----------------
    section(col3, "Address Details")
    addr1    = field(col3, "Address Line 1")
    addr2    = field(col3, "Address Line 2")
    district = field(col3, "District")
    pincode  = field(col3, "Pincode")

    #btn_bar = tk.Frame(main, bg="white")
    # btn_bar.pack(fill="x", pady=25)

    btn_bar = tk.Frame(col2, bg="white")
    btn_bar.pack(fill="x", pady=(10, 0))

    tk.Button(
        btn_bar,
        text="CANCEL",
        bg="#E5E7EB",
        fg="#0F172A",
        font=("Segoe UI", 10, "bold"),
        padx=30,
        pady=8,
        relief="flat",
        command=lambda: open_shop_details(workspace)
    ).pack(side="right", padx=8)


    import mysql.connector

    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )


    def save_shop_details():
        conn = get_db()
        cur = conn.cursor()

        try:
            if shop_exists.get():
                cur.execute("""
                    UPDATE shop_details SET
                        shop_name=%s, shop_code=%s, gst_number=%s,
                        phone1=%s, phone2=%s, phone3=%s,
                        email1=%s, email2=%s,
                        website=%s, fax=%s,
                        address_line1=%s, address_line2=%s,
                        district=%s, pincode=%s
                    WHERE shop_id=%s
                """, (
                    shop_name.get(), shop_code.get(), gst.get(),
                    phone1.get(), phone2.get(), phone3.get(),
                    email1.get(), email2.get(),
                    website.get(), fax.get(),
                    addr1.get(), addr2.get(),
                    district.get(), pincode.get(),
                    shop_id.get()
                ))
            else:
                cur.execute("""
                    INSERT INTO shop_details
                    (shop_name, shop_code, gst_number,
                     phone1, phone2, phone3,
                     email1, email2, website, fax,
                     address_line1, address_line2,
                     district, pincode)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    shop_name.get(), shop_code.get(), gst.get(),
                    phone1.get(), phone2.get(), phone3.get(),
                    email1.get(), email2.get(),
                    website.get(), fax.get(),
                    addr1.get(), addr2.get(),
                    district.get(), pincode.get()
                ))

                shop_id.set(cur.lastrowid)
                shop_exists.set(True)

            conn.commit()
            update_button_mode()
            messagebox.showinfo("Success", "✅ Shop details saved")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    save_btn = tk.Button(
        btn_bar,
        text="SAVE",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=30,
        pady=8,
        relief="flat",
        command=save_shop_details   # 🔥 THIS WAS MISSING
    )
    save_btn.pack(side="right", padx=8)






    # ---------------- ADDRESS DETAILS ----------------
    # section(col3, "Address Details")
    # addr1    = field(col3, "Address Line 1")
    # addr2    = field(col3, "Address Line 2")
    # district = field(col3, "District")
    # pincode  = field(col3, "Pincode")

    # ---------------- MODE SWITCH ----------------
    def update_button_mode():
        save_btn.config(text="UPDATE" if shop_exists.get() else "SAVE")

    # ---------- LOAD ----------
    def load_shop_details():
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM shop_details LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if row:
            shop_exists.set(True)
            shop_id.set(row["shop_id"])
            shop_name.set(row["shop_name"])
            shop_code.set(row["shop_code"])
            gst.set(row["gst_number"])
            phone1.set(row["phone1"])
            phone2.set(row["phone2"])
            phone3.set(row["phone3"])
            email1.set(row["email1"])
            email2.set(row["email2"])
            website.set(row["website"])
            fax.set(row["fax"])
            addr1.set(row["address_line1"])
            addr2.set(row["address_line2"])
            district.set(row["district"])
            pincode.set(row["pincode"])

        update_button_mode()

    load_shop_details()
# -------------------------------------------------------------------------------------------------------------------------------------
def fetch_selected_customer_details(checked_rows):
    if not checked_rows:
        return []

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(checked_rows))

    query = f"""
        SELECT
            customer_name,
            phone_1,
            address,
            current_points
        FROM customers
        WHERE customer_id IN ({placeholders})
    """

    cur.execute(query, tuple(checked_rows))
    rows = cur.fetchall()
    conn.close()

    return rows




sort_high_to_low = False

from datetime import datetime, date
from tkcalendar import DateEntry

# 🔐 GLOBAL SMS STATE (PERSIST ACROSS REFRESH)
SMS_ENABLED_STATE = False
edit_entry = None
editing_info = {}
checked_rows = set()
all_customer_rows = []
edit_entry = None
date_filter_active = False
PREMIUM_VIOLET = "#7C3AED"   # Modern premium violet

# -------------------------------
# Customer List Window (Premium)
# -------------------------------
def open_offer_window(workspace, shop_id):
    global checked_rows
    PREMIUM_VIOLET = "#7C3AED"
    import tkinter as tk
    from tkinter import ttk
    from datetime import datetime
    from tkcalendar import DateEntry
    import socket

    # -------------------------------
    # CLEAR WORKSPACE
    # -------------------------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # -------------------------------
    # CARD
    # -------------------------------
    card = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=PREMIUM_VIOLET,
        highlightthickness=3
    )
    card.pack(fill="both", expand=True, padx=10, pady=10)

   

    tk.Label(
        card,
        text="Offer (Premium View)",
        font=("Segoe UI", 10, "bold"),
        fg=PREMIUM_VIOLET,
        bg="white"
    ).pack(pady=(7, 6))

    # -------------------------------
    # TOP ROW
    # -------------------------------
    top_row = tk.Frame(card, bg="white")
    top_row.pack(fill="x", padx=20, pady=(5, 10))

    # -------------------------------
    # SEARCH
    # -------------------------------
    tk.Label(
        top_row,
        text="Search:",
        bg="white",
        fg="black",
    ).pack(side="left", padx=(0, 6))

    search_var = tk.StringVar()

    search_entry = tk.Entry(
        top_row,
        textvariable=search_var,
        width=26,
        bg="white",          # ✅ white background
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left", padx=(0, 12))


    # -------------------------------
    # LOAD CUSTOMERS (DUMMY)
    # -------------------------------
    def load_customers(start_date=None, end_date=None):
        print("📥 Load customers")
        print("From:", start_date, "To:", end_date)

    # -------------------------------
    # NETWORK CHECK
    # -------------------------------
    def is_network_connected():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    # ===============================
    # ACTION ROW (FIXED ALIGNMENT)
    # ===============================
    action_row = tk.Frame(top_row, bg="white")
    action_row.pack(side="left", padx=6)


    def fixed_box(parent, w=90, h=30):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box


    # -------------------------------
    # ADD CUSTOMER
    # -------------------------------
    box_add = fixed_box(action_row, 120, 30)
    



    tk.Button(
        box_add,
        text="Send Message",
        bg="#c727ef",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        command=lambda: open_send_offer_page(
            workspace,
            shop_id,
            fetch_selected_customer_details(checked_rows)
        )


    ).pack(fill="both", expand=True)


    # -------------------------------
    # HIGH ↔ LOW TOGGLE BUTTON
    # -------------------------------
    sort_high_to_low = False

    box_sort = fixed_box(action_row, 90, 30)

    def toggle_sort_by_points():
        global sort_high_to_low
        sort_high_to_low = not sort_high_to_low

        if sort_high_to_low:
            btn_sort.config(text="Clear", bg="#dc2626")
            load_customers(order_by_points=True)
        else:
            btn_sort.config(text="High → Low", bg="#5ba728")
            load_customers(order_by_points=False)

    btn_sort = tk.Button(
        box_sort,
        text="High → Low",
        bg="#4ca728",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        command=toggle_sort_by_points
    )
    btn_sort.pack(fill="both", expand=True)


    # -------------------------------
    # FROM DATE
    # -------------------------------
    from datetime import datetime

    # -------------------------------
    # FROM DATE
    # -------------------------------
    box_from = fixed_box(action_row, 130, 30)

    tk.Label(box_from, text="From", bg="black", fg="white").pack(side="left", padx=3)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")


    # -------------------------------
    # TO DATE
    # -------------------------------
    box_to = fixed_box(action_row, 130, 30)

    tk.Label(box_to, text="To", bg="black", fg="white").pack(side="left", padx=3)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")



    # -------------------------------
    # APPLY / CLEAR BUTTON (FIXED SIZE)
    # -------------------------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False  # toggle state

    def toggle_date_filter():
        global date_filter_active

        if not date_filter_active:
            # ✅ APPLY FILTER
            load_customers(
                start_date.get_date(),
                end_date.get_date()
            )

            btn_apply.config(
                text="Clear",
                bg="#dc2626"   # red
            )

            date_filter_active = True

        else:
            # ✅ CLEAR FILTER
            load_customers()   # normal full list

            btn_apply.config(
                text="🔍 Apply",
                bg="#261987"
            )

            date_filter_active = False


    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        command=toggle_date_filter
    )

    btn_apply.pack(fill="both", expand=True)



    

       # -------------------------------
    # STATUS FRAME (RIGHT SIDE)
    # -------------------------------
    status_frame = tk.Frame(top_row, bg="white")
    status_frame.pack(side="left", padx=(25, 5))

    import socket

    # -------------------------------
    # NETWORK CHECK
    # -------------------------------
    def is_network_connected():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    # -------------------------------
    # NETWORK STATUS SQUARE
    # -------------------------------
    net_canvas = tk.Canvas(
        status_frame,
        width=28,
        height=28,
        bg="white",
        highlightthickness=0
    )
    net_canvas.pack(side="left", padx=(0, 10))

    square = net_canvas.create_rectangle(2, 2, 26, 26, outline="")
    icon = net_canvas.create_text(14, 14, font=("Segoe UI", 12, "bold"))

    def update_network_status():
        if is_network_connected():
            net_canvas.itemconfig(square, fill="#28a745")
            net_canvas.itemconfig(icon, text="✔", fill="white")
        else:
            net_canvas.itemconfig(square, fill="#dc3545")
            net_canvas.itemconfig(icon, text="✖", fill="white")

        # 🔁 refresh every 3 sec
        net_canvas.after(3000, update_network_status)

    update_network_status()

    # -------------------------------
    # 🔘 MODERN TOGGLE (FIXED & PERMANENT)
    # -------------------------------
    sms_enabled = load_sms_state()   # 🔐 load once

    # -------------------------------
    # 🔘 MODERN TOGGLE (BORDER FIXED)
    # -------------------------------
    sms_enabled = load_sms_state()   # 🔐 persistent state

    toggle_canvas = tk.Canvas(
        status_frame,
        width=90,          # ✅ FIXED WIDTH
        height=30,
        bg="white",
        highlightthickness=0
    )
    toggle_canvas.pack(side="left", padx=(8, 0))

    # background (pill with full border)
    bg = toggle_canvas.create_rectangle(
        2, 2, 88, 28,      # ✅ inside canvas
        outline="black",
        width=1,
        fill="#e5e7eb"
    )

    # knob
    knob = toggle_canvas.create_oval(
        4, 4, 28, 26,
        fill="white",
        outline="#9ca3af"
    )

    # ON / OFF text
    label = toggle_canvas.create_text(
        45, 15,
        font=("Segoe UI", 9, "bold"),
        text=""
    )

    def draw_toggle():
        if sms_enabled:
            toggle_canvas.itemconfig(bg, fill="#2563eb")  # blue
            toggle_canvas.coords(knob, 60, 4, 84, 26)     # 👉 right
            toggle_canvas.itemconfig(label, text="ON", fill="white")
        else:
            toggle_canvas.itemconfig(bg, fill="#e5e7eb")  # grey
            toggle_canvas.coords(knob, 4, 4, 28, 26)      # 👉 left
            toggle_canvas.itemconfig(label, text="OFF", fill="#111827")

    def toggle_sms(event=None):
        nonlocal sms_enabled
        sms_enabled = not sms_enabled
        save_sms_state(sms_enabled)

        if sms_enabled:
            enable_sms_sending()
        else:
            disable_sms_sending()

        draw_toggle()

    toggle_canvas.bind("<Button-1>", toggle_sms)

    draw_toggle()





    # -------------------------------
    # SMS METHODS (YOUR REAL LOGIC HERE)
    # -------------------------------
    def enable_sms_sending():
        print("✅ SMS SENDING ENABLED")

    def disable_sms_sending():
        print("❌ SMS SENDING DISABLED")


    style = ttk.Style()
    style.theme_use("default")

    # ===== TREE BODY =====
    style.configure(
        "Treeview",
        background="white",
        foreground="black",
        rowheight=28,
        fieldbackground="white",

        # 🔥 EXCEL GRID LINES
        rowseparatorcolor="black",
        rowseparatorwidth=1,
        columnseparatorcolor="black",
        columnseparatorwidth=1,

        bordercolor="black",
        borderwidth=1,
        relief="solid"
    )

    # ===== HEADER =====
    style.configure(
        "Treeview.Heading",
        background="#e6e6e6",
        foreground="black",
        font=("Segoe UI", 9, "bold"),
        borderwidth=1,
        relief="solid"
    )

    # ===== SELECTION =====
    style.map(
        "Treeview",
        background=[("selected", "#f0ed3d")],
        foreground=[("selected", "white")]
    )

    # ===============================
    # CUSTOMER TABLE WITH CHECKBOX
    # ===============================

    checked_rows = set()
    all_checked = False   # for All ✓ toggle

    # ===============================
    # TABLE FRAME (OUTER)
    # ===============================
    table_frame = tk.Frame(card, bg="black", bd=1)
    table_frame.pack(fill="both", expand=True, padx=10, pady=6)

    # ===============================
    # INNER CONTAINER (TREE + SCROLL)
    # ===============================
    table_container = tk.Frame(table_frame, bg="white")
    table_container.pack(fill="both", expand=True)

    # ===============================
    # TREEVIEW
    # ===============================
    tree_customers = ttk.Treeview(
        table_container,
        columns=(
            "check",
            "customer_id",
            "name",
            "phone",
            "address",
            "last_purchase",
            "lifetime_total",
            "current_points"
        ),
        show="headings",
        height=16
    )

    # ===============================
    # SCROLLBAR
    # ===============================
    scroll_y = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=tree_customers.yview
    )

    tree_customers.configure(yscrollcommand=scroll_y.set)

    # ===============================
    # PACK ORDER (IMPORTANT)
    # ===============================
    tree_customers.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    # ===============================
    # HEADINGS
    # ===============================
    tree_customers.heading("check", text="☐ All")
    tree_customers.heading("customer_id", text="Cust ID")
    tree_customers.heading("name", text="Name")
    tree_customers.heading("phone", text="Phone")
    tree_customers.heading("address", text="Address")
    tree_customers.heading("last_purchase", text="Last Purchase")
    tree_customers.heading("lifetime_total", text="Lifetime Total ₹")
    tree_customers.heading("current_points", text="Points")

    # ===============================
    # COLUMNS
    # ===============================
    tree_customers.column("check", width=80, anchor="center", stretch=False)
    tree_customers.column("customer_id", width=90, anchor="center", stretch=False)
    tree_customers.column("name", width=160, anchor="w")
    tree_customers.column("phone", width=130, anchor="center")
    tree_customers.column("address", width=200, anchor="w")
    tree_customers.column("last_purchase", width=140, anchor="center")
    tree_customers.column("lifetime_total", width=120, anchor="e")
    tree_customers.column("current_points", width=90, anchor="center")

    # ===============================
    # TAGS
    # ===============================
    tree_customers.tag_configure(
        "group",
        background="#f060e4",
        font=("Segoe UI", 10, "bold")
    )

    tree_customers.tag_configure(
        "row",
        background="white"
    )

        
    from datetime import datetime, time

    from datetime import datetime, date, timedelta

    from datetime import date, timedelta

    def load_customers(start_dt=None, end_dt=None, order_by_points=False):
        tree_customers.delete(*tree_customers.get_children())

        conn = get_connection()
        cur = conn.cursor()

        search_text = search_entry.get().strip()

        base_query = """
            SELECT
                c.customer_id,
                c.customer_name,
                c.phone_1,
                c.address,

                -- ✅ LAST PURCHASE AMOUNT
                COALESCE(
                    (
                        SELECT s2.total_amount
                        FROM sales s2
                        WHERE s2.customer_id = c.customer_id
                        AND s2.shop_id = c.shop_id
                        ORDER BY s2.date_time DESC
                        LIMIT 1
                    ), 0
                ) AS last_purchase_amount,

                -- ✅ LIFETIME TOTAL
                c.lifetime_total,

                -- ✅ CURRENT POINTS
                c.current_points,

                -- ✅ LAST BILL DATE (for sorting)
                MAX(s.date_time) AS last_bill_date

            FROM customers c
            LEFT JOIN sales s
                ON s.customer_id = c.customer_id
                AND s.shop_id = c.shop_id
            WHERE c.shop_id = %s
            AND c.status = 'ACTIVE'
        """


        params = [shop_id]

        # 🔍 SEARCH FILTER
        if search_text:
            base_query += """
                AND (
                    c.customer_name LIKE %s
                    OR c.phone_1 LIKE %s
                )
            """
            like = f"%{search_text}%"
            params.extend([like, like])

        # 📅 DATE FILTER
        filter_active = False
        if start_dt and end_dt:
            filter_active = True
            base_query += " AND DATE(s.date_time) BETWEEN %s AND %s"
            params.extend([start_dt, end_dt])

        base_query += """
            GROUP BY
                c.customer_id,
                c.customer_name,
                c.phone_1,
                c.address,
                
                c.lifetime_total,
                c.current_points
        """

        # 🔥 SORT
        if order_by_points:
            base_query += " ORDER BY c.current_points DESC"
        else:
            base_query += " ORDER BY last_bill_date DESC"

        cur.execute(base_query, params)
        rows = cur.fetchall()
        conn.close()

        today = date.today()
        yesterday = today - timedelta(days=1)

        # =====================================================
        # 🔥 HIGH → LOW MODE (NO DATE GROUPING)
        # =====================================================
        if order_by_points:
            for r in rows:
                cid = str(r[0])
                checkbox = "☑" if cid in checked_rows else "☐"

                tree_customers.insert(
                    "", "end",
                    iid=cid,
                    values=(
                        checkbox,
                        r[0],
                        r[1],
                        r[2],
                        r[3] or "-",
                        f"₹ {r[4]:.2f}",
                        f"₹ {r[5]:.2f}",
                        r[6]
                    ),
                    tags=("row",)
                )


            return

        # =====================================================
        # NORMAL DATE GROUP MODE
        # =====================================================
        grouped = {}

        for r in rows:
            last_dt = r[7]

            if last_dt:
                bill_date = last_dt.date()
                if filter_active:
                    label = bill_date.strftime("%d-%m-%Y")
                else:
                    if bill_date == today:
                        label = "TODAY"
                    elif bill_date == yesterday:
                        label = "YESTERDAY"
                    else:
                        label = bill_date.strftime("%d-%m-%Y")
            else:
                label = "NO BILL"

            grouped.setdefault(label, []).append(r)

        for label, customers in grouped.items():
            tree_customers.insert(
                "",
                "end",
                values=(f"☐ {label}", "", "", "", "", "", "", ""),
                tags=("group",)
            )


            for r in customers:
                cid = str(r[0])
                checkbox = "☑" if cid in checked_rows else "☐"

                tree_customers.insert(
                    "", "end",
                    iid=cid,
                    values=(
                        checkbox,
                        r[0],
                        r[1],
                        r[2],
                        r[3] or "-",
                        f"₹ {r[4]:.2f}",
                        f"₹ {r[5]:.2f}",
                        r[6]
                    ),
                    tags=("row",)
                )

    search_entry.bind("<KeyRelease>", lambda e: load_customers())

    def on_heading_click(event):
        nonlocal all_checked   # 🔥 THIS FIXES YOUR ERROR

        region = tree_customers.identify_region(event.x, event.y)
        if region != "heading":
            return

        col = tree_customers.identify_column(event.x)
        if col != "#1":
            return

        all_checked = not all_checked

        tree_customers.heading(
            "check",
            text="☑ All" if all_checked else "☐ All"
        )

        for iid in tree_customers.get_children():
            if "group" in tree_customers.item(iid, "tags"):
                continue

            if all_checked:
                checked_rows.add(iid)
                tree_customers.set(iid, "check", "☑")
            else:
                checked_rows.discard(iid)
                tree_customers.set(iid, "check", "☐")

    tree_customers.bind("<ButtonRelease-1>", on_heading_click)



    def toggle_checkbox(event):
        region = tree_customers.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree_customers.identify_row(event.y)
        col_id = tree_customers.identify_column(event.x)

        if col_id != "#1" or not row_id:
            return

        tags = tree_customers.item(row_id, "tags")

        # ===============================
        # GROUP ROW CLICK
        # ===============================
        if "group" in tags:
            children = []
            start = False

            for iid in tree_customers.get_children():
                if iid == row_id:
                    start = True
                    continue
                if start:
                    if "group" in tree_customers.item(iid, "tags"):
                        break
                    children.append(iid)

            select = any(cid not in checked_rows for cid in children)

            tree_customers.set(
                row_id, "check",
                "☑ " + tree_customers.item(row_id, "values")[0][2:]
                if select else
                "☐ " + tree_customers.item(row_id, "values")[0][2:]
            )

            for cid in children:
                if select:
                    checked_rows.add(cid)
                    tree_customers.set(cid, "check", "☑")
                else:
                    checked_rows.discard(cid)
                    tree_customers.set(cid, "check", "☐")
            return

        # ===============================
        # NORMAL ROW
        # ===============================
        if row_id in checked_rows:
            checked_rows.remove(row_id)
            tree_customers.set(row_id, "check", "☐")
        else:
            checked_rows.add(row_id)
            tree_customers.set(row_id, "check", "☑")

    tree_customers.bind("<Button-1>", toggle_checkbox)



    def on_drag_select(event):
        row_id = tree_customers.identify_row(event.y)
        if not row_id:
            return

        tags = tree_customers.item(row_id, "tags")
        if "group" in tags:
            return

        if row_id not in checked_rows:
            checked_rows.add(row_id)
            tree_customers.set(row_id, "check", "☑")

    tree_customers.bind("<B1-Motion>", on_drag_select)

    def get_selected_customers():
        return list(checked_rows)


    def refresh_table(data):
        tree_customers.delete(*tree_customers.get_children())

        for i, vals in enumerate(data):
            tag = "even" if i % 2 == 0 else "odd"
            tree_customers.insert(
                "",
                "end",
                values=vals,
                tags=(tag,)
            )



    # INITIAL LOAD
    load_customers()
    def get_selected_customers():
        return list(checked_rows)


    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview",
        rowheight=28,
        font=("Segoe UI", 10)
    )

    style.map(
        "Treeview",
        background=[("selected", "#3aaed8")],
        foreground=[("selected", "white")]
    )

    def search_and_refresh(*_):
        q = search_var.get().strip().lower()

        if not q:
            refresh_table(all_customer_rows)
            return

        matched = []
        others = []

        for row in all_customer_rows:
            name  = str(row[1]).lower()
            phone = str(row[2]).lower()

            if q in name or q in phone:
                matched.append(row)
            else:
                others.append(row)

        refresh_table(matched + others)


    search_var.trace_add("write", search_and_refresh)

    def get_selected_customer_details():
        if not checked_rows:
            return []

        conn = get_connection()
        cur = conn.cursor()

        placeholders = ",".join(["%s"] * len(checked_rows))

        query = f"""
            SELECT
                customer_name,
                phone_1,
                address,
                current_points
            FROM customers
            WHERE customer_id IN ({placeholders})
        """

        cur.execute(query, tuple(checked_rows))
        rows = cur.fetchall()
        conn.close()

        return rows




#     def select_first(event=None):
#         items = tree_customers.get_children()
#         if items:
#             tree_customers.selection_set(items[0])
#             tree_customers.focus(items[0])

#     search_entry.bind("<Return>", select_first)

# # row eduted functions

#     EDITABLE_COLS = {
#         1: "customer_name",   # Name
#         2: "phone_1",         # Phone
#         3: "address"          # Address
#     }

#     def start_inline_edit(event):
#         global edit_entry, editing_info

#         region = tree_customers.identify("region", event.x, event.y)
#         if region != "cell":
#             return

#         row_id = tree_customers.identify_row(event.y)
#         col_id = tree_customers.identify_column(event.x)

#         col_index = int(col_id.replace("#", "")) - 1

#         # 🔒 only allow Name / Phone / Address
#         if col_index not in (1, 2, 3):
#             return

#         bbox = tree_customers.bbox(row_id, col_id)
#         if not bbox:
#             return

#         x, y, w, h = bbox
#         value = tree_customers.item(row_id, "values")[col_index]

#         edit_entry = tk.Entry(tree_customers)
#         edit_entry.place(x=x, y=y, width=w, height=h)
#         edit_entry.insert(0, value)
#         edit_entry.focus()

#         editing_info = {
#             "row": row_id,
#             "col": col_index
#         }

#         edit_entry.bind("<Return>", save_inline_edit)
#         edit_entry.bind("<Escape>", cancel_inline_edit)
#         edit_entry.bind("<FocusOut>", cancel_inline_edit)

            

#     def save_inline_edit(event=None):
#         global edit_entry, editing_info

#         if not edit_entry:
#             return

#         new_value = edit_entry.get().strip()
#         row_id = editing_info["row"]
#         col = editing_info["col"]

#         values = list(tree_customers.item(row_id, "values"))
#         values[col] = new_value
#         tree_customers.item(row_id, values=values)

#         customer_id = values[0]

#         # 🔥 UPDATE DB
#         conn = get_connection()
#         cur = conn.cursor()

#         if col == 1:
#             cur.execute(
#                 "UPDATE customers SET customer_name=%s WHERE customer_id=%s",
#                 (new_value, customer_id)
#             )
#         elif col == 2:
#             cur.execute(
#                 "UPDATE customers SET phone_1=%s WHERE customer_id=%s",
#                 (new_value, customer_id)
#             )
#         elif col == 3:
#             cur.execute(
#                 "UPDATE customers SET address=%s WHERE customer_id=%s",
#                 (new_value, customer_id)
#             )

#         conn.commit()
#         conn.close()

#         edit_entry.destroy()
#         edit_entry = None



#     def cancel_inline_edit(event=None):
#         global edit_entry
#         if edit_entry:
#             edit_entry.destroy()
#             edit_entry = None
            
#     tree_customers.bind("<Double-1>", start_inline_edit)

    # def on_customer_click(event):
    #     region = tree_customers.identify_region(event.x, event.y)
    #     if region != "cell":
    #         return

    #     row_id = tree_customers.identify_row(event.y)
    #     col_id = tree_customers.identify_column(event.x)

    #     if not row_id:
    #         return

    #     # only "Details" column
    #     if col_id != f"#{len(tree_customers['columns'])}":
    #         return

    #     values = tree_customers.item(row_id, "values")
    #     if not values:
    #         return

    #     try:
    #         customer_id = int(values[0])   # ✅ CORRECT
    #     except:
    #         return

    #     open_customer_detail(workspace, shop_id, customer_id)



    # tree_customers.bind("<ButtonRelease-1>", on_customer_click)
    
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import os
from tkinter import filedialog
from PIL import Image, ImageTk
from PIL import Image, ImageTk


WORK_BG = "#F8FAFC"
CARD = "#FFFFFF"
PRIMARY = "#0EA5E9"
SUCCESS = "#22C55E"
TEXT = "#0F172A"
MUTED = "#64748B"
BORDER = "#CBD5E1"
# 🔥 GLOBAL STATE FOR SEND OFFER PAGE
SEND_OFFER_SELECTED_CUSTOMERS = None
SEND_OFFER_MESSAGE_TEXT = ""
SEND_OFFER_IMAGE_PATH = None
SEND_OFFER_FILE_PATH = None



def open_send_offer_page(workspace, shop_id, selected_customers):

    global SEND_OFFER_SELECTED_CUSTOMERS

    # 🔥 store only first time
    if SEND_OFFER_SELECTED_CUSTOMERS is None:
        SEND_OFFER_SELECTED_CUSTOMERS = selected_customers

    selected_customers = SEND_OFFER_SELECTED_CUSTOMERS

    # CLEAR WORKSPACE
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ================= HEADER =================
    header = tk.Frame(workspace, bg="#1E293B", height=45)
    header.pack(fill="x")

    tk.Label(
        header, text="📤 Send Offer",
        bg="#1E293B", fg="white",
        font=("Segoe UI", 13, "bold")
    ).pack(side="left", padx=15)

   
    def close_send_offer():
        global SEND_OFFER_SELECTED_CUSTOMERS
        global SEND_OFFER_MESSAGE_TEXT
        global SEND_OFFER_IMAGE_PATH
        global SEND_OFFER_FILE_PATH

        SEND_OFFER_SELECTED_CUSTOMERS = None
        SEND_OFFER_MESSAGE_TEXT = ""
        SEND_OFFER_IMAGE_PATH = None
        SEND_OFFER_FILE_PATH = None

        for w in workspace.winfo_children():
            w.destroy()

        open_offer_window(workspace, shop_id)

    tk.Button(
        header, text="✖",
        command=close_send_offer
    ).pack(side="right")

    def go_back_to_offer():
        global SEND_OFFER_MESSAGE_TEXT
        global SEND_OFFER_IMAGE_PATH
        global SEND_OFFER_FILE_PATH

        SEND_OFFER_MESSAGE_TEXT = msg_text.get("1.0", "end").strip()

        for w in workspace.winfo_children():
            w.destroy()

        open_offer_window(workspace, shop_id)


        
    tk.Button(header, text="⬅", command=go_back_to_offer).pack(side="right")
    


        
    # ================= MAIN =================
    main = tk.Frame(workspace, bg=WORK_BG)
    main.pack(fill="both", expand=True, padx=15, pady=15)

    main.grid_rowconfigure(0, weight=1)
    main.grid_columnconfigure(0, weight=9)   # 45%
    main.grid_columnconfigure(1, weight=11)  # 55%

    # ================= LEFT =================
    left = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    left.grid_propagate(False)

    tk.Label(left, text="📸 Offer Content", bg=CARD, fg=TEXT,
             font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=8)

    # IMAGE PREVIEW
    # IMAGE PREVIEW OUTER BOX (GREY BORDER FULL)
    img_box = tk.Frame(
        left,
        bg="#E5E7EB",
        height=170,
        highlightbackground="#9CA3AF",   # 🔥 GREY BORDER
        highlightthickness=2
    )
    img_box.pack(fill="x", padx=15, pady=5)
    img_box.pack_propagate(False)

    # IMAGE LABEL (FIXED SIZE – CENTERED)
    img_label = tk.Label(
        img_box,
        text="Upload Offer Image",
        bg="#E5E7EB",
        fg=MUTED,
        width=340,
        height=160,
        anchor="center",
        compound="center"
    )
    img_label.place(relx=0.5, rely=0.5, anchor="center")

    img_ref = {"img": None}

    # FILE PATH DISPLAY (FULL PATH)
    path_label = tk.Label(
        left,
        text="No file selected",
        bg=CARD,
        fg="#475569",
        font=("Segoe UI", 9),
        wraplength=360,
        justify="left"
    )
    path_label.pack(anchor="w", padx=15, pady=(2, 2))

    # FILE NAME (BIG & CLEAR)
    file_label = tk.Label(
        left,
        text="",
        bg=CARD,
        fg="#0F172A",
        font=("Segoe UI", 10, "bold")
    )
    file_label.pack(anchor="w", padx=15, pady=(0, 6))

    from tkinter import ttk
   

    def open_file_picker():
        picker = tk.Toplevel(workspace)
        picker.title("Select File")
        picker.configure(bg="#F8FAFC")
        picker.geometry("820x520")

        picker.focus_force()
        picker.lift()

        # 🔥 CENTER WINDOW (already added earlier)
        picker.update_idletasks()

        parent_x = workspace.winfo_rootx()
        parent_y = workspace.winfo_rooty()
        parent_w = workspace.winfo_width()
        parent_h = workspace.winfo_height()

        win_w = 820
        win_h = 520

        x = parent_x + (parent_w // 2) - (win_w // 2)
        y = parent_y + (parent_h // 2) - (win_h // 2)

        picker.geometry(f"{win_w}x{win_h}+{x}+{y}")

        current_dir = tk.StringVar(value=os.path.expanduser("~"))
        active_btn = {"btn": None}

        # ================= LEFT SIDEBAR =================
        sidebar = tk.Frame(picker, width=160, bg="#1E293B")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        def highlight(btn):
            if active_btn["btn"]:
                active_btn["btn"].config(bg="#1E293B")
            btn.config(bg="#2AEBCE")
            active_btn["btn"] = btn

        def go(path, btn):
            highlight(btn)
            current_dir.set(path)
            load_files()

        locations = {
            "🏠 Home": os.path.expanduser("~"),
            "🖥 Desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "⬇ Downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "📄 Documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "🖼 Pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            "🎬 Videos": os.path.join(os.path.expanduser("~"), "Videos"),
        }

        for name, path in locations.items():
            b = tk.Button(
                sidebar, text=name,
                anchor="w",
                bg="#1E293B", fg="white",
                bd=0, padx=12, pady=8,
                font=("Segoe UI", 10)
            )
            b.pack(fill="x")
            b.config(command=lambda p=path, btn=b: go(p, btn))

        # ================= RIGHT PANEL =================
        right = tk.Frame(picker, bg="white")
        right.pack(fill="both", expand=True)

        # TOP BAR
        top = tk.Frame(right, bg="white")
        top.pack(fill="x", padx=10, pady=6)

        tk.Label(top, textvariable=current_dir,
                bg="white", fg="#4878BB",
                font=("Segoe UI", 9)).pack(side="left")

        def go_up():
            parent = os.path.dirname(current_dir.get())
            if parent:
                current_dir.set(parent)
                load_files()

        tk.Button(
            top, text="⬆ Up",
            command=go_up,
            bg="#3278CE", bd=0,
            font=("Segoe UI", 9)
        ).pack(side="right")

        # FILE LIST
        file_list = tk.Listbox(
            right,
            font=("Segoe UI", 10),
            bg="white",
            fg="black",
            activestyle="none",
            selectbackground="#F9C134"
        )
        file_list.pack(fill="both", expand=True, padx=10, pady=5)

        # BOTTOM BAR
        bottom = tk.Frame(right, bg="white")
        bottom.pack(fill="x", padx=10, pady=6)

        def select_file():
            sel = file_list.curselection()
            if not sel:
                return

            raw = file_list.get(sel[0])
            name = raw.split(" ", 1)[1]   # 🔥 removes icon
            full = os.path.join(current_dir.get(), name)

            if os.path.isdir(full):
                current_dir.set(full)
                load_files()
                return

            picker.destroy()
            handle_selected_file(full)


        tk.Button(
            bottom, text="Open",
            bg="#0EA5E9", fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0, padx=20, pady=6,
            command=select_file
        ).pack(side="right")

        tk.Button(
            bottom, text="Cancel",
            command=picker.destroy,
            bg="#EF4444", fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0, padx=20, pady=6
        ).pack(side="right", padx=6)

        # ================= FILE LOADER =================
        def load_files():
            file_list.delete(0, "end")
            path = current_dir.get()

            try:
                folders, files, images = [], [], []

                for f in os.listdir(path):
                    full = os.path.join(path, f)
                    ext = os.path.splitext(f)[1].lower()

                    if os.path.isdir(full):
                        folders.append(f)
                    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
                        images.append(f)
                    else:
                        files.append(f)

                # 🔥 ORDER: Folder → Files → Images
                for f in sorted(folders):
                    file_list.insert("end", f"📁 {f}")

                for f in sorted(files):
                    file_list.insert("end", f"📄 {f}")

                for f in sorted(images):
                    file_list.insert("end", f"🖼 {f}")

            except Exception as e:
                print("Load error:", e)


        load_files()



    def handle_selected_file(path):

        global SEND_OFFER_IMAGE_PATH, SEND_OFFER_FILE_PATH

        ext = os.path.splitext(path)[1].lower()

        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            SEND_OFFER_IMAGE_PATH = path
            SEND_OFFER_FILE_PATH = None
        else:
            SEND_OFFER_FILE_PATH = path

        ext = os.path.splitext(path)[1].lower()
        filename = os.path.basename(path)

        path_label.config(text=f"📁 {path}")

        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            img = Image.open(path)

            # 🔥 FIT IMAGE TO GREY BOX (KEEP BORDER VISIBLE)
            box_w = img_box.winfo_width()
            box_h = img_box.winfo_height()

            if box_w <= 1 or box_h <= 1:
                box_w, box_h = 340, 160   # fallback

            img = img.resize((box_w - 10, box_h - 10), Image.LANCZOS)

            img_ref["img"] = ImageTk.PhotoImage(img)

            img_label.config(
                image=img_ref["img"],
                text=""
            )

            file_label.config(text=f"🖼 {filename}")

        else:
            img_label.config(
                image="",
                text="📄 File Selected"
            )
            file_label.config(text=f"📄 {filename}")



  
    btn_frame = tk.Frame(left, bg=CARD)
    btn_frame.pack(fill="x", padx=15, pady=8)

    tk.Button(
        btn_frame,
        text="Upload File / Image",
        bg=PRIMARY,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        bd=0,
        padx=14,
        pady=6,
        command=open_file_picker
    ).pack(side="left")

    tk.Button(
        btn_frame,
        text="Clear",
        bg="#EF4444",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        bd=0,
        padx=12,
        pady=6,
        command=lambda: (
            img_label.config(image="", text="Upload Offer Image"),
            file_label.config(text=""),
            path_label.config(text="No file selected"),
            img_ref.update({"img": None})
        )

    ).pack(side="left", padx=8)



    # ================= MESSAGE (ONLY THIS SCROLLS) =================
    tk.Label(left, text="Message", bg=CARD, fg=TEXT,
            font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15)

    msg_frame = tk.Frame(left, bg=CARD, height=220)
    msg_frame.pack(fill="x", padx=15, pady=8)
    msg_frame.pack_propagate(False)

    msg_text = tk.Text(msg_frame, wrap="word", font=("Segoe UI", 10))
    msg_text.pack(side="left", fill="both", expand=True)

    msg_scroll = ttk.Scrollbar(
        msg_frame, orient="vertical", command=msg_text.yview
    )
    msg_scroll.pack(side="right", fill="y")
    msg_text.configure(yscrollcommand=msg_scroll.set)

    # ================= RESTORE MESSAGE =================
    msg_text.delete("1.0", "end")
    if SEND_OFFER_MESSAGE_TEXT:
        msg_text.insert("1.0", SEND_OFFER_MESSAGE_TEXT)
    else:
        msg_text.insert("1.0", "Special offer just for you 🎁")

    # ================= RESTORE IMAGE / FILE =================
    if SEND_OFFER_IMAGE_PATH:
        img = Image.open(SEND_OFFER_IMAGE_PATH)

        box_w = img_box.winfo_width()
        box_h = img_box.winfo_height()
        if box_w <= 1 or box_h <= 1:
            box_w, box_h = 340, 160

        img = img.resize((box_w - 10, box_h - 10), Image.LANCZOS)
        img_ref["img"] = ImageTk.PhotoImage(img)
        img_label.config(image=img_ref["img"], text="")
        file_label.config(text="🖼 " + os.path.basename(SEND_OFFER_IMAGE_PATH))
        path_label.config(text=SEND_OFFER_IMAGE_PATH)

    elif SEND_OFFER_FILE_PATH:
        img_label.config(image="", text="📄 File Selected")
        file_label.config(text="📄 " + os.path.basename(SEND_OFFER_FILE_PATH))
        path_label.config(text=SEND_OFFER_FILE_PATH)


    # ================= RESTORE MESSAGE STATE (ONLY HERE) =================
    msg_text.delete("1.0", "end")

    if SEND_OFFER_MESSAGE_TEXT:
        msg_text.insert("1.0", SEND_OFFER_MESSAGE_TEXT)
    else:
        msg_text.insert("1.0", "Special offer just for you 🎁")



    # ================= RIGHT =================
    right = tk.Frame(main, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    right.grid_propagate(False)

    top_bar = tk.Frame(right, bg=CARD)
    top_bar.pack(fill="x", padx=10, pady=6)

    tk.Label(top_bar, text="👥 Selected Customers", bg=CARD, fg=TEXT,
             font=("Segoe UI", 12, "bold")).pack(side="left")

    tk.Button(top_bar, text="🟢 Send Message",
              bg=SUCCESS, fg="white",
              font=("Segoe UI", 10, "bold"),
              bd=0, padx=14, pady=5).pack(side="right")

    table_frame = tk.Frame(right, bg=CARD)
    table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    columns = ("name", "phone", "address", "points", "delete")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    for c in columns:
        tree.heading(c, text=c.capitalize())

    tree.column("name", width=150)
    tree.column("phone", width=120)
    tree.column("address", width=180)
    tree.column("points", width=60, anchor="center")
    tree.column("delete", width=45, anchor="center")

    tree.pack(side="left", fill="both", expand=True)

    table_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    table_scroll.pack(side="right", fill="y")
    tree.configure(yscrollcommand=table_scroll.set)

    def load_selected_customers():
        tree.delete(*tree.get_children())

        for row in selected_customers:
            name, phone, address, points = row

            tree.insert(
                "",
                "end",
                values=(
                    name,
                    phone,
                    address or "-",
                    points,
                    "❌"
                )
            )

    load_selected_customers()

    def on_delete_click(event):
        row = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if col == "#5" and row:
            tree.delete(row)

    tree.bind("<Button-1>", on_delete_click)

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



def open_expenses_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    search_active = False
    last_search_keyword = ""

    def set_search_active(val):
        nonlocal search_active
        search_active = val

    def set_last_keyword(val):
        nonlocal last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="EXPENSES",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")
            row_text = " ".join(str(v).lower() for v in values)
            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)


    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # reset base zebra
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        tree.after_idle(apply_search_highlight)



    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)

    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    box_add = fixed_box(action_row, 140, 30)

    btn_add_expense = tk.Button(
        box_add,
        text="➕ Add Expense",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=lambda: open_add_expense_window(workspace,shop_id,expense_id=None)
    )

    btn_add_expense.pack(fill="both", expand=True)


    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)
    tk.Label(box_from, text="From", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")

    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)
    tk.Label(box_to, text="To", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")

    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

    # =================================================
    # TABLE
    # =================================================
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = ("date", "cat", "name", "amt", "mode", "paid", "action")

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    # ---------------- TAGS ----------------
    tree.tag_configure("match", background="#BBF7D0")   # green
    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")



    headers = ["Date", "Category", "Name", "Amount", "Mode", "Paid To", "Action"]
    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    tree.column("date", width=100, anchor="center")
    tree.column("cat", width=120, anchor="center")
    tree.column("name", width=180, anchor="w")
    tree.column("amt", width=100, anchor="e")
    tree.column("mode", width=90, anchor="center")
    tree.column("paid", width=140, anchor="center")
    tree.column("action", width=80, anchor="center")

    sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)

    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

     # =================================================
    # TOTAL SUMMARY BAR (BELOW TABLE)
    # =================================================
    summary_bar = tk.Frame(main, bg="#F1F5F9", height=40)
    summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    summary_bar.pack_propagate(False)

    lbl_total = tk.Label(
        summary_bar,
        text="Total : ₹0",
        bg="#F1F5F9",
        fg="black",
        font=("Segoe UI", 10, "bold")
    )
    lbl_total.pack(side="left", padx=20)

    lbl_cash = tk.Label(
        summary_bar,
        text="Cash : ₹0",
        bg="#F1F5F9",
        fg="#16A34A",
        font=("Segoe UI", 10, "bold")
    )
    lbl_cash.pack(side="left", padx=20)

    lbl_credit = tk.Label(
        summary_bar,
        text="Credit : ₹0",
        bg="#F1F5F9",
        fg="#DC2626",
        font=("Segoe UI", 10, "bold")
    )
    lbl_credit.pack(side="left", padx=20)

    def update_totals():
        total = 0
        cash_total = 0
        credit_total = 0

        for item in tree.get_children():
            values = tree.item(item, "values")

            if len(values) < 6:
                continue

            amt = values[3].replace("₹", "").replace(",", "").strip()
            try:
                amt = float(amt)
            except:
                amt = 0

            mode = (values[4] or "").lower()

            total += amt

            if mode == "cash":
                cash_total += amt
            else:
                credit_total += amt

        lbl_total.config(text=f"Total : ₹{total:,.0f}")
        lbl_cash.config(text=f"Cash : ₹{cash_total:,.0f}")
        lbl_credit.config(text=f"Credit : ₹{credit_total:,.0f}")

    update_totals()


    # =================================================
    # LOAD EXPENSES (SINGLE FUNCTION)
    # =================================================
    def load_expenses(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT expense_date, category, expense_name,
                amount, payment_mode, paid_to,
                expense_id
            FROM expenses
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (expense_name LIKE %s OR category LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        if from_dt and to_dt:
            query += " AND expense_date BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += " ORDER BY expense_date DESC"

        cur.execute(query, tuple(params))

        for r in cur.fetchall():
            tree.insert(
                "",
                "end",
                values=(
                    r[0].strftime("%d-%m-%Y"),  # date
                    r[1],                      # category
                    r[2],                      # name
                    f"₹{r[3]:,.0f}",            # amount
                    r[4],                      # mode
                    r[5],                      # paid_to
                    "❌",                      # delete icon
                    r[6]                       # ✅ expense_id (HIDDEN)
                )
            )

        conn.close()
        if search_active:
            apply_search_highlight()
        else:
            restore_zebra()

        update_totals()


    def delete_expense(expense_id):
        if not messagebox.askyesno("Confirm", "Delete this expense?"):
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE expense_id=%s", (expense_id,))
        conn.commit()
        conn.close()

        load_expenses()

    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # ❌ column = #7
        if col_id == "#7":
            values = tree.item(row_id, "values")

            # safety check
            if len(values) < 8:
                return

            expense_id = values[7]   # 🔥 expense_id (hidden)
            delete_expense(expense_id)

    tree.bind("<Button-1>", on_tree_click)


   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


    tree.tag_configure("even", background="#3B81C7")
    tree.tag_configure("odd", background="#EEF2F7")


    # ---------------- INLINE EDIT ----------------
    edit_entry = None

    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        # ❌ ID / Action column editable illa
        if not row_id or col in ("#1", "#7"):
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.insert(0, value.replace("₹", "").replace(",", ""))
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            tree.set(row_id, col, new_val)
            update_db(row_id, col, new_val)
            update_totals()
            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())

    
    tree.bind("<Double-1>", on_double_click)


    # ---------------- UPDATE DB ----------------
    def update_db(row_id, col, value):
        col_map = {
            "#2": "category",
            "#3": "expense_name",
            "#4": "amount",
            "#5": "payment_mode",
            "#6": "paid_to"
        }

        db_col = col_map.get(col)
        if not db_col:
            return

        expense_id = tree.item(row_id)["values"][7]  # 🔥 expense_id

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE expenses
            SET {db_col}=%s
            WHERE expense_id=%s
            """,
            (value, expense_id)
        )

        conn.commit()
        conn.close()



    # ---------------- APPLY / CLEAR LOGIC ----------------
    date_filter_active = False

    def toggle_date_filter():
        nonlocal date_filter_active

        if not date_filter_active:
            # ✅ DateEntry → DATE object (MySQL compatible)
            from_date = start_date.get_date()
            to_date   = end_date.get_date()

            load_expenses(
                search=search_var.get().strip(),
                from_dt=from_date,
                to_dt=to_date
            )

            btn_apply.config(text="Clear", bg="#dc2626")
            date_filter_active = True

        else:
            load_expenses(search=search_var.get().strip())
            btn_apply.config(text="🔍 Apply", bg="#192987")
            date_filter_active = False

    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)

    # ---------------- SEARCH BIND ----------------
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_expenses(search_var.get().strip())
    )

    load_expenses()

   

    

def open_add_expense_window(workspace, shop_id, expense_id=None):

    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date
    current_expense_id = tk.IntVar(value=0)
    if expense_id:
        current_expense_id.set(expense_id)




    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------
    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )
    win.place(relx=0.5, rely=0.5, anchor="center", width=520, height=580)


    is_maximized = False
    mode = tk.StringVar(value="ADD")
    current_staff_id = tk.IntVar(value=0)  
    if expense_id:
        mode.set("UPDATE")


    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_expenses_page(workspace,shop_id)

    def toggle_zoom():
        nonlocal is_maximized
        if not is_maximized:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=workspace.winfo_width()-40,
                      height=workspace.winfo_height()-40)
            is_maximized = True
        else:
            win.place(relx=0.5, rely=0.5, anchor="center",
                      width=520, height=580)
            is_maximized = False

    tk.Button(title_bar, text="✖", width=3, bd=0,
              bg="black", fg="red",
              command=close_window).pack(side="right")

    tk.Button(title_bar, text="⛶", width=3, bd=0,
              bg="black",
              command=toggle_zoom).pack(side="right")

    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Expenses")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Expenses")
            clear_form(reset_id=True)
        else:
            header_lbl.config(text="Update Expenses")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Expenses")

    add_btn = tk.Button(
        top_bar, text="Add Expenses",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Expenses",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    search_var = tk.StringVar()
    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))   # ✅ VERY IMPORTANT

    tk.Label(
        search_row,
        text="Search:",
        bg="white", fg="black",               # ✅ FIXED
        font=("Segoe UI", 9),
        width=20,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")

   
    # ---------------- HEADER ----------------
    header_lbl = tk.Label(
        win,
        text="Add Expenses",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))

    # ---------------- FORM CARD ----------------
    card = tk.Frame(win, bg="white")
    card.pack(fill="both", expand=True, padx=22, pady=10)   # ✅ extra padding


    def field(label):
        var = tk.StringVar()

        row = tk.Frame(card, bg="white")
        row.pack(fill="x", pady=6)

        tk.Label(
            row,
            text=label,
            bg="white",
            fg="black",        # ✅ force black
            width=18,
            anchor="w",
            font=("Segoe UI", 9)
        ).pack(side="left")

        ent = tk.Entry(
            row,
            textvariable=var,
            width=30,
            bg="white",
            fg="black",
            insertbackground="black",
            relief="solid",
            bd=1
        )
        ent.pack(side="left", padx=6)

        return var


    expense_name  = field("Expense Name")
    amount        = field("Amount")
    paid_to       = field("Paid To")
    bill_no       = field("Bill No")

    # ---------------- PAYMENT MODE (DROPDOWN) ----------------
    row = tk.Frame(card, bg="white")
    row.pack(fill="x", pady=6)

    tk.Label(
        row,
        text="Payment Mode",
        bg="white",
        fg="black",
        width=18,
        anchor="w",
        font=("Segoe UI", 9)
    ).pack(side="left")

    payment_mode = tk.StringVar(value="Cash")

    payment_menu = tk.OptionMenu(
        row,
        payment_mode,
        "Cash",
        "Credit"
    )

    payment_menu.config(
        width=27,
        bg="white",
        fg="black",
        relief="solid",
        bd=1
    )
    payment_menu.pack(side="left", padx=6)


   # ---------------- CATEGORY ----------------
    row = tk.Frame(card, bg="white")
    row.pack(fill="x", pady=6)

    tk.Label(
        row,
        text="Category",
        bg="white",
        fg="black",
        width=18,
        anchor="w"
    ).pack(side="left")

    category = tk.StringVar(value="Rent")

    category_menu = tk.OptionMenu(
        row,
        category,
        "All",
        "Rent",
        "Electricity",
        "Internet",
        "Salary",
        "Transport",
        "Maintenance",
        "Office Supplies",
        "Marketing",
        "Food / Tea",
        "Other"
    )

    category_menu.config(
        width=27,
        bg="white",
        fg="black",
        relief="solid",
        bd=1
    )
    category_menu.pack(side="left", padx=6)

    mode = tk.StringVar(value="ADD")

    # # DATE
    # expense_date = DateEntry(card, width=12, date_pattern="dd-mm-yyyy")
    # expense_date.pack()

    # NOTES
    # notes = tk.Text(card, height=4, width=30)
    # notes.pack()

    # ---------------- HELPERS ----------------
   # ---------------- CLEAR FORM ----------------
    def clear_form(reset_id=True):
        if reset_id:
            current_expense_id.set(0)

        category.set("Rent")
        expense_name.set("")
        amount.set("")
        payment_mode.set("Cash")

        paid_to.set("")
        bill_no.set("")
        


    # ---------------- SEARCH EXPENSE ----------------
    def search_expense(*_):
        text = search_var.get().strip()
        if not text:
            return
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
 # expense_date.set_date(date.today())
        cur.execute("""
            SELECT *
            FROM expenses
            WHERE expense_name LIKE %s
            OR category LIKE %s
            OR paid_to LIKE %s
            ORDER BY expense_date DESC
            LIMIT 1
        """, (
            f"%{text}%",
            f"%{text}%",
            f"%{text}%"
        ))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showinfo("Not Found", "Expense not found")
            return

        # ---------------- LOAD DATA INTO FORM ----------------
        current_expense_id.set(row["expense_id"])

        # expense_date.set_date(row["expense_date"])
        category.set(row["category"])
        expense_name.set(row["expense_name"])
        amount.set(str(row["amount"]))
        payment_mode.set(row["payment_mode"] or "")
        paid_to.set(row["paid_to"] or "")
        bill_no.set(row["bill_no"] or "")

       
        mode.set("UPDATE")
        update_mode_ui()



    search_entry.bind("<KeyRelease>", search_expense)

    # ---------------- SAVE ----------------
    def save_expense():
        if not expense_name.get() or not amount.get():
            messagebox.showwarning(
                "Missing",
                "Expense Name & Amount required"
            )
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            # -------- UPDATE EXPENSE --------
            if mode.get() == "UPDATE" and current_expense_id.get() != 0:
                cur.execute("""
                    UPDATE expenses SET
                        expense_date=%s,
                        category=%s,
                        expense_name=%s,
                        amount=%s,
                        payment_mode=%s,
                        paid_to=%s,
                        bill_no=%s,
                        notes=%s
                    WHERE expense_id=%s
                """, (
                    date.today(),                      # ✅ expense_date
                    category.get(),
                    expense_name.get(),
                    amount.get(),
                    payment_mode.get() or None,
                    paid_to.get() or None,
                    bill_no.get() or None,
                    None,                              # ✅ notes = NULL
                    current_expense_id.get()
                ))


                messagebox.showinfo(
                    "Success",
                    "✅ Expense updated successfully"
                )

            # -------- INSERT EXPENSE --------
            else:
                cur.execute("""
                    INSERT INTO expenses
                    (expense_date, category, expense_name,
                    amount, payment_mode, paid_to,
                    bill_no, notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    date.today(),                      # ✅ expense_date
                    category.get(),
                    expense_name.get(),
                    amount.get(),
                    payment_mode.get() or None,
                    paid_to.get() or None,
                    bill_no.get() or None,
                    None                               # ✅ notes = NULL
                ))



                messagebox.showinfo(
                    "Success",
                    "✅ Expense added successfully"
                )

            conn.commit()

            clear_form()
            mode.set("ADD")
            update_mode_ui()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()



    # ---------------- SAVE BUTTON ----------------
    save_btn = tk.Button(
        win,
        text="💾 Save Expense",
        bg=SELECTED_COLOR,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18,
        pady=6,
        command=save_expense
    )
    save_btn.pack(pady=10)

    update_mode_ui()
    win.bind("<Return>", lambda e: save_expense())

# -------------------------------------------------------------------------------------------------------------------------------------

def open_income_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    search_active = False
    last_search_keyword = ""

    def set_search_active(val):
        nonlocal search_active
        search_active = val

    def set_last_keyword(val):
        nonlocal last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Income",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")

            # Income row full text
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        # Empty search → reset
        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # Reset zebra first
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        # Apply highlight safely
        tree.after_idle(apply_search_highlight)



    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)

    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    box_add = fixed_box(action_row, 140, 30)

    btn_add_expense = tk.Button(
        box_add,
        text="➕ Add Income",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=lambda: open_add_income_window(workspace,shop_id,income_id=None)
    )

    btn_add_expense.pack(fill="both", expand=True)


    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)
    tk.Label(box_from, text="From", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")

    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)
    tk.Label(box_to, text="To", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")

    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

   # ---------------- TABLE FRAME ----------------
   # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = (
        "date", "type", "customer", "invoice",
        "amount", "gst_app", "gst_amt", "net_amt",
        "mode", "received", "ref", "status",
        "desc", "created",
        "delete",      # 🗑 DELETE COLUMN
        "id"           # 🔒 HIDDEN income_id
    )


    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    # ---------------- TAG COLORS ----------------
    tree.tag_configure("received", background="#BBF7D0")   # green
    tree.tag_configure("pending", background="#FECACA")    # red
    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("match", background="#BBF7D0")

    # ---------------- HEADERS ----------------
    headers = [
        "Date",
        "Income Type",
        "Customer Name",
        "Invoice No",
        "Amount",
        "GST?",
        "GST Amount",
        "Net Amount",
        "Payment Mode",
        "Received By",
        "Reference No",
        "Status",
        "Description",
        "Created At",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    # ---------------- COLUMN SETTINGS ----------------
    tree.column("date", width=90, anchor="center")
    tree.column("type", width=120, anchor="center")
    tree.column("customer", width=160, anchor="w")
    tree.column("invoice", width=110, anchor="center")

    tree.column("amount", width=90, anchor="e")
    tree.column("gst_app", width=60, anchor="center")
    tree.column("gst_amt", width=110, anchor="e")
    tree.column("net_amt", width=110, anchor="e")

    tree.column("mode", width=120, anchor="center")
    tree.column("received", width=130, anchor="center")
    tree.column("ref", width=120, anchor="center")
    tree.column("status", width=90, anchor="center")

    tree.column("desc", width=200, anchor="w")
    tree.column("created", width=150, anchor="center")

    tree.column("delete", width=70, anchor="center")   # 🗑
    tree.column("id", width=0, stretch=False)           # 🔒 hidden

    # ---------------- SCROLLBARS ----------------
    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    # ---------------- GRID LAYOUT (IMPORTANT) ----------------
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    # ---------------- GRID WEIGHT (THIS IS THE KEY 🔑) ----------------
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

     # =================================================
    # TOTAL SUMMARY BAR (BELOW TABLE)
    # =================================================
    summary_bar = tk.Frame(main, bg="#F1F5F9", height=40)
    summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    summary_bar.pack_propagate(False)

    lbl_total = tk.Label(
        summary_bar,
        text="Total : ₹0",
        bg="#F1F5F9",
        fg="black",
        font=("Segoe UI", 10, "bold")
    )
    lbl_total.pack(side="left", padx=20)

    lbl_cash = tk.Label(
        summary_bar,
        text="Cash : ₹0",
        bg="#F1F5F9",
        fg="#16A34A",
        font=("Segoe UI", 10, "bold")
    )
    lbl_cash.pack(side="left", padx=20)

    lbl_credit = tk.Label(
        summary_bar,
        text="Credit : ₹0",
        bg="#F1F5F9",
        fg="#DC2626",
        font=("Segoe UI", 10, "bold")
    )
    lbl_credit.pack(side="left", padx=20)

    def update_totals():
        total = 0
        cash_total = 0
        credit_total = 0

        for item in tree.get_children():
            values = tree.item(item, "values")

            # safety check
            if len(values) < 9:
                continue

            # ✅ AMOUNT (index 4)
            amt_str = str(values[4]).replace("₹", "").replace(",", "").strip()
            try:
                amt = float(amt_str)
            except:
                amt = 0

            # ✅ PAYMENT MODE (index 8)
            mode = str(values[8]).lower().strip()

            total += amt

            if mode == "cash":
                cash_total += amt
            else:
                credit_total += amt

        lbl_total.config(text=f"Total : ₹{total:,.0f}")
        lbl_cash.config(text=f"Cash : ₹{cash_total:,.0f}")
        lbl_credit.config(text=f"Credit : ₹{credit_total:,.0f}")


    update_totals()


    # =================================================
    # LOAD EXPENSES (SINGLE FUNCTION)
    # =================================================
    def load_income(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT 
                income_date,
                income_type,
                customer_name,
                invoice_no,
                amount,
                gst_applied,
                gst_amount,
                net_amount,
                payment_mode,
                received_by,
                reference_no,
                status,
                description,
                created_at,
                income_id
            FROM income
            WHERE 1=1
        """

        params = []

        # 🔍 Search filter
        if search:
            query += """
                AND (
                    customer_name LIKE %s OR
                    income_type LIKE %s OR
                    invoice_no LIKE %s OR
                    payment_mode LIKE %s OR
                    received_by LIKE %s OR
                    status LIKE %s
                )
            """
            params.extend([
                f"%{search}%", f"%{search}%", f"%{search}%",
                f"%{search}%", f"%{search}%", f"%{search}%"
            ])

        # 📅 Date filter
        if from_dt and to_dt:
            query += " AND income_date BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += " ORDER BY income_date DESC"

        cur.execute(query, tuple(params))

        for i, r in enumerate(cur.fetchall()):

            tag = "even" if i % 2 == 0 else "odd"
            if r[11] == "Received":
                tag = "received"
            elif r[11] == "Pending":
                tag = "pending"

            tree.insert(
                "",
                "end",
                values=(
                    r[0].strftime("%d-%m-%Y"),      # date
                    r[1],                           # income_type
                    r[2] or "",                     # customer
                    r[3] or "",                     # invoice
                    f"₹{r[4]:,.2f}",                # amount
                    "Yes" if r[5] else "No",        # gst?
                    f"₹{r[6]:,.2f}",                # gst amount
                    f"₹{r[7]:,.2f}" if r[7] else "",# net
                    r[8],                           # payment mode
                    r[9] or "",                     # received by
                    r[10] or "",                    # reference
                    r[11],                          # status
                    r[12] or "",                    # description
                    r[13].strftime("%d-%m-%Y %H:%M"), # created
                    "🗑",                           # 🔥 DELETE ICON
                    r[14]                           # 🔒 income_id
                ),
                tags=(tag,)
            )

        conn.close()

        if search_active:
            apply_search_highlight()
        else:
            restore_zebra()

        update_totals()


    def delete_income(income_id):
        if not messagebox.askyesno("Confirm", "Delete this income?"):
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM income WHERE income_id=%s", (income_id,))
        conn.commit()
        conn.close()

        load_income()


    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 🗑 DELETE COLUMN
        if col_id == "#15":
            values = tree.item(row_id, "values")

            # safety
            if len(values) < 16:
                return

            income_id = values[15]   # 🔒 hidden id
            delete_income(income_id)

    tree.bind("<Button-1>", on_tree_click)


   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


    tree.tag_configure("even", background="#3B81C7")
    tree.tag_configure("odd", background="#EEF2F7")


    # ---------------- INLINE EDIT ----------------
    edit_entry = None

    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        # ❌ Date & hidden ID editable illa
        if not row_id or col in ("#1", "#15"):
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)

        # 🔥 ₹ strip pannitu show
        edit_entry.insert(0, value.replace("₹", "").replace(",", ""))
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            # UI update (₹ add back)
            if col in ("#5", "#7", "#8"):   # amount / gst / net
                try:
                    new_val_fmt = f"₹{float(new_val):,.2f}"
                except:
                    new_val_fmt = "₹0.00"
                tree.set(row_id, col, new_val_fmt)
            else:
                tree.set(row_id, col, new_val)

            update_income_db(row_id, col, new_val)

            update_totals()      # ✅ LIVE TOTAL / CASH / CREDIT UPDATE

            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())

    tree.bind("<Double-1>", on_double_click)

    col_map = {
        "#1": "income_date",
        "#2": "income_type",
        "#3": "customer_name",
        "#4": "invoice_no",
        "#5": "amount",          # 🔥 NUMERIC
        "#6": "gst_applied",
        "#7": "gst_amount",      # 🔥 NUMERIC
        "#8": "net_amount",      # 🔥 NUMERIC
        "#9": "payment_mode",
        "#10": "received_by",
        "#11": "reference_no"
    }


    def clean_numeric(val):
        if val is None:
            return None
        return val.replace("₹", "").replace(",", "").strip()

    # ---------------- UPDATE DB ----------------
    def update_income_db(row_id, col, value):
        db_col = col_map.get(col)
        if not db_col:
            return

        income_id = tree.item(row_id)["values"][-1]  # 🔥 last column = income_id

        # 🔥 Numeric fields clean pannanum
        if db_col in ("amount", "gst_amount", "net_amount"):
            value = clean_numeric(value)

            try:
                value = float(value)
            except:
                value = 0

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE income
            SET {db_col}=%s
            WHERE income_id=%s
            """,
            (value, income_id)
        )

        conn.commit()
        conn.close()



    # ---------------- APPLY / CLEAR LOGIC ----------------
    date_filter_active = False

    def toggle_date_filter():
        nonlocal date_filter_active

        if not date_filter_active:
            # ✅ DateEntry → DATE object (MySQL compatible)
            from_date = start_date.get_date()
            to_date   = end_date.get_date()

            load_income(
                search=search_var.get().strip(),
                from_dt=from_date,
                to_dt=to_date
            )

            btn_apply.config(text="Clear", bg="#dc2626")
            date_filter_active = True

        else:
            load_income(search=search_var.get().strip())
            btn_apply.config(text="🔍 Apply", bg="#192987")
            date_filter_active = False

    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)

    # ---------------- SEARCH BIND ----------------
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_income(search_var.get().strip())
    )

    load_income()

   
def open_add_income_window(workspace, shop_id, income_id=None):

    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date
    current_income_id = tk.IntVar(value=0)

    if income_id:
        current_income_id.set(income_id)




    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------

    # ================= BASE CONTENT FRAME =================
    if not hasattr(workspace, "content"):
        workspace.content = tk.Frame(workspace, bg="white")
        workspace.content.place(relx=0, rely=0, relwidth=1, relheight=1)

    workspace.update_idletasks()  # 🔑 IMPORTANT

    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )

    # 🔥 OPEN MAXIMIZED BY DEFAULT
    win.place(
        relx=0.5,
        rely=0.5,
        anchor="center",
        width=workspace.winfo_width() - 40,
        height=workspace.winfo_height() - 40
    )

    is_maximized = True   # 🔥 DEFAULT TRUE
    mode = tk.StringVar(value="ADD")
    current_staff_id = tk.IntVar(value=0)

    if income_id:
        mode.set("UPDATE")

    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_income_page(workspace, shop_id)

    def toggle_zoom():
        nonlocal is_maximized

        if is_maximized:
            # 🔽 RESTORE (NORMAL SIZE)
            win.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
                width=650,
                height=580
            )
            is_maximized = False
        else:
            # 🔼 MAXIMIZE
            win.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
                width=workspace.winfo_width() - 40,
                height=workspace.winfo_height() - 40
            )
            is_maximized = True

    # ---------------- TITLE BAR BUTTONS ----------------
    tk.Button(
        title_bar,
        text="✖",
        width=3,
        bd=0,
        bg="black",
        fg="red",
        command=close_window
    ).pack(side="right")

    tk.Button(
        title_bar,
        text="⛶",
        width=3,
        bd=0,
        bg="black",
        fg="white",
        command=toggle_zoom
    ).pack(side="right")


    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Income")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Income")
            clear_form(reset_id=True)
        else:
            header_lbl.config(text="Update Income")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Income")

    add_btn = tk.Button(
        top_bar, text="Add Income",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Income",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    # ================= SEARCH ROW =================
    search_var = tk.StringVar()

    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))

    tk.Label(
        search_row,
        text="Search:",
        bg="white",
        fg="black",
        font=("Segoe UI", 9),
        width=18,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")


    # ================= HEADER =================
    header_lbl = tk.Label(
        win,
        text="Add Income",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))


    # ================= FORM CARD =================
    card = tk.Frame(win, bg="white")

    # 🔥 IMPORTANT: expand=False + anchor="n"
    card.pack(
        fill="x",
        expand=False,
        padx=30,
        pady=(10, 10),     # 👈 top-la move
        anchor="n"
    )

    # ---------------- GRID CONFIG ----------------
    card.columnconfigure(0, weight=1, uniform="a")
    card.columnconfigure(1, weight=1, uniform="a")

    # 🔥 Force content stick to TOP
    card.grid_rowconfigure("all", weight=0)

    FIELD_WIDTH = 38


    # ================= IEEE FIELD =================
    def ieee_field(parent, label, row, col, var=None):
        if var is None:
            var = tk.StringVar()

        box = tk.Frame(parent, bg="white")
        box.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=12,
            pady=4          # 🔥 reduce vertical gap
        )

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        tk.Entry(
            box,
            textvariable=var,
            width=FIELD_WIDTH,
            bg="white",
            fg="black",
            relief="solid",
            bd=1
        ).pack(fill="x", pady=2)

        return var


    def ieee_dropdown(parent, label, row, col, var, values):
        box = tk.Frame(parent, bg="white")
        box.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=12,
            pady=4          # 🔥 reduce vertical gap
        )

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        opt = tk.OptionMenu(box, var, *values)
        opt.config(
            bg="white",
            fg="black",
            relief="solid",
            bd=1
        )
        opt.pack(fill="x", pady=2)


    # ================= ROW 0 =================
    customer_name = ieee_field(card, "Customer Name", 0, 0)
    amount        = ieee_field(card, "Amount", 0, 1)

    # ================= ROW 1 =================
    received_by   = ieee_field(card, "Received By", 1, 0)
    invoice_no    = ieee_field(card, "Invoice No", 1, 1)

    # ================= ROW 2 =================
    reference_no  = ieee_field(card, "Reference No", 2, 0)
    net_amount    = ieee_field(card, "Net Amount", 2, 1)

    # ================= ROW 3 =================
    payment_mode = tk.StringVar(value="Cash")
    income_type  = tk.StringVar(value="Sales")

    ieee_dropdown(
        card, "Payment Mode", 3, 0,
        payment_mode,
        ["Cash", "UPI", "Card", "Bank Transfer"]
    )

    ieee_dropdown(
        card, "Income Type", 3, 1,
        income_type,
        ["Sales", "Service", "Commission", "Other"]
    )

    # ================= ROW 4 =================
    gst_applied = tk.StringVar(value="No")
    gst_amount  = tk.StringVar()

    ieee_dropdown(
        card, "GST Applied", 4, 0,
        gst_applied,
        ["No", "Yes"]
    )

    ieee_field(card, "GST Amount", 4, 1, gst_amount)

    # ================= FORM HELPERS =================
    def clear_form(reset_id=True):
        customer_name.set("")
        amount.set("")
        received_by.set("")
        invoice_no.set("")
        reference_no.set("")
        payment_mode.set("Cash")
        income_type.set("Sales")
        gst_applied.set("No")
        gst_amount.set("")
        net_amount.set("")

        
    def clear_income_form():
        current_income_id.set(0)
        clear_income_fields_only()

        mode.set("ADD")
        update_mode_ui()


    def clear_income_fields_only():
        customer_name.set("")
        amount.set("")
        received_by.set("")
        invoice_no.set("")
        reference_no.set("")

        payment_mode.set("Cash")
        income_type.set("Sales")

        gst_applied.set("No")
        gst_amount.set("")
        net_amount.set("")

        # 🔴 IMPORTANT: DO NOT TOUCH
        # current_income_id
        # mode


    # ---------------- SEARCH EXPENSE ----------------
    def search_income(*_):
        text = search_var.get().strip()

        # 🔥 SEARCH CLEARED → ONLY CLEAR FIELDS (STAY IN UPDATE MODE)
        if not text:
            clear_income_fields_only()
            update_mode_ui()
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM income
            WHERE customer_name LIKE %s
            ORDER BY income_date DESC
            LIMIT 1
        """, (f"%{text}%",))

        row = cur.fetchone()
        conn.close()

        if not row:
            clear_income_fields_only()
            return

        # ---------------- LOAD DATA INTO FORM ----------------
        current_income_id.set(row["income_id"])

        customer_name.set(row["customer_name"] or "")
        amount.set(str(row["amount"]))
        payment_mode.set(row["payment_mode"] or "")
        received_by.set(row["received_by"] or "")
        invoice_no.set(row["invoice_no"] or "")
        reference_no.set(row["reference_no"] or "")

        income_type.set(row["income_type"] or "")

        gst_applied.set("Yes" if row["gst_applied"] else "No")
        gst_amount.set(str(row["gst_amount"] or ""))
        net_amount.set(str(row["net_amount"] or ""))

        mode.set("UPDATE")
        update_mode_ui()



    search_entry.bind("<KeyRelease>", search_income)


   # ---------------- SAVE INCOME ----------------
    def save_income():
        if not customer_name.get() or not amount.get():
            messagebox.showwarning(
                "Missing",
                "Customer Name & Amount required"
            )
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            # -------- UPDATE INCOME --------
            if mode.get() == "UPDATE" and current_income_id.get() != 0:
                cur.execute("""
                    UPDATE income SET
                        income_date=%s,
                        income_type=%s,
                        customer_name=%s,
                        amount=%s,
                        payment_mode=%s,
                        received_by=%s,
                        invoice_no=%s,
                        reference_no=%s,
                        gst_applied=%s,
                        gst_amount=%s,
                        net_amount=%s
                    WHERE income_id=%s
                """, (
                    date.today(),                             # income_date
                    income_type.get(),
                    customer_name.get(),
                    amount.get(),
                    payment_mode.get() or None,
                    received_by.get() or None,
                    invoice_no.get() or None,
                    reference_no.get() or None,
                    1 if gst_applied.get() == "Yes" else 0,
                    gst_amount.get() or 0,
                    net_amount.get() or amount.get(),
                    current_income_id.get()
                ))

                messagebox.showinfo(
                    "Success",
                    "✅ Income updated successfully"
                )

            # -------- INSERT INCOME --------
            else:
                cur.execute("""
                    INSERT INTO income
                    (income_date, income_type, customer_name,
                    amount, payment_mode, received_by,
                    invoice_no, reference_no,
                    gst_applied, gst_amount, net_amount)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    date.today(),                             # income_date
                    income_type.get(),
                    customer_name.get(),
                    amount.get(),
                    payment_mode.get() or None,
                    received_by.get() or None,
                    invoice_no.get() or None,
                    reference_no.get() or None,
                    1 if gst_applied.get() == "Yes" else 0,
                    gst_amount.get() or 0,
                    net_amount.get() or amount.get()
                ))

                messagebox.showinfo(
                    "Success",
                    "✅ Income added successfully"
                )

            conn.commit()

            clear_form()
            current_income_id.set(0)
            mode.set("ADD")
            update_mode_ui()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()
    save_btn = tk.Button(
        win,
        text="💾 Save Income",
        bg=SELECTED_COLOR,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18,
        pady=6,
        command=save_income
    )
    save_btn.pack(pady=10)

    update_mode_ui()
    win.bind("<Return>", lambda e: save_income())


# -------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------------------------------------

def open_banks_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    search_active = False
    last_search_keyword = ""

    def set_search_active(val):
        nonlocal search_active
        search_active = val

    def set_last_keyword(val):
        nonlocal last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Banks",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")

            # Income row full text
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        # Empty search → reset
        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # Reset zebra first
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        # Apply highlight safely
        tree.after_idle(apply_search_highlight)



    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)

    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    box_add = fixed_box(action_row, 140, 30)

    btn_add_expense = tk.Button(
        box_add,
        text="➕ Add Banks",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=lambda: open_add_bank_window(workspace, shop_id, bank_id=None)
    )

    btn_add_expense.pack(fill="both", expand=True)


    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)
    tk.Label(box_from, text="From", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")

    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)
    tk.Label(box_to, text="To", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")

    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

   # ---------------- TABLE FRAME ----------------
    # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = (
        "bank_name",
        "holder",
        "account_no",
        "ifsc",
        "type",
        "opening",
        "current",
        "remarks",
        "status",
        "created",
        "updated",
        "delete",     # 🗑 DELETE
        "id"          # 🔒 HIDDEN bank_id
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )


    # ---------------- TAG COLORS ----------------
    tree.tag_configure("even", background="#7BACDD")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("active", background="#BBF7D0")
    tree.tag_configure("inactive", background="#FECACA")


    # ---------------- HEADERS ----------------
    headers = [
        "Bank Name",
        "Account Holder",
        "Account No",
        "IFSC Code",
        "Bank Type",
        "Opening Balance",
        "Current Balance",
        "Remarks",
        "Status",
        "Created At",
        "Updated At",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)


    tree.column("bank_name", width=140, anchor="w")
    tree.column("holder", width=140, anchor="w")
    tree.column("account_no", width=130, anchor="center")
    tree.column("ifsc", width=120, anchor="center")

    tree.column("type", width=90, anchor="center")

    tree.column("opening", width=120, anchor="e")
    tree.column("current", width=120, anchor="e")

    tree.column("remarks", width=180, anchor="w")
    tree.column("status", width=90, anchor="center")

    tree.column("created", width=150, anchor="center")
    tree.column("updated", width=150, anchor="center")

    tree.column("delete", width=70, anchor="center")
    tree.column("id", width=0, stretch=False)   # 🔒 hidden
          # 🔒 hidden

    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

     # =================================================
    # TOTAL SUMMARY BAR (BELOW TABLE)
    # =================================================
    summary_bar = tk.Frame(main, bg="#F1F5F9", height=40)
    summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    summary_bar.pack_propagate(False)

    lbl_total = tk.Label(
        summary_bar,
        text="Total : ₹0",
        bg="#F1F5F9",
        fg="black",
        font=("Segoe UI", 10, "bold")
    )
    lbl_total.pack(side="left", padx=20)

    lbl_cash = tk.Label(
        summary_bar,
        text="Cash : ₹0",
        bg="#F1F5F9",
        fg="#16A34A",
        font=("Segoe UI", 10, "bold")
    )
    lbl_cash.pack(side="left", padx=20)

    lbl_credit = tk.Label(
        summary_bar,
        text="Credit : ₹0",
        bg="#F1F5F9",
        fg="#DC2626",
        font=("Segoe UI", 10, "bold")
    )
    lbl_credit.pack(side="left", padx=20)

    def update_bank_totals():
        total = 0
        cash_total = 0
        other_total = 0

        for item in tree.get_children():
            values = tree.item(item, "values")

            # safety
            if len(values) < 9:
                continue

            # ✅ CURRENT BALANCE (index 6)
            bal_str = str(values[6]).replace("₹", "").replace(",", "").strip()
            try:
                bal = float(bal_str)
            except:
                bal = 0

            # ✅ BANK TYPE (index 4)
            bank_type = str(values[4]).lower().strip()

            total += bal

            if bank_type == "cash":
                cash_total += bal
            else:
                other_total += bal

        lbl_total.config(text=f"Total : ₹{total:,.0f}")
        lbl_cash.config(text=f"Cash : ₹{cash_total:,.0f}")
        lbl_credit.config(text=f"Other : ₹{other_total:,.0f}")



    update_bank_totals()


    # =================================================
    # LOAD EXPENSES (SINGLE FUNCTION)
    # =================================================
    def load_banks(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                bank_name,
                account_holder,
                account_no,
                ifsc_code,
                bank_type,
                opening_balance,
                current_balance,
                remarks,
                status,
                created_at,
                updated_at,
                bank_id
            FROM banks
            WHERE 1=1
        """

        params = []

        # 🔍 SEARCH FILTER
        if search:
            query += """
                AND (
                    bank_name LIKE %s OR
                    account_holder LIKE %s OR
                    bank_type LIKE %s OR
                    status LIKE %s
                )
            """
            s = f"%{search}%"
            params.extend([s, s, s, s])

        # 📅 DATE FILTER (created_at)
        if from_dt and to_dt:
            query += " AND DATE(created_at) BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += " ORDER BY bank_name"

        cur.execute(query, tuple(params))

        for i, r in enumerate(cur.fetchall()):
            tag = "even" if i % 2 == 0 else "odd"

            if r[8] == "Active":
                tag = "active"
            else:
                tag = "inactive"

            tree.insert(
                "",
                "end",
                values=(
                    r[0],                          # bank name
                    r[1] or "",                   # holder
                    r[2] or "",                   # account no
                    r[3] or "",                   # ifsc
                    r[4],                          # bank type
                    f"₹{r[5]:,.2f}",               # opening balance
                    f"₹{r[6]:,.2f}",               # current balance
                    r[7] or "",                   # remarks
                    r[8],                          # status
                    r[9].strftime("%d-%m-%Y %H:%M"),
                    r[10].strftime("%d-%m-%Y %H:%M"),
                    "🗑",                          # delete icon
                    r[11]                          # 🔒 bank_id
                ),
                tags=(tag,)
            )

        conn.close()
        update_bank_totals()


        


    def delete_bank(bank_id):
        if not messagebox.askyesno("Confirm", "Delete this bank?"):
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM banks WHERE bank_id=%s", (bank_id,))
        conn.commit()
        conn.close()

        load_banks()


      


    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 🗑 DELETE column = #12
        if col_id == "#12":
            values = tree.item(row_id, "values")

            if len(values) < 13:
                return

            bank_id = values[12]   # 🔒 hidden bank_id
            delete_bank(bank_id)


    tree.bind("<Button-1>", on_tree_click)
    load_banks()

   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")

    # ---------------- INLINE EDIT ----------------
    edit_entry = None

    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        # ❌ Delete & hidden ID editable illa
        if not row_id or col in ("#12", "#13"):
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)

        # ₹ strip pannitu show
        edit_entry.insert(0, value.replace("₹", "").replace(",", ""))
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            # 🔥 Numeric columns (Opening / Current Balance)
            if col in ("#6", "#7"):
                try:
                    new_val_fmt = f"₹{float(new_val):,.2f}"
                except:
                    new_val_fmt = "₹0.00"
                tree.set(row_id, col, new_val_fmt)
            else:
                tree.set(row_id, col, new_val)

            update_bank_db(row_id, col, new_val)

            update_bank_totals()   # ✅ LIVE TOTAL UPDATE

            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())


    tree.bind("<Double-1>", on_double_click)

    bank_col_map = {
        "#1": "bank_name",
        "#2": "account_holder",
        "#3": "account_no",
        "#4": "ifsc_code",
        "#5": "bank_type",
        "#6": "opening_balance",     # 🔥 numeric
        "#7": "current_balance",     # 🔥 numeric
        "#8": "remarks",
        "#9": "status"
    }



    def clean_numeric(val):
        return val.replace("₹", "").replace(",", "").strip()


    # ---------------- UPDATE DB ----------------
    def update_bank_db(row_id, col, value):
        db_col = bank_col_map.get(col)
        if not db_col:
            return

        bank_id = tree.item(row_id)["values"][-1]  # 🔒 bank_id

        # Numeric cleanup
        if db_col in ("opening_balance", "current_balance"):
            value = clean_numeric(value)
            try:
                value = float(value)
            except:
                value = 0

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE banks
            SET {db_col}=%s
            WHERE bank_id=%s
            """,
            (value, bank_id)
        )

        conn.commit()
        conn.close()



    # ---------------- APPLY / CLEAR LOGIC ----------------
    date_filter_active = False

    def toggle_date_filter():
        nonlocal date_filter_active

        if not date_filter_active:
            # ✅ DateEntry → DATE object
            from_date = start_date.get_date()
            to_date   = end_date.get_date()

            load_banks(
                search=search_var.get().strip(),
                from_dt=from_date,
                to_dt=to_date
            )

            btn_apply.config(text="Clear", bg="#dc2626")
            date_filter_active = True

        else:
            load_banks(search=search_var.get().strip())
            btn_apply.config(text="🔍 Apply", bg="#192987")
            date_filter_active = False


    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)


    # ---------------- SEARCH BIND ----------------
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_banks(search=search_var.get().strip())
    )

    # ---------------- INITIAL LOAD ----------------
    load_banks()

def open_add_bank_window(workspace, shop_id, bank_id=None):

    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date
    current_bank_id = tk.IntVar(value=0)
    mode = tk.StringVar(value="ADD")


    if bank_id:
        current_bank_id.set(bank_id)




    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------

    # ================= BASE CONTENT FRAME =================
    if not hasattr(workspace, "content"):
        workspace.content = tk.Frame(workspace, bg="white")
        workspace.content.place(relx=0, rely=0, relwidth=1, relheight=1)

    workspace.update_idletasks()  # 🔑 IMPORTANT

    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )

    # 🔥 OPEN MAXIMIZED BY DEFAULT
    win.place(
        relx=0.5,
        rely=0.5,
        anchor="center",
        width=workspace.winfo_width() - 40,
        height=workspace.winfo_height() - 40
    )

    is_maximized = True   # 🔥 DEFAULT TRUE
    mode = tk.StringVar(value="ADD")
    current_staff_id = tk.IntVar(value=0)

    if bank_id:
        mode.set("UPDATE")

    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_banks_page(workspace, shop_id)

    def toggle_zoom():
        nonlocal is_maximized

        if is_maximized:
            # 🔽 RESTORE (NORMAL SIZE)
            win.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
                width=650,
                height=580
            )
            is_maximized = False
        else:
            # 🔼 MAXIMIZE
            win.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
                width=workspace.winfo_width() - 40,
                height=workspace.winfo_height() - 40
            )
            is_maximized = True

    # ---------------- TITLE BAR BUTTONS ----------------
    tk.Button(
        title_bar,
        text="✖",
        width=3,
        bd=0,
        bg="black",
        fg="red",
        command=close_window
    ).pack(side="right")

    tk.Button(
        title_bar,
        text="⛶",
        width=3,
        bd=0,
        bg="black",
        fg="white",
        command=toggle_zoom
    ).pack(side="right")


    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Banks")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Bank")
            clear_bank_form()
            current_bank_id.set(0)

        else:
            header_lbl.config(text="Update Bank")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Bank")

    add_btn = tk.Button(
        top_bar, text="Add Bank",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Bank",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    # ================= SEARCH ROW =================
    search_var = tk.StringVar()

    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))

    tk.Label(
        search_row,
        text="Search:",
        bg="white",
        fg="black",
        font=("Segoe UI", 9),
        width=18,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")


    # ================= HEADER =================
    header_lbl = tk.Label(
        win,
        text="Add Income",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))


    # ================= FORM CARD =================
    card = tk.Frame(win, bg="white")

    # 🔥 IMPORTANT: expand=False + anchor="n"
    card.pack(
        fill="x",
        expand=False,
        padx=30,
        pady=(10, 10),     # 👈 top-la move
        anchor="n"
    )

   # ================= FORM CARD =================
    card = tk.Frame(win, bg="white")
    card.pack(fill="x", expand=False, padx=30, pady=(10, 10), anchor="n")

    # Grid config
    card.columnconfigure(0, weight=1, uniform="a")
    card.columnconfigure(1, weight=1, uniform="a")

    FIELD_WIDTH = 38


    # ================= IEEE FIELD =================
    def ieee_field(parent, label, row, col, var=None):
        if var is None:
            var = tk.StringVar()

        box = tk.Frame(parent, bg="white")
        box.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        tk.Entry(
            box,
            textvariable=var,
            width=FIELD_WIDTH,
            bg="white",
            fg="black",
            relief="solid",
            bd=1
        ).pack(fill="x", pady=2)

        return var


    def ieee_dropdown(parent, label, row, col, var, values):
        box = tk.Frame(parent, bg="white")
        box.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        opt = tk.OptionMenu(box, var, *values)
        opt.config(bg="white", fg="black", relief="solid", bd=1)
        opt.pack(fill="x", pady=2)


    # ================= ROW 0 =================
    bank_name       = ieee_field(card, "Bank Name", 0, 0)
    account_holder  = ieee_field(card, "Account Holder", 0, 1)

    # ================= ROW 1 =================
    account_no = ieee_field(card, "Account No", 1, 0)
    ifsc_code  = ieee_field(card, "IFSC Code", 1, 1)

    # ================= ROW 2 =================
    opening_balance = ieee_field(card, "Opening Balance", 2, 0)
    current_balance = ieee_field(card, "Current Balance", 2, 1)

    # ================= ROW 3 =================
    bank_type = tk.StringVar(value="Bank")
    status    = tk.StringVar(value="Active")

    ieee_dropdown(
        card, "Bank Type", 3, 0,
        bank_type,
        ["Bank", "Cash", "UPI", "Card", "Wallet"]
    )

    ieee_dropdown(
        card, "Status", 3, 1,
        status,
        ["Active", "Inactive"]
    )

    # ================= ROW 4 =================
    remarks = ieee_field(card, "Remarks", 4, 0)


    # ================= FORM HELPERS =================
    def clear_bank_form():
        bank_name.set("")
        account_holder.set("")
        account_no.set("")
        ifsc_code.set("")

        opening_balance.set("")
        current_balance.set("")

        bank_type.set("Bank")
        status.set("Active")

        remarks.set("")

        
    def clear_banks_form():
        current_bank_id.set(0)
        clear_bank_fields_only()

        mode.set("ADD")
        update_mode_ui()

    def clear_bank_fields_only():
        bank_name.set("")
        account_holder.set("")
        account_no.set("")
        ifsc_code.set("")

        opening_balance.set("")
        current_balance.set("")

        bank_type.set("Bank")
        status.set("Active")

        remarks.set("")

        # 🔴 IMPORTANT: DO NOT TOUCH
        # current_bank_id
        # mode



    # ---------------- SEARCH EXPENSE ----------------
    def search_bank(*_):
        text = search_var.get().strip()

        # 🔥 SEARCH CLEARED → ONLY CLEAR FIELDS (STAY IN SAME MODE)
        if not text:
            clear_bank_fields_only()
            update_mode_ui()
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM banks
            WHERE
                bank_name LIKE %s
                OR account_holder LIKE %s
                OR account_no LIKE %s
                OR ifsc_code LIKE %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (
            f"%{text}%",
            f"%{text}%",
            f"%{text}%",
            f"%{text}%"
        ))

        row = cur.fetchone()
        conn.close()

        if not row:
            clear_bank_fields_only()
            return

        # ---------------- LOAD DATA INTO BANK FORM ----------------
        current_bank_id.set(row["bank_id"])

        bank_name.set(row["bank_name"] or "")
        account_holder.set(row["account_holder"] or "")
        account_no.set(row["account_no"] or "")
        ifsc_code.set(row["ifsc_code"] or "")

        opening_balance.set(str(row["opening_balance"] or ""))
        current_balance.set(str(row["current_balance"] or ""))

        bank_type.set(row["bank_type"] or "Bank")
        status.set(row["status"] or "Active")

        remarks.set(row["remarks"] or "")

        mode.set("UPDATE")
        update_mode_ui()



    search_entry.bind("<KeyRelease>", search_bank)


   # ---------------- SAVE INCOME ----------------
    def save_bank():
        # ---------------- VALIDATION ----------------
        if not bank_name.get():
            messagebox.showwarning(
                "Missing",
                "Bank Name is required"
            )
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            # -------- UPDATE BANK --------
            if mode.get() == "UPDATE" and current_bank_id.get() != 0:
                cur.execute("""
                    UPDATE banks SET
                        bank_name=%s,
                        account_holder=%s,
                        account_no=%s,
                        ifsc_code=%s,
                        bank_type=%s,
                        opening_balance=%s,
                        current_balance=%s,
                        remarks=%s,
                        status=%s
                    WHERE bank_id=%s
                """, (
                    bank_name.get(),
                    account_holder.get() or None,
                    account_no.get() or None,
                    ifsc_code.get() or None,
                    bank_type.get(),
                    opening_balance.get() or 0,
                    current_balance.get() or opening_balance.get() or 0,
                    remarks.get() or None,
                    status.get(),
                    current_bank_id.get()
                ))

                messagebox.showinfo(
                    "Success",
                    "✅ Bank updated successfully"
                )

            # -------- INSERT BANK --------
            else:
                cur.execute("""
                    INSERT INTO banks
                    (bank_name, account_holder, account_no, ifsc_code,
                    bank_type, opening_balance, current_balance,
                    remarks, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    bank_name.get(),
                    account_holder.get() or None,
                    account_no.get() or None,
                    ifsc_code.get() or None,
                    bank_type.get(),
                    opening_balance.get() or 0,
                    current_balance.get() or opening_balance.get() or 0,
                    remarks.get() or None,
                    status.get()
                ))

                messagebox.showinfo(
                    "Success",
                    "✅ Bank added successfully"
                )

            conn.commit()

            # ---------------- RESET ----------------
            clear_bank_form()
            current_bank_id.set(0)
            mode.set("ADD")
            update_mode_ui()

             # 🔥load_banks()   refresh table

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()

    save_btn = tk.Button(
        win,
        text="💾 Save Bank",
        bg=SELECTED_COLOR,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18,
        pady=6,
        command=save_bank
    )
    save_btn.pack(pady=10)

    update_mode_ui()
    win.bind("<Return>", lambda e: save_bank())


# -------------------------------------------------------------------------------------------------------------------------------------

def open_taxes_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    search_active = False
    last_search_keyword = ""

    def set_search_active(val):
        nonlocal search_active
        search_active = val

    def set_last_keyword(val):
        nonlocal last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Tax Details",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")

            # Income row full text
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        # Empty search → reset
        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # Reset zebra first
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        # Apply highlight safely
        tree.after_idle(apply_search_highlight)



    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)

    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    box_add = fixed_box(action_row, 140, 30)

    btn_add_expense = tk.Button(
        box_add,
        text="➕ Add Tax",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=lambda: open_add_tax_window(workspace, shop_id, tax_id=None)
    )

    btn_add_expense.pack(fill="both", expand=True)


    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)
    tk.Label(box_from, text="From", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")

    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)
    tk.Label(box_to, text="To", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")

    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

   
    # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = (
        "tax_name",
        "tax_code",
        "tax_type",
        "tax_rate",
        "applied_on",
        "compound",
        "status",
        "remarks",
        "created",
        "updated",
        "delete",     # 🗑 DELETE
        "id"          # 🔒 HIDDEN tax_id
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    # ---------------- TAG COLORS ----------------
    tree.tag_configure("even", background="#7BACDD")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("active", background="#BBF7D0")
    tree.tag_configure("inactive", background="#FECACA")

    # ---------------- HEADERS ----------------
    headers = [
        "Tax Name",
        "Tax Code",
        "Tax Type",
        "Tax Rate (%)",
        "Applied On",
        "Compound?",
        "Status",
        "Remarks",
        "Created At",
        "Updated At",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    # ---------------- COLUMN SETTINGS ----------------
    tree.column("tax_name", width=140, anchor="w")
    tree.column("tax_code", width=100, anchor="center")

    tree.column("tax_type", width=100, anchor="center")
    tree.column("tax_rate", width=110, anchor="e")

    tree.column("applied_on", width=100, anchor="center")
    tree.column("compound", width=90, anchor="center")

    tree.column("status", width=90, anchor="center")
    tree.column("remarks", width=180, anchor="w")

    tree.column("created", width=150, anchor="center")
    tree.column("updated", width=150, anchor="center")

    tree.column("delete", width=70, anchor="center")
    tree.column("id", width=0, stretch=False)   # 🔒 hidden

    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    #  # =================================================
    # # TOTAL SUMMARY BAR (BELOW TABLE)
    # # =================================================
    # summary_bar = tk.Frame(main, bg="#F1F5F9", height=40)
    # summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    # summary_bar.pack_propagate(False)

    # lbl_total = tk.Label(
    #     summary_bar,
    #     text="Total : ₹0",
    #     bg="#F1F5F9",
    #     fg="black",
    #     font=("Segoe UI", 10, "bold")
    # )
    # lbl_total.pack(side="left", padx=20)

    # lbl_cash = tk.Label(
    #     summary_bar,
    #     text="Cash : ₹0",
    #     bg="#F1F5F9",
    #     fg="#16A34A",
    #     font=("Segoe UI", 10, "bold")
    # )
    # lbl_cash.pack(side="left", padx=20)

    # lbl_credit = tk.Label(
    #     summary_bar,
    #     text="Credit : ₹0",
    #     bg="#F1F5F9",
    #     fg="#DC2626",
    #     font=("Segoe UI", 10, "bold")
    # )
    # lbl_credit.pack(side="left", padx=20)                        *Important*
                          
    # def update_bank_totals():
    #     total = 0
    #     cash_total = 0
    #     other_total = 0

    #     for item in tree.get_children():
    #         values = tree.item(item, "values")

    #         # safety
    #         if len(values) < 9:
    #             continue

    #         # ✅ CURRENT BALANCE (index 6)
    #         bal_str = str(values[6]).replace("₹", "").replace(",", "").strip()
    #         try:
    #             bal = float(bal_str)
    #         except:
    #             bal = 0

    #         # ✅ BANK TYPE (index 4)
    #         bank_type = str(values[4]).lower().strip()

    #         total += bal

    #         if bank_type == "cash":
    #             cash_total += bal
    #         else:
    #             other_total += bal

    #     lbl_total.config(text=f"Total Tax : ₹{total:,.0f}")
    #     lbl_cash.config(text=f"Cash : ₹{cash_total:,.0f}")
    #     lbl_credit.config(text=f"Other : ₹{other_total:,.0f}")



    # update_bank_totals()


    # =================================================
    # LOAD EXPENSES (SINGLE FUNCTION)
    # =================================================
    def load_taxes(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                tax_name,
                tax_code,
                tax_type,
                tax_rate,
                applied_on,
                is_compound,
                status,
                remarks,
                created_at,
                updated_at,
                tax_id
            FROM tax_master
            WHERE 1=1
        """

        params = []

        # 🔍 SEARCH FILTER
        if search:
            query += """
                AND (
                    tax_name LIKE %s OR
                    tax_code LIKE %s OR
                    tax_type LIKE %s OR
                    applied_on LIKE %s OR
                    status LIKE %s
                )
            """
            s = f"%{search}%"
            params.extend([s, s, s, s, s])

        # 📅 DATE FILTER (created_at)
        if from_dt and to_dt:
            query += " AND DATE(created_at) BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += " ORDER BY tax_name"

        cur.execute(query, tuple(params))

        for i, r in enumerate(cur.fetchall()):
            tag = "even" if i % 2 == 0 else "odd"

            if r[6] == "Active":
                tag = "active"
            else:
                tag = "inactive"

            tree.insert(
                "",
                "end",
                values=(
                    r[0],                              # tax_name
                    r[1] or "",                       # tax_code
                    r[2],                              # tax_type
                    f"{r[3]:.2f}%",                    # tax_rate
                    r[4],                              # applied_on
                    "Yes" if r[5] else "No",            # compound
                    r[6],                              # status
                    r[7] or "",                       # remarks
                    r[8].strftime("%d-%m-%Y %H:%M"),  # created_at
                    r[9].strftime("%d-%m-%Y %H:%M"),  # updated_at
                    "🗑",                              # delete icon
                    r[10]                              # 🔒 tax_id
                ),
                tags=(tag,)
            )

        conn.close()

        # update_bank_totals()


        


    def delete_tax(tax_id):
        if not messagebox.askyesno("Confirm", "Delete this tax?"):
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM tax_master WHERE tax_id=%s", (tax_id,))
        conn.commit()
        conn.close()

        load_taxes()

      


    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 🗑 DELETE column
        if col_id == "#11":
            values = tree.item(row_id, "values")

            # safety check
            if len(values) < 12:
                return

            tax_id = values[11]   # 🔒 hidden tax_id
            delete_tax(tax_id)


    tree.bind("<Button-1>", on_tree_click)
    load_taxes()

   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")

   
    edit_entry = None

    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        # ❌ Delete & hidden ID editable illa
        if not row_id or col in ("#11", "#12"):
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)

        # % remove pannitu show (tax_rate)
        edit_entry.insert(0, value.replace("%", "").strip())
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            # 🔥 TAX RATE (column #4)
            if col == "#4":
                try:
                    new_val_fmt = f"{float(new_val):.2f}%"
                except:
                    new_val_fmt = "0.00%"
                tree.set(row_id, col, new_val_fmt)

            # 🔥 OTHER COLUMNS (ENUM / TEXT)
            else:
                tree.set(row_id, col, new_val)

            # 🔥 SAFE DB UPDATE (ENUM handled inside)
            update_tax_db(row_id, col, new_val)

            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())


    tree.bind("<Double-1>", on_double_click)


    tax_col_map = {
        "#1": "tax_name",
        "#2": "tax_code",
        "#3": "tax_type",
        "#4": "tax_rate",      # 🔥 numeric
        "#5": "applied_on",
        "#6": "is_compound",
        "#7": "status",
        "#8": "remarks"
    }



    def clean_numeric(val):
        return val.replace("%", "").strip()


    # ---------------- UPDATE DB ----------------
    def update_tax_db(row_id, col, value):
        db_col = tax_col_map.get(col)
        if not db_col:
            return

        tax_id = tree.item(row_id)["values"][-1]   # 🔒 tax_id

        # 🔥 TAX RATE (NUMERIC)
        if db_col == "tax_rate":
            value = value.replace("%", "").strip()
            try:
                value = float(value)
            except:
                value = 0

        # 🔥 TAX TYPE ENUM FIX (🔥 IMPORTANT)
        elif db_col == "tax_type":
            val = str(value).strip().lower()
            if val.startswith("p"):
                value = "Percentage"
            elif val.startswith("f"):
                value = "Fixed"
            else:
                value = "Percentage"   # safe default

        # 🔥 APPLIED ON ENUM FIX
        elif db_col == "applied_on":
            val = str(value).strip().lower()
            if val.startswith("inc"):
                value = "Income"
            elif val.startswith("exp"):
                value = "Expense"
            elif val.startswith("bo"):
                value = "Both"
            else:
                value = "Income"

        # 🔥 IS COMPOUND (Yes / No → 1 / 0)
        elif db_col == "is_compound":
            value = 1 if str(value).strip().lower().startswith("y") else 0

        # 🔥 STATUS ENUM FIX
        elif db_col == "status":
            value = "Active" if str(value).strip().lower().startswith("a") else "Inactive"

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE tax_master
            SET {db_col}=%s
            WHERE tax_id=%s
            """,
            (value, tax_id)
        )

        conn.commit()
        conn.close()






    # ---------------- APPLY / CLEAR LOGIC ----------------
    date_filter_active = False

    def toggle_date_filter():
        nonlocal date_filter_active

        if not date_filter_active:
            from_date = start_date.get_date()
            to_date   = end_date.get_date()

            load_taxes(
                search=search_var.get().strip(),
                from_dt=from_date,
                to_dt=to_date
            )

            btn_apply.config(text="Clear", bg="#dc2626")
            date_filter_active = True

        else:
            load_taxes(search=search_var.get().strip())
            btn_apply.config(text="🔍 Apply", bg="#192987")
            date_filter_active = False



    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)


    # ---------------- SEARCH BIND ----------------
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_taxes(search=search_var.get().strip())
    )

    # ---------------- INITIAL LOAD ----------------
    load_taxes()



def open_add_tax_window(workspace, shop_id, tax_id=None):

    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date
    current_tax_id = tk.IntVar(value=0)
    mode = tk.StringVar(value="ADD")



    if tax_id:
        current_tax_id.set(tax_id)




    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------

    # ================= BASE CONTENT FRAME =================
    if not hasattr(workspace, "content"):
        workspace.content = tk.Frame(workspace, bg="white")
        workspace.content.place(relx=0, rely=0, relwidth=1, relheight=1)

    workspace.update_idletasks()  # 🔑 IMPORTANT

    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )

    # 🔥 OPEN MAXIMIZED BY DEFAULT
    win.place(
        relx=0.5,
        rely=0.5,
        anchor="center",
        width=workspace.winfo_width() - 40,
        height=workspace.winfo_height() - 40
    )

    is_maximized = True   # 🔥 DEFAULT TRUE
    mode = tk.StringVar(value="ADD")
    current_staff_id = tk.IntVar(value=0)

    if tax_id:
        mode.set("UPDATE")

    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white")
    title_bar.pack(fill="x", pady=(4, 0), padx=6)

    def close_window():
        win.destroy()
        open_taxes_page(workspace, shop_id)

    def toggle_zoom():
        nonlocal is_maximized

        if is_maximized:
            # 🔽 RESTORE (NORMAL SIZE)
            win.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
                width=650,
                height=580
            )
            is_maximized = False
        else:
            # 🔼 MAXIMIZE
            win.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
                width=workspace.winfo_width() - 40,
                height=workspace.winfo_height() - 40
            )
            is_maximized = True

    # ---------------- TITLE BAR BUTTONS ----------------
    tk.Button(
        title_bar,
        text="✖",
        width=3,
        bd=0,
        bg="black",
        fg="red",
        command=close_window
    ).pack(side="right")

    tk.Button(
        title_bar,
        text="⛶",
        width=3,
        bd=0,
        bg="black",
        fg="white",
        command=toggle_zoom
    ).pack(side="right")


    # ---------------- TOP MODE BUTTONS ----------------
    top_bar = tk.Frame(win, bg="white")
    top_bar.pack(fill="x", pady=(8, 6))

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Tax")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Tax")
            clear_tax_form()
            current_tax_id.set(0)

        else:
            header_lbl.config(text="Update Tax")
            search_row.pack(after=header_lbl, fill="x", pady=(6, 10))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Tax")

    add_btn = tk.Button(
        top_bar, text="Add Tax",
        bg=SELECTED_COLOR, fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left", padx=6)

    upd_btn = tk.Button(
        top_bar, text="Update Tax",
        bg=NORMAL_COLOR, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14, pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=6)

   
    # ---------------- SEARCH ----------------
    # ================= SEARCH ROW =================
    search_var = tk.StringVar()

    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", pady=(6, 8))

    tk.Label(
        search_row,
        text="Search:",
        bg="white",
        fg="black",
        font=("Segoe UI", 9),
        width=18,
        anchor="w"
    ).pack(side="left", padx=(14, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")


    # ================= HEADER =================
    header_lbl = tk.Label(
        win,
        text="Add Income",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))


    # ================= FORM CARD =================
    card = tk.Frame(win, bg="white")

    # 🔥 IMPORTANT: expand=False + anchor="n"
    card.pack(
        fill="x",
        expand=False,
        padx=30,
        pady=(10, 10),     # 👈 top-la move
        anchor="n"
    )

   # ================= FORM CARD =================
    # ================= FORM CARD =================
    card = tk.Frame(win, bg="white")
    card.pack(fill="x", expand=False, padx=30, pady=(10, 10), anchor="n")

    # Grid config
    card.columnconfigure(0, weight=1, uniform="a")
    card.columnconfigure(1, weight=1, uniform="a")

    FIELD_WIDTH = 38


    # ================= IEEE FIELD =================
    def ieee_field(parent, label, row, col, var=None):
        if var is None:
            var = tk.StringVar()

        box = tk.Frame(parent, bg="white")
        box.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        tk.Entry(
            box,
            textvariable=var,
            width=FIELD_WIDTH,
            bg="white",
            fg="black",
            relief="solid",
            bd=1
        ).pack(fill="x", pady=2)

        return var


    def ieee_dropdown(parent, label, row, col, var, values):
        box = tk.Frame(parent, bg="white")
        box.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        opt = tk.OptionMenu(box, var, *values)
        opt.config(bg="white", fg="black", relief="solid", bd=1)
        opt.pack(fill="x", pady=2)


    # ================= ROW 0 =================
    tax_name = tk.StringVar(value="GST")

    ieee_dropdown(
        card, "Tax Name", 0, 0,
        tax_name,
        [
            "GST",
            "CGST",
            "SGST",
            "IGST",
            "Service Tax",
            "Cess",
            "Other"
        ]
    )

    tax_code = ieee_field(card, "Tax Code", 0, 1)

    # ================= ROW 1 =================
    tax_rate = ieee_field(card, "Tax Rate (%)", 1, 0)

    tax_type = tk.StringVar(value="Percentage")

    ieee_dropdown(
        card, "Tax Type", 1, 1,
        tax_type,
        [
            "Percentage",   # GST, CGST, SGST
            "Fixed"         # Cess, Penalty, Fee
        ]
    )


    # ================= ROW 2 =================
    applied_on = tk.StringVar(value="Income")
    ieee_dropdown(
        card, "Applied On", 2, 0,
        applied_on,
        ["Income", "Expense", "Both"]
    )

    is_compound = tk.StringVar(value="No")
    ieee_dropdown(
        card, "Compound Tax?", 2, 1,
        is_compound,
        ["No", "Yes"]
    )

    # ================= ROW 3 =================
    status = tk.StringVar(value="Active")
    ieee_dropdown(
        card, "Status", 3, 0,
        status,
        ["Active", "Inactive"]
    )

    remarks = ieee_field(card, "Remarks", 3, 1)



    # ================= FORM HELPERS =================
    # ================= FORM HELPERS =================
    def clear_tax_form():
        tax_name.set("")
        tax_code.set("")
        tax_rate.set("")

        tax_type.set("Percentage")
        applied_on.set("Income")
        is_compound.set("No")
        status.set("Active")

        remarks.set("")


    def clear_taxes_form():
        current_tax_id.set(0)
        clear_tax_fields_only()

        mode.set("ADD")
        update_mode_ui()


    def clear_tax_fields_only():
        tax_name.set("")
        tax_code.set("")
        tax_rate.set("")

        tax_type.set("Percentage")
        applied_on.set("Income")
        is_compound.set("No")
        status.set("Active")

        remarks.set("")

        # 🔴 IMPORTANT: DO NOT TOUCH
        # current_tax_id
        # mode
    # ---------------- SEARCH TAX ----------------
    def search_tax(*_):
        text = search_var.get().strip()

        # 🔥 SEARCH CLEARED → ONLY CLEAR FIELDS (STAY IN SAME MODE)
        if not text:
            clear_tax_fields_only()
            update_mode_ui()
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM tax_master
            WHERE
                tax_name LIKE %s
                OR tax_code LIKE %s
                OR tax_type LIKE %s
                OR applied_on LIKE %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (
            f"%{text}%",
            f"%{text}%",
            f"%{text}%",
            f"%{text}%"
        ))

        row = cur.fetchone()
        conn.close()

        if not row:
            clear_tax_fields_only()
            return

        # ---------------- LOAD DATA INTO TAX FORM ----------------
        current_tax_id.set(row["tax_id"])

        tax_name.set(row["tax_name"] or "")
        tax_code.set(row["tax_code"] or "")
        tax_rate.set(str(row["tax_rate"] or ""))

        tax_type.set(row["tax_type"] or "Percentage")
        applied_on.set(row["applied_on"] or "Income")

        is_compound.set("Yes" if row["is_compound"] else "No")
        status.set(row["status"] or "Active")

        remarks.set(row["remarks"] or "")

        mode.set("UPDATE")
        update_mode_ui()


    search_entry.bind("<KeyRelease>", search_tax)






   # ---------------- SAVE TAX ----------------
    def save_tax():
        # ---------------- VALIDATION ----------------
        if not tax_name.get() or not tax_rate.get():
            messagebox.showwarning(
                "Missing",
                "Tax Name & Tax Rate are required"
            )
            return

        conn = get_db()
        cur = conn.cursor()

        try:
            # -------- UPDATE TAX --------
            if mode.get() == "UPDATE" and current_tax_id.get() != 0:
                cur.execute("""
                    UPDATE tax_master SET
                        tax_name=%s,
                        tax_code=%s,
                        tax_type=%s,
                        tax_rate=%s,
                        applied_on=%s,
                        is_compound=%s,
                        status=%s,
                        remarks=%s
                    WHERE tax_id=%s
                """, (
                    tax_name.get(),
                    tax_code.get() or None,
                    tax_type.get(),
                    float(tax_rate.get()),
                    applied_on.get(),
                    1 if is_compound.get() == "Yes" else 0,
                    status.get(),
                    remarks.get() or None,
                    current_tax_id.get()
                ))

                messagebox.showinfo(
                    "Success",
                    "✅ Tax updated successfully"
                )

            # -------- INSERT TAX --------
            else:
                cur.execute("""
                    INSERT INTO tax_master
                    (tax_name, tax_code, tax_type,
                    tax_rate, applied_on, is_compound,
                    status, remarks)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    tax_name.get(),
                    tax_code.get() or None,
                    tax_type.get(),
                    float(tax_rate.get()),
                    applied_on.get(),
                    1 if is_compound.get() == "Yes" else 0,
                    status.get(),
                    remarks.get() or None
                ))

                messagebox.showinfo(
                    "Success",
                    "✅ Tax added successfully"
                )

            conn.commit()

            # ---------------- RESET ----------------
            clear_tax_form()
            current_tax_id.set(0)
            mode.set("ADD")
            update_mode_ui()

            # 🔥 OPTIONAL: refresh table
            # load_taxes()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()


    # ---------------- SAVE BUTTON ----------------
    save_btn = tk.Button(
        win,
        text="💾 Save Tax",
        bg=SELECTED_COLOR,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=18,
        pady=6,
        command=save_tax
    )
    save_btn.pack(pady=10)

    update_mode_ui()
    win.bind("<Return>", lambda e: save_tax())

# -------------------------------------------------------------------------------------------------------------------------------------

def open_categories_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    search_active = False
    last_search_keyword = ""

    def set_search_active(val):
        nonlocal search_active
        search_active = val

    def set_last_keyword(val):
        nonlocal last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Tax Details",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")

            # Income row full text
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # reset zebra
        restore_zebra()

        # apply highlight
        tree.after_idle(apply_search_highlight)



    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)

    search_entry.focus_set()


    date_filter_active = False

   
   # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = (
        "sno",
        "category_name",
        "product_count",
        "show",
        "id"          # 🔒 hidden category_id
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    headers = [
        "S.No",
        "Category Name",
        "Product Count",
        "Show"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)


    # ---------------- TAG COLORS ----------------
    tree.tag_configure("even", background="#7BACDD")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("active", background="#BBF7D0")
    tree.tag_configure("inactive", background="#FECACA")

    # ---------------- HEADERS ----------------
    # ---------------- COLUMN SETTINGS ----------------
    tree.column("sno", width=60, anchor="center")
    tree.column("category_name", width=220, anchor="w")

    tree.column("product_count", width=120, anchor="center")
    tree.column("show", width=80, anchor="center")

    tree.column("id", width=0, stretch=False)   # 🔒 hidden

    # ---------------- SCROLLBARS ----------------
    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    


    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
   

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)


   # =================================================
    # LOAD CATEGORIES (SINGLE FUNCTION)
    # =================================================
    def load_categories(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                c.category_name,
                COUNT(p.product_id) AS product_count,
                c.status,
                c.created_at,
                c.updated_at,
                c.category_id
            FROM categories c
            LEFT JOIN products p
                ON p.category_id = c.category_id
                AND p.shop_id = %s
            WHERE 1=1
        """

        params = [shop_id]

        # 🔍 SEARCH FILTER
        if search:
            query += """
                AND (
                    c.category_name LIKE %s OR
                    c.status LIKE %s
                )
            """
            s = f"%{search}%"
            params.extend([s, s])

        # 📅 DATE FILTER
        if from_dt and to_dt:
            query += " AND DATE(c.created_at) BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += """
            GROUP BY c.category_id
            ORDER BY c.category_name
        """

        cur.execute(query, tuple(params))

        for i, r in enumerate(cur.fetchall()):
            tag = "even" if i % 2 == 0 else "odd"

            if r[2] == "Active":
                tag = "active"
            else:
                tag = "inactive"

            tree.insert(
                "",
                "end",
                values=(
                    i + 1,                           # S.No
                    r[0],                            # Category Name
                    r[1],                            # Product Count
                    "Show",                          # Show button
                    r[5]                             # 🔒 category_id
                ),
                tags=(tag,)
            )

        conn.close()

     


    def on_category_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # SHOW column = #4
        if col_id == "#4":
            values = tree.item(row_id, "values")

            category_name = values[1]
            category_id = values[4]

            open_category_products_page(
                workspace,
                shop_id,
                category_id,
                category_name
            )

    tree.bind("<Button-1>", on_category_tree_click)



   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

    tree.tag_configure("even", background="#FFF701")
    tree.tag_configure("odd", background="#B8B8B8")




    # ---------------- SEARCH BIND ----------------
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_categories(search=search_var.get().strip())
    )


    # ---------------- INITIAL LOAD ----------------
    load_categories()

def open_category_products_page(workspace, shop_id, category_id, category_name):


    import tkinter as tk
    from tkinter import ttk, messagebox
    import mysql.connector
    all_products = []

    # ---------------- CLEAR ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="#F8FAFC")

    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TOP BAR ----------------
    top = tk.Frame(main, bg="white")
    top.pack(fill="x", padx=15, pady=10)

    tk.Label(
        top,
        text=f"Products in Category : {category_name}",
        font=("Segoe UI", 16, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(side="left")

    tk.Button(
        top,
        text="✖",
        font=("Segoe UI", 14, "bold"),
        fg="red",
        bg="white",
        relief="flat",
        command=lambda: open_categories_page(workspace, shop_id)
    ).pack(side="right")

    
    # ================= SEARCH BAR =================
    search_frame = tk.Frame(main, bg="white")
    search_frame.pack(fill="x", padx=15, pady=(0, 8))

    tk.Label(
        search_frame,
        text="Search Product",
        bg="white",
        fg="black",
        font=("Segoe UI", 10, "bold")
    ).pack(side="left")

    product_search_var = tk.StringVar()

    product_search_entry = tk.Entry(
        search_frame,
        textvariable=product_search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1,
        font=("Segoe UI", 10)
    )
    product_search_entry.pack(side="left", padx=8)
    product_search_entry.focus_set()

    
    def live_filter(*args):
        keyword = product_search_var.get().strip().lower()

        # 🔁 CLEAR SEARCH → NORMAL TABLE
        if keyword == "":
            render_table(all_products)
            return

        filtered = []

        for row in all_products:
            text = " ".join(str(col).lower() for col in row)
            if keyword in text:
                filtered.append(row)

        # 🔥 FILTERED RESULTS TOP-LA
        render_table(filtered)

        # 🔥 highlight first match
        children = tree.get_children()
        if children:
            tree.item(children[0], tags=("match",))
            tree.see(children[0])


    product_search_var.trace_add("write", live_filter)


    # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = (
        "sno",
        "product_id",
        "product_name",
        "barcode1",
        "barcode2",
        "stock",
        "move",
        "delete"
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=15
    )
    # ---------------- TREE TAGS (AFTER TREE CREATED) ----------------
    tree.tag_configure("match", background="#BBF7D0")   # green highlight
    tree.tag_configure("normal", background="white")


    headers = [
        "S.No",
        "Product ID",
        "Product Name",
        "Barcode 1",
        "Barcode 2",
        "Stock",
        "Move",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    tree.column("sno", width=60, anchor="center")
    tree.column("product_id", width=90, anchor="center")
    tree.column("product_name", width=220)
    tree.column("barcode1", width=130)
    tree.column("barcode2", width=130)
    tree.column("stock", width=80, anchor="center")
    tree.column("move", width=80, anchor="center")
    tree.column("delete", width=80, anchor="center")

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)


    def render_table(rows):
        tree.delete(*tree.get_children())

        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))
    tree.tag_configure("even", background="#93FF87")   # light
    tree.tag_configure("odd", background="#FFFFFF")    # grey
    tree.tag_configure("match", background="#7B7DFB")  # green



    # ---------------- LOAD PRODUCTS ----------------
    
    def load_products():
        all_products.clear()
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                product_id,
                product_name,
                barcode1,
                barcode2,
                stock
            FROM products
            WHERE category_id=%s AND shop_id=%s
            ORDER BY product_name
        """, (category_id, shop_id))

        for i, r in enumerate(cur.fetchall()):
            row = (
                i + 1,        # S.No
                r[0],         # product_id
                r[1],         # product_name
                r[2] or "",
                r[3] or "",
                r[4],
                "Move",
                "🗑"
            )
            all_products.append(row)

        conn.close()
        render_table(all_products)




    def center_popup(win, parent):
        win.update_idletasks()

        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        ww = win.winfo_width()
        wh = win.winfo_height()

        x = px + (pw // 2) - (ww // 2)
        y = py + (ph // 2) - (wh // 2)

        win.geometry(f"+{x}+{y}")


    def move_product(product_id):
        popup = tk.Toplevel(main)
        popup.geometry("320x190")
        popup.overrideredirect(True)          # 🔥 remove OS title bar
        popup.transient(main)
        popup.resizable(False, False)

        popup.update_idletasks()
        popup.deiconify()

        center_popup(popup, main)   # ✅ CENTER OF WORKSPACE

        popup.grab_set()


        # ================= HEADER =================
        header = tk.Frame(popup, bg="#111827", height=36)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Move Product",
            bg="#111827",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=10)

        close_btn = tk.Button(
            header,
            text="✖",
            font=("Segoe UI", 10, "bold"),
            fg="red",
            bg="#111827",
            bd=0,
            cursor="hand2",
            activebackground="#111827",
            command=popup.destroy
        )
        close_btn.pack(side="right", padx=8)

        # ================= BODY =================
        body = tk.Frame(popup, bg="white")
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Select Category",
            bg="white",
            fg="#0F172A",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(18, 6))

        categories = [
            "All", "Bathing", "Biscuits", "Child Items", "Chocolates",
            "Cool Drinks", "Detergents", "Fairness", "General",
            "Masalas", "Medicals", "Milk Mixers", "Mosquito Coils",
            "Napkins", "Oils", "Perfumes", "Rice & Dhalls",
            "Salt", "School Needs", "Semeya", "Snacks",
            "Swamy Items", "Tooth Paste / Brush", "Vegetables"
        ]

        cat_var = tk.StringVar()

        combo = ttk.Combobox(
            body,
            textvariable=cat_var,
            values=categories,
            state="readonly",
            width=26
        )
        combo.pack(pady=4)
        combo.focus_set()

        def confirm_move():
            selected_category = cat_var.get()
            if not selected_category:
                messagebox.showwarning("Warning", "Select category")
                return

            conn = get_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT category_id
                FROM categories
                WHERE category_name=%s
                LIMIT 1
            """, (selected_category,))
            row = cur.fetchone()

            if not row:
                conn.close()
                messagebox.showerror("Error", "Category not found")
                return

            cur.execute("""
                UPDATE products
                SET category_id=%s
                WHERE product_id=%s AND shop_id=%s
            """, (row[0], product_id, shop_id))

            conn.commit()
            conn.close()

            popup.destroy()
            load_products()

        tk.Button(
            body,
            text="Save",
            bg="#0EA5E9",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=14,
            relief="flat",
            command=confirm_move
        ).pack(pady=16)



    # ---------------- DELETE PRODUCT ----------------
    def delete_product(product_id):
        if not messagebox.askyesno("Confirm", "Delete this product permanently?"):
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM products WHERE product_id=%s AND shop_id=%s",
            (product_id, shop_id)
        )
        conn.commit()
        conn.close()

        load_products()

    # ---------------- CLICK HANDLER ----------------
    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if not row_id:
            return

        values = tree.item(row_id, "values")
        product_id = values[1]

        if col == "#7":      # Move
            move_product(product_id)

        elif col == "#8":    # Delete
            delete_product(product_id)

    tree.bind("<Button-1>", on_tree_click)

    load_products()

# -----------------------------------------------------------------------------------------------------------------------------------------
def open_purchase_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    last_search_keyword = ""
    search_active = False

    def set_search_active(val):
        global search_active
        search_active = val

    def set_last_keyword(val):
        global last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Tax Details",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        # 🔥 Search cleared → full reset
        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # 🔥 Reset non-matching rows only
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        # 🔥 Apply permanent highlight
        tree.after_idle(apply_search_highlight)




    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)


    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    box_add = fixed_box(action_row, 140, 30)

    btn_add_expense = tk.Button(
        box_add,
        text="➕ Add purchase",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=lambda: open_add_purchase_window(workspace, shop_id, purchase_id=None)
    )

    btn_add_expense.pack(fill="both", expand=True)


    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)
    tk.Label(box_from, text="From", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")

    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)
    tk.Label(box_to, text="To", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")

    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

   
    # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    # ---------------- COLUMNS ----------------
    columns = (
        "company_name",
        "purchase_date",
        "invoice_no",
        "supplier_id",
        "bill_type",
        "sub_total",
        "tax_amount",
        "discount",
        "grand_total",
        "paid_amount",
        "balance_amount",
        "payment_status",
        "payment_mode",
        "created_at",
        "updated_at",
        "delete",     # 🗑 DELETE
        "id"          # 🔒 HIDDEN purchase_id
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    # ---------------- TAG COLORS ----------------
    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("match", background="#FFE08A")  # 🔥 permanent highlight
    # permanent yellow
    # yellow

    # ---------------- HEADERS ----------------
    headers = [
        "Company",
        "Purchase Date",
        "Invoice No",
        "Supplier ID",
        "Bill Type",
        "Sub Total",
        "Tax Amount",
        "Discount",
        "Grand Total",
        "Paid Amount",
        "Balance",
        "Status",
        "Payment Mode",
        "Created At",
        "Updated At",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    # ---------------- COLUMN SETTINGS ----------------
    tree.column("company_name", width=140, anchor="w")
    tree.column("purchase_date", width=140, anchor="center")
    tree.column("invoice_no", width=130, anchor="center")

    tree.column("supplier_id", width=120, anchor="center")
    tree.column("bill_type", width=90, anchor="center")

    tree.column("sub_total", width=130, anchor="e")
    tree.column("tax_amount", width=130, anchor="e")
    tree.column("discount", width=100, anchor="e")
    tree.column("grand_total", width=130, anchor="e")

    tree.column("paid_amount", width=130, anchor="e")
    tree.column("balance_amount", width=150, anchor="e")

    tree.column("payment_status", width=120, anchor="center")
    tree.column("payment_mode", width=140, anchor="center")

    tree.column("created_at", width=150, anchor="center")
    tree.column("updated_at", width=150, anchor="center")

    tree.column("delete", width=70, anchor="center")
    tree.column("id", width=0, stretch=False)   # 🔒 hidden

    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    #  # =================================================
    # # TOTAL SUMMARY BAR (BELOW TABLE)
    # # =================================================
    # summary_bar = tk.Frame(main, bg="#F1F5F9", height=40)
    # summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    # summary_bar.pack_propagate(False)

    # lbl_total = tk.Label(
    #     summary_bar,
    #     text="Total : ₹0",
    #     bg="#F1F5F9",
    #     fg="black",
    #     font=("Segoe UI", 10, "bold")
    # )
    # lbl_total.pack(side="left", padx=20)

    # lbl_cash = tk.Label(
    #     summary_bar,
    #     text="Cash : ₹0",
    #     bg="#F1F5F9",
    #     fg="#16A34A",
    #     font=("Segoe UI", 10, "bold")
    # )
    # lbl_cash.pack(side="left", padx=20)

    # lbl_credit = tk.Label(
    #     summary_bar,
    #     text="Credit : ₹0",
    #     bg="#F1F5F9",
    #     fg="#DC2626",
    #     font=("Segoe UI", 10, "bold")
    # )
    # lbl_credit.pack(side="left", padx=20)                        *Important*
                          
    # def update_bank_totals():
    #     total = 0
    #     cash_total = 0
    #     other_total = 0

    #     for item in tree.get_children():
    #         values = tree.item(item, "values")

    #         # safety
    #         if len(values) < 9:
    #             continue

    #         # ✅ CURRENT BALANCE (index 6)
    #         bal_str = str(values[6]).replace("₹", "").replace(",", "").strip()
    #         try:
    #             bal = float(bal_str)
    #         except:
    #             bal = 0

    #         # ✅ BANK TYPE (index 4)
    #         bank_type = str(values[4]).lower().strip()

    #         total += bal

    #         if bank_type == "cash":
    #             cash_total += bal
    #         else:
    #             other_total += bal

    #     lbl_total.config(text=f"Total Tax : ₹{total:,.0f}")
    #     lbl_cash.config(text=f"Cash : ₹{cash_total:,.0f}")
    #     lbl_credit.config(text=f"Other : ₹{other_total:,.0f}")



    # update_bank_totals()


    # =================================================
    # LOAD EXPENSES (SINGLE FUNCTION)
    # =================================================
    def load_purchases(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                company_name,
                purchase_date,
                invoice_no,
                supplier_id,
                bill_type,
                sub_total,
                tax_amount,
                discount,
                grand_total,
                paid_amount,
                balance_amount,
                payment_status,
                payment_mode,
                created_at,
                updated_at,
                id
            FROM purchases
            WHERE 1=1
        """

        params = []

        # 🔍 SEARCH FILTER
        if search:
            query += """
                AND (
                    company_name LIKE %s OR
                    invoice_no LIKE %s OR
                    bill_type LIKE %s OR
                    payment_status LIKE %s OR
                    payment_mode LIKE %s
                )
            """
            s = f"%{search}%"
            params.extend([s, s, s, s, s])

        # 📅 DATE FILTER (purchase_date)
        if from_dt and to_dt:
            query += " AND DATE(purchase_date) BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += " ORDER BY purchase_date DESC"

        cur.execute(query, tuple(params))

        for i, r in enumerate(cur.fetchall()):
            tag = "even" if i % 2 == 0 else "odd"

            # 🎨 STATUS COLOR
            if r[11] == "Paid":
                tag = "paid"
            elif r[11] == "Partial":
                tag = "partial"
            else:
                tag = "pending"

            tree.insert(
                "",
                "end",
                values=(
                    r[0],                               # company_name
                    r[1].strftime("%d-%m-%Y"),          # purchase_date
                    r[2],                               # invoice_no
                    r[3],                               # supplier_id
                    r[4],                               # bill_type
                    f"{r[5]:.2f}",                      # sub_total
                    f"{r[6]:.2f}",                      # tax_amount
                    f"{r[7]:.2f}",                      # discount
                    f"{r[8]:.2f}",                      # grand_total
                    f"{r[9]:.2f}",                      # paid_amount
                    f"{r[10]:.2f}",                     # balance_amount
                    r[11],                              # payment_status
                    r[12],                              # payment_mode
                    r[13].strftime("%d-%m-%Y %H:%M"),   # created_at
                    r[14].strftime("%d-%m-%Y %H:%M"),   # updated_at
                    "🗑",                               # delete icon
                    r[15]                               # 🔒 purchase_id
                ),
                tags=(tag,)
            )

        conn.close()


    def delete_purchase(purchase_id):
        if not messagebox.askyesno("Confirm", "Delete this purchase?"):
            return

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM purchases WHERE id = %s",
            (purchase_id,)
        )

        conn.commit()
        conn.close()

        load_purchases()


      


    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 🗑 DELETE column (last visible column)
        # Purchase Treeview columns index:
        # delete = 16 → column number = #16
        if col_id == "#16":
            values = tree.item(row_id, "values")

            # safety check
            if len(values) < 17:
                return

            purchase_id = values[16]   # 🔒 hidden purchase_id
            delete_purchase(purchase_id)



    tree.bind("<Button-1>", on_tree_click)
    load_purchases()


   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            if search_active:
                tags = tree.item(item, "tags")
                if "match" in tags:
                    continue   # 🔥 keep highlight permanent

            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


   
    edit_entry = None
    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        # ❌ Delete column (#16) & hidden ID (#17) editable illa
        if not row_id or col in ("#16", "#17"):
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)

        edit_entry.insert(0, value)
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            # 🔥 NUMERIC COLUMNS FORMAT
            if col in ("#6", "#7", "#8", "#9", "#10", "#11"):
                try:
                    new_val = f"{float(new_val):.2f}"
                except:
                    new_val = "0.00"

            tree.set(row_id, col, new_val)

            update_purchase_db(row_id, col, new_val)
            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())


    tree.bind("<Double-1>", on_double_click)


    purchase_col_map = {
        "#1": "company_name",
        "#2": "purchase_date",
        "#3": "invoice_no",
        "#4": "supplier_id",
        "#5": "bill_type",
        "#6": "sub_total",
        "#7": "tax_amount",
        "#8": "discount",
        "#9": "grand_total",
        "#10": "paid_amount",
        "#11": "balance_amount",
        "#12": "payment_status",
        "#13": "payment_mode"
    }




    def clean_numeric(val):
        return val.replace("%", "").strip()


    # ---------------- UPDATE DB ----------------
    def update_purchase_db(row_id, col, value):
        db_col = purchase_col_map.get(col)
        if not db_col:
            return

        purchase_id = tree.item(row_id)["values"][-1]   # 🔒 hidden purchase_id

        # 🔥 ENUM FIXES
        if db_col == "bill_type":
            value = "Credit" if value.lower().startswith("c") else "Cash"

        elif db_col == "payment_status":
            val = value.lower()
            if val.startswith("p") and "art" in val:
                value = "Partial"
            elif val.startswith("p"):
                value = "Paid"
            else:
                value = "Pending"

        elif db_col == "payment_mode":
            val = value.lower()
            if val.startswith("u"):
                value = "UPI"
            elif val.startswith("b"):
                value = "Bank"
            else:
                value = "Cash"

        # 🔥 NUMERIC SAFETY
        elif db_col in (
            "sub_total",
            "tax_amount",
            "discount",
            "grand_total",
            "paid_amount",
            "balance_amount"
        ):
            try:
                value = float(value)
            except:
                value = 0.00

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE purchases
            SET {db_col}=%s
            WHERE id=%s
            """,
            (value, purchase_id)
        )

        conn.commit()
        conn.close()


    # ---------------- APPLY / CLEAR LOGIC ----------------
    date_filter_active = False

    def toggle_date_filter():
        nonlocal date_filter_active

        if not date_filter_active:
            from_date = start_date.get_date()
            to_date   = end_date.get_date()

            load_purchases(
                search=search_var.get().strip(),
                from_dt=from_date,
                to_dt=to_date
            )

            btn_apply.config(text="Clear", bg="#dc2626")
            date_filter_active = True

        else:
            load_purchases(search=search_var.get().strip())
            btn_apply.config(text="🔍 Apply", bg="#192987")
            date_filter_active = False



    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)

    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_purchases(search=search_var.get().strip())
    )


    # ---------------- INITIAL LOAD ----------------
    load_purchases()




def open_add_purchase_window(workspace, shop_id, purchase_id=None):

    import tkinter as tk
    from tkinter import messagebox
    import mysql.connector
    from datetime import date
    # ================= FORM VARIABLES =================
    current_purchase_id = tk.IntVar(value=0)
    mode = tk.StringVar(value="ADD")



    if purchase_id:
        current_purchase_id.set(purchase_id)




    # ---------------- COLORS ----------------
    ERROR = "#dc2626"
    SELECTED_COLOR = "#2563eb"
    NORMAL_COLOR = "#E5E7EB"
    TEXT_COLOR = "#0F172A"

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg="white")

    # ---------------- MAIN WINDOW ----------------

    # ================= BASE CONTENT FRAME =================
    if not hasattr(workspace, "content"):
        workspace.content = tk.Frame(workspace, bg="white")
        workspace.content.place(relx=0, rely=0, relwidth=1, relheight=1)

    workspace.update_idletasks()  # 🔑 IMPORTANT

    win = tk.Frame(
        workspace,
        bg="white",
        highlightbackground=SELECTED_COLOR,
        highlightthickness=2
    )

    # 🔥 OPEN MAXIMIZED BY DEFAULT
    win.place(
        relx=0.5,
        rely=0.5,
        anchor="center",
        width=workspace.winfo_width() - 40,
        height=workspace.winfo_height() - 40
    )

    
    is_maximized = True   # 🔥 DEFAULT TRUE
    mode = tk.StringVar(value="ADD")
    current_staff_id = tk.IntVar(value=0)

    if purchase_id:
        mode.set("UPDATE")

    # ---------------- TITLE BAR ----------------
    # ---------------- TITLE BAR ----------------
    title_bar = tk.Frame(win, bg="white", height=28)
    title_bar.pack(fill="x", padx=0, pady=0)

    def close_window():
        win.destroy()
        open_purchase_page(workspace,shop_id)

    def toggle_zoom():
        nonlocal is_maximized
        if is_maximized:
            win.place(relx=0.5, rely=0.5, anchor="center", width=650, height=580)
            is_maximized = False
        else:
            win.place(
                relx=0.5, rely=0.5, anchor="center",
                width=workspace.winfo_width() - 40,
                height=workspace.winfo_height() - 40
            )
            is_maximized = True

    tk.Button(
        title_bar, text="✖", width=3, bd=0,
        bg="black", fg="red", command=close_window
    ).pack(side="right")

    tk.Button(
        title_bar, text="⛶", width=3, bd=0,
        bg="black", fg="white", command=toggle_zoom
    ).pack(side="right")


    # ---------------- TOP MODE BUTTONS (🔥 REAL TOP BORDER FIX) ----------------
    top_bar = tk.Frame(win, bg="white")

    # 🔥 ABSOLUTE POSITION → BORDER-KU OTTI
    top_bar.place(
        x=6,     # 🔥 left border distance
        y=2      # 🔥 top border distance (VERY IMPORTANT)
    )

    

    def update_mode_ui():
        if mode.get() == "ADD":
            header_lbl.config(text="Add Tax")
            search_row.pack_forget()
            add_btn.config(bg=SELECTED_COLOR, fg="white")
            upd_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Save Tax")
            clear_purchase_form()
            current_purchase_id.set(0)
        else:
            header_lbl.config(text="Update Tax")
            search_row.pack(after=header_lbl, fill="x", pady=(4, 8))
            upd_btn.config(bg=SELECTED_COLOR, fg="white")
            add_btn.config(bg=NORMAL_COLOR, fg=TEXT_COLOR)
            save_btn.config(text="💾 Update Tax")

    add_btn = tk.Button(
        top_bar,
        text="Add Tax",
        bg=SELECTED_COLOR,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=14,
        pady=4,
        command=lambda: [mode.set("ADD"), update_mode_ui()]
    )
    add_btn.pack(side="left")

    upd_btn = tk.Button(
        top_bar,
        text="Update Tax",
        bg=NORMAL_COLOR,
        fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        padx=14,
        pady=4,
        command=lambda: [mode.set("UPDATE"), update_mode_ui()]
    )
    upd_btn.pack(side="left", padx=(6, 0))


    # ---------------- SEARCH ROW ----------------
    search_var = tk.StringVar()
    search_row = tk.Frame(win, bg="white")
    search_row.pack(fill="x", padx=6, pady=(4, 8))

    tk.Label(
        search_row,
        text="Search:",
        bg="white",
        fg="black",
        font=("Segoe UI", 9),
        width=18,
        anchor="w"
    ).pack(side="left", padx=(8, 6))

    search_entry = tk.Entry(
        search_row,
        textvariable=search_var,
        width=30,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left")



    # ================= HEADER =================
    header_lbl = tk.Label(
        win,
        text="Add Income",
        font=("Segoe UI", 14, "bold"),
        fg="black",
        bg="white"
    )
    header_lbl.pack(pady=(6, 10))


    # ================= FORM CARD =================
    # ================= FORM CARD =================
    card = tk.Frame(win, bg="white")
    card.pack(
        fill="both",
        expand=True,      # form takes remaining space
        padx=30,
        pady=(10, 5),
        anchor="n"
    )

    # Grid config (2 columns)
    card.columnconfigure(0, weight=1, uniform="a")
    card.columnconfigure(1, weight=1, uniform="a")

    for r in range(8):
        card.rowconfigure(r, weight=0)   # fields height fixed

    FIELD_WIDTH = 42

    # ================= ACTION BAR =================
    action_bar = tk.Frame(win, bg="white")
    action_bar.pack(
        fill="x",
        expand=False,
        padx=30,
        pady=(5, 1),
        anchor="s"
    )


    # ================= IEEE FIELD =================
    def ieee_field(parent, label, row, col, var=None):
        if var is None:
            var = tk.StringVar()

        box = tk.Frame(parent, bg="white")
        box.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        tk.Entry(
            box,
            textvariable=var,
            width=FIELD_WIDTH,
            bg="white",
            fg="black",
            relief="solid",
            bd=1
        ).pack(fill="x", pady=2)

        return var


    def ieee_dropdown(parent, label, row, col, var, values):
        box = tk.Frame(parent, bg="white")
        box.grid(row=row, column=col, sticky="ew", padx=12, pady=4)

        tk.Label(
            box,
            text=label,
            bg="white",
            fg="black",
            font=("Segoe UI", 9),
            anchor="w"
        ).pack(anchor="w")

        opt = tk.OptionMenu(box, var, *values)
        opt.config(bg="white", fg="black", relief="solid", bd=1)
        opt.pack(fill="x", pady=2)


   # ================= ROW 0 =================
    company_name = ieee_field(card, "Company Name", 0, 0)
    invoice_no   = ieee_field(card, "Invoice No", 1, 0)

    # ================= ROW 1 =================
    purchase_date = ieee_field(card, "Purchase Date (YYYY-MM-DD)", 2, 0)
    supplier_id   = ieee_field(card, "Supplier ID", 3, 0)

    # ================= ROW 2 =================
    bill_type = tk.StringVar(value="Cash")
    ieee_dropdown(card, "Bill Type", 4, 0, bill_type, ["Cash", "Credit"])

    payment_mode = tk.StringVar(value="Cash")
    ieee_dropdown(card, "Payment Mode", 5, 0, payment_mode, ["Cash", "UPI", "Bank"])

    # ================= ROW 3 =================
    sub_total  = ieee_field(card, "Sub Total", 0, 1)
    tax_amount = ieee_field(card, "Tax Amount", 1, 1)

    # ================= ROW 4 =================
    discount    = ieee_field(card, "Discount", 6, 0)
    grand_total = ieee_field(card, "Grand Total", 2, 1)

    # ================= ROW 5 =================
    paid_amount    = ieee_field(card, "Paid Amount", 4, 1)
    balance_amount = ieee_field(card, "Balance Amount", 5, 1)

    # ================= ROW 6 =================
    payment_status = tk.StringVar(value="Paid")
    ieee_dropdown(card, "Payment Status", 3, 1, payment_status,
                ["Paid", "Partial", "Pending"])





   
    # ================= FORM HELPERS =================
    def clear_purchase_fields_only():
        company_name.set("")
        invoice_no.set("")
        purchase_date.set("")
        supplier_id.set("")

        bill_type.set("Cash")
        payment_mode.set("Cash")

        sub_total.set("")
        tax_amount.set("")
        discount.set("")
        grand_total.set("")

        paid_amount.set("")
        balance_amount.set("")

        payment_status.set("Paid")
      

        # 🔴 IMPORTANT: DO NOT TOUCH
        # current_purchase_id
        # mode



    def clear_purchase_form():
        clear_purchase_fields_only()


    def clear_purchases_form():
        current_purchase_id.set(0)

        clear_purchase_fields_only()

        mode.set("ADD")
        update_mode_ui()


        # 🔴 IMPORTANT: DO NOT TOUCH
        # current_tax_id
        # mode
    # ---------------- SEARCH TAX ----------------
    def search_purchase(*_):
        text = search_var.get().strip()

        # 🔥 SEARCH CLEARED → ONLY CLEAR FIELDS (STAY IN SAME MODE)
        if not text:
            clear_purchase_fields_only()
            update_mode_ui()
            return

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT *
            FROM purchases
            WHERE
                company_name LIKE %s
                OR invoice_no LIKE %s
                OR bill_type LIKE %s
                OR payment_status LIKE %s
                OR payment_mode LIKE %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (
            f"%{text}%",
            f"%{text}%",
            f"%{text}%",
            f"%{text}%",
            f"%{text}%"
        ))

        row = cur.fetchone()
        conn.close()

        if not row:
            clear_purchase_fields_only()
            return

        # ---------------- LOAD DATA INTO PURCHASE FORM ----------------
        current_purchase_id.set(row["id"])

        company_name.set(row["company_name"] or "")
        invoice_no.set(row["invoice_no"] or "")
        purchase_date.set(str(row["purchase_date"] or ""))

        supplier_id.set(str(row["supplier_id"] or ""))

        bill_type.set(row["bill_type"] or "Cash")
        payment_mode.set(row["payment_mode"] or "Cash")

        sub_total.set(str(row["sub_total"] or ""))
        tax_amount.set(str(row["tax_amount"] or ""))
        discount.set(str(row["discount"] or ""))
        grand_total.set(str(row["grand_total"] or ""))

        paid_amount.set(str(row["paid_amount"] or ""))
        balance_amount.set(str(row["balance_amount"] or ""))

        payment_status.set(row["payment_status"] or "Paid")
      

        mode.set("UPDATE")
        update_mode_ui()

    search_entry.bind("<KeyRelease>", search_purchase)

    sup_id = supplier_id.get().strip()
    if sup_id == "":
        sup_id = None
    else:
        sup_id = int(sup_id)


    # ---------------- SAVE PURCHASE ----------------
    def save_purchase():
        # ---------- BASIC VALIDATION ----------
        if not company_name.get() or not invoice_no.get():
            messagebox.showwarning(
                "Missing",
                "Company Name & Invoice No are required"
            )
            return

        # ---------- SAFE DATE (YYYY-MM-DD) ----------
        from datetime import datetime

        raw_date = purchase_date.get().strip()
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Purchase Date must be in YYYY-MM-DD format\nExample: 2026-01-01"
            )
            return

        # ---------- SAFE supplier_id (OPTIONAL) ----------
        sup_id_raw = supplier_id.get().strip()
        if sup_id_raw == "":
            sup_id = None
        else:
            try:
                sup_id = int(sup_id_raw)
            except ValueError:
                messagebox.showerror(
                    "Invalid Supplier ID",
                    "Supplier ID must be a number"
                )
                return

        conn = get_db()
        cur = conn.cursor()

        try:
            # ---------- UPDATE ----------
            if mode.get() == "UPDATE" and current_purchase_id.get() != 0:
                cur.execute("""
                    UPDATE purchases SET
                        company_name=%s,
                        purchase_date=%s,
                        invoice_no=%s,
                        supplier_id=%s,
                        bill_type=%s,
                        sub_total=%s,
                        tax_amount=%s,
                        discount=%s,
                        grand_total=%s,
                        paid_amount=%s,
                        balance_amount=%s,
                        payment_status=%s,
                        payment_mode=%s
                    WHERE id=%s
                """, (
                    company_name.get(),
                    parsed_date,          # 🔥 SAFE DATE
                    invoice_no.get(),
                    sup_id,               # 🔥 SAFE SUPPLIER
                    bill_type.get(),
                    float(sub_total.get() or 0),
                    float(tax_amount.get() or 0),
                    float(discount.get() or 0),
                    float(grand_total.get() or 0),
                    float(paid_amount.get() or 0),
                    float(balance_amount.get() or 0),
                    payment_status.get(),
                    payment_mode.get(),
                    current_purchase_id.get()
                ))
                messagebox.showinfo("Success", "✅ Purchase updated successfully")

            # ---------- INSERT ----------
            else:
                cur.execute("""
                    INSERT INTO purchases
                    (
                        company_name, purchase_date, invoice_no,
                        supplier_id, bill_type, sub_total,
                        tax_amount, discount, grand_total,
                        paid_amount, balance_amount,
                        payment_status, payment_mode
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    company_name.get(),
                    parsed_date,          # 🔥 SAFE DATE
                    invoice_no.get(),
                    sup_id,               # 🔥 SAFE SUPPLIER
                    bill_type.get(),
                    float(sub_total.get() or 0),
                    float(tax_amount.get() or 0),
                    float(discount.get() or 0),
                    float(grand_total.get() or 0),
                    float(paid_amount.get() or 0),
                    float(balance_amount.get() or 0),
                    payment_status.get(),
                    payment_mode.get()
                ))
                messagebox.showinfo("Success", "✅ Purchase added successfully")

            conn.commit()

            # ---------- RESET FORM ----------
            clear_purchase_form()
            current_purchase_id.set(0)
            mode.set("ADD")
            update_mode_ui()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            conn.close()


            # # ---------------- RESET ----------------
            # clear_purchase_form()
            # current_purchase_id.set(0)
            # mode.set("ADD")
            # update_mode_ui()

            # 🔥 OPTIONAL: refresh table
            # load_purchases()

        
    
    # ================= SAVE BUTTON (FIXED POSITION) =================
    save_btn = tk.Button(
        win,                     # 🔥 card / action_bar illa
        text="💾 Save Purchase",
        bg="#2563eb",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=25,
        pady=8,
        relief="flat",
        command=save_purchase
    )

    # 🔥 Always bottom-right (parallel issue gone)
    save_btn.place(
        relx=1.0,
        rely=1.0,
        anchor="se",
        x=-25,    # right border gap
        y=-25     # bottom border gap
    )



    update_mode_ui()
    win.bind("<Return>", lambda e: save_purchase())





# -----------------------------------------------------------------------------------------------------------------------------------------
def open_sales_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector
    from datetime import date
    from tkinter import messagebox


    WORK_BG = "#F8FAFC"
    last_search_keyword = ""
    search_active = False

    def set_search_active(val):
        global search_active
        search_active = val

    def set_last_keyword(val):
        global last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Tax Details",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        # 🔥 Search cleared → full reset
        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # 🔥 Reset non-matching rows only
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        # 🔥 Apply permanent highlight
        tree.after_idle(apply_search_highlight)




    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)


    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    # box_add = fixed_box(action_row, 140, 30)

    # btn_add_expense = tk.Button(
    #     box_add,
    #     text="➕ Add purchase",
    #     bg="#0EA5E9",
    #     fg="white",
    #     font=("Segoe UI", 9, "bold"),
    #     relief="flat",
    #     command=lambda: open_add_purchase_window(workspace, shop_id, purchase_id=None)
    # )

    # btn_add_expense.pack(fill="both", expand=True)


    
    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)

    tk.Label(
        box_from,
        text="From",
        bg="black",
        fg="white",
        font=("Segoe UI", 8)
    ).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy"
    )
    start_date.pack(side="left")


    # ---------------- TO DATE ----------------
    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)

    tk.Label(
        box_to,
        text="To",
        bg="black",
        fg="white",
        font=("Segoe UI", 8)
    ).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy"
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")


    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

   
    # ---------------- TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    # ---------------- COLUMNS ----------------
    columns = (
        "sno",
        "date",
        "Time",
        "barcode",
        "product_name",
        "mrp",
        "purchase_rate",
        "price",
        "qty",
        "stock",
        "discount_percent",
        "gst_percent",
        "amount",
        "profit",
        "loss",
        "delete",     # 🗑 DELETE
        "item_id"     # 🔒 HIDDEN
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    # ---------------- TAG COLORS ----------------
    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("profit", background="#DCFCE7")   # 🟢 light green
    tree.tag_configure("loss", background="#FEE2E2")     # 🔴 light red
    tree.tag_configure("match", background="#FFE08A")    # 🔍 search highlight

    # ---------------- HEADERS ----------------
    headers = [
        "S.No",
        "Date",
        "Time",
        "Barcode",
        "Product",
        "MRP",
        "Purchase",
        "Price",
        "Qty",
        "Stock",
        "Disc %",
        "GST %",
        "Amount",
        "Profit",
        "Loss",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    # ---------------- COLUMN SETTINGS ----------------
    tree.column("sno", width=60, anchor="center")
    tree.column("date", width=100, anchor="center")
    tree.column("Time", width=100, anchor="center")
    tree.column("barcode", width=130, anchor="center")
    tree.column("product_name", width=200, anchor="w")

    tree.column("mrp", width=90, anchor="e")
    tree.column("purchase_rate", width=110, anchor="e")
    tree.column("price", width=100, anchor="e")

    tree.column("qty", width=70, anchor="center")
    tree.column("stock", width=90, anchor="center")

    tree.column("discount_percent", width=90, anchor="e")
    tree.column("gst_percent", width=80, anchor="e")

    tree.column("amount", width=120, anchor="e")
    tree.column("profit", width=100, anchor="e")
    tree.column("loss", width=100, anchor="e")

    tree.column("delete", width=70, anchor="center")
    tree.column("item_id", width=0, stretch=False)   # 🔒 hidden

    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)


    # =================================================
    # TOTAL SUMMARY BAR (BELOW SALES TABLE)
    # =================================================
    summary_bar = tk.Frame(main, bg="#F1F5F9", height=42)
    summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    summary_bar.pack_propagate(False)

    lbl_total_amount = tk.Label(
        summary_bar,
        text="Total Amount : ₹0",
        bg="#F1F5F9",
        fg="black",
        font=("Segoe UI", 10, "bold")
    )
    lbl_total_amount.pack(side="left", padx=20)

    lbl_total_profit = tk.Label(
        summary_bar,
        text="Total Profit : ₹0",
        bg="#F1F5F9",
        fg="#16A34A",   # 🟢 green
        font=("Segoe UI", 10, "bold")
    )
    lbl_total_profit.pack(side="left", padx=20)

    lbl_total_loss = tk.Label(
        summary_bar,
        text="Total Loss : ₹0",
        bg="#F1F5F9",
        fg="#DC2626",   # 🔴 red
        font=("Segoe UI", 10, "bold")
    )
    lbl_total_loss.pack(side="left", padx=20)

    def update_sales_totals():
        total_amount = 0.0
        total_profit = 0.0
        total_loss = 0.0

        for item in tree.get_children():
            values = tree.item(item, "values")

            if len(values) < 15:
                continue

            # ---------- AMOUNT ----------
            try:
                amt = float(str(values[12]).replace("₹", "").replace(",", "").strip())
            except:
                amt = 0.0

            # ---------- PROFIT ----------
            try:
                prof = float(str(values[13]).replace("₹", "").replace(",", "").strip())
            except:
                prof = 0.0

            # ---------- LOSS (🔥 IMPORTANT FIX) ----------
            try:
                loss = float(str(values[14]).replace("₹", "").replace(",", "").strip())
            except:
                loss = 0.0

            total_amount += amt
            total_profit += max(prof, 0)   # only positive profit
            total_loss   += max(loss, 0)   # only positive loss

        lbl_total_amount.config(text=f"Total Amount : ₹{total_amount:,.2f}")
        lbl_total_profit.config(text=f"Total Profit : ₹{total_profit:,.2f}")
        lbl_total_loss.config(text=f"Total Loss : ₹{total_loss:,.2f}")



    update_sales_totals()


   # =================================================
    def load_sales(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                MAX(DATE(s.date_time)) AS bill_date,
                MAX(TIME(s.date_time)) AS bill_time,

                p.barcode1,
                p.product_name,
                p.mrp_rate,
                p.purchase_rate,

                si.price AS sale_price,
                SUM(si.quantity) AS total_qty,
                p.stock,

                0 AS discount_percent,
                (p.gst_sgst + p.gst_cgst) AS gst_percent,

                SUM(si.subtotal) AS total_amount,

                SUM(
                    CASE
                        WHEN si.price > p.purchase_rate
                        THEN (si.price - p.purchase_rate) * si.quantity
                        ELSE 0
                    END
                ) AS total_profit,

                SUM(
                    CASE
                        WHEN si.price < p.purchase_rate
                        THEN (p.purchase_rate - si.price) * si.quantity
                        ELSE 0
                    END
                ) AS total_loss

            FROM sales_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE 1=1
        """

        params = []

        # 🔍 SEARCH FILTER
        if search:
            query += " AND (p.product_name LIKE %s OR p.barcode1 LIKE %s)"
            s = f"%{search}%"
            params.extend([s, s])

        # 📅 DATE FILTER (IMPORTANT PART)
        if from_dt and to_dt:
            query += " AND DATE(s.date_time) BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += """
            GROUP BY
                p.barcode1,
                p.product_name,
                p.mrp_rate,
                p.purchase_rate,
                si.price,
                p.stock,
                p.gst_sgst,
                p.gst_cgst
            ORDER BY
                total_qty DESC
        """

        cur.execute(query, params)

        for i, r in enumerate(cur.fetchall(), start=1):

            if r[12] > 0:
                tag = "profit"
            elif r[13] > 0:
                tag = "loss"
            else:
                tag = "even" if i % 2 == 0 else "odd"

            tree.insert(
                "",
                "end",
                values=(
                    i,              # S.No
                    r[0],           # Date
                    r[1],           # Time
                    r[2],           # Barcode
                    r[3],           # Product
                    f"{r[4]:.2f}",  # MRP
                    f"{r[5]:.2f}",  # Purchase
                    f"{r[6]:.2f}",  # Sale Price
                    r[7],           # TOTAL QTY
                    r[8],           # Stock
                    f"{r[9]:.2f}",  # Disc %
                    f"{r[10]:.2f}", # GST %
                    f"{r[11]:.2f}", # Amount
                    f"{r[12]:.2f}", # Profit
                    f"{r[13]:.2f}", # Loss
                    "🗑",
                    None
                ),
                tags=(tag,)
            )

        conn.close()
        update_sales_totals()


    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")
    tree.tag_configure("profit", background="#DCFCE7")   # 🟢 green
    tree.tag_configure("loss", background="#F4A0A0")     # 🔴 red
    tree.tag_configure("match", background="#FFE08A")

   # =================================================
    # DELETE SALES ITEM
    # =================================================
    def delete_sale(item_id):
        if not messagebox.askyesno("Confirm", "Delete this sales item?"):
            return

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM billing_items WHERE item_id = %s",
            (item_id,)
        )

        conn.commit()
        conn.close()

        load_sales()   # 🔥 reload sales table


    # =================================================
    # TREE CLICK HANDLER (DELETE ICON)
    # =================================================
    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 🗑 DELETE column
        # Sales Treeview columns order:
        # 1:S.No 2:Barcode 3:Product 4:MRP 5:Purchase
        # 6:Price 7:Qty 8:Stock 9:Disc 10:GST
        # 11:Amount 12:Profit 13:Loss 14:Delete 15:item_id(hidden)
        if col_id == "#14":
            values = tree.item(row_id, "values")

            # safety
            if len(values) < 15:
                return

            item_id = values[14]   # 🔒 hidden item_id
            delete_sale(item_id)


    tree.bind("<Button-1>", on_tree_click)
    load_sales()


    # =================================================
    # ZEBRA RESTORE (KEEP SEARCH HIGHLIGHT)
    # =================================================
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            if search_active:
                tags = tree.item(item, "tags")
                if "match" in tags:
                    continue   # 🔥 keep highlight permanent

            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))


   
    # =================================================
    # INLINE EDIT (DOUBLE CLICK) – SALES PAGE
    # =================================================
    edit_entry = None

    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if not row_id or col in ("#14", "#15"):
            return

        values = tree.item(row_id, "values")
        item_id = values[-1]

        # ❌ Block edit if item_id is None
        if item_id in (None, "", "None"):
            messagebox.showinfo(
                "Not Editable",
                "Grouped / summary row edit panna mudiyadhu ❌"
            )
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.insert(0, value)
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            if col in ("#6", "#7", "#9", "#10", "#11", "#12", "#13"):
                try:
                    new_val = f"{float(new_val):.2f}"
                except:
                    new_val = "0.00"

            tree.set(row_id, col, new_val)
            update_sales_db(row_id, col, new_val)
            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())



    tree.bind("<Double-1>", on_double_click)





    sales_col_map = {
        "#2": "barcode",
        "#3": "product_name",
        "#4": "mrp",
        "#5": "purchase_rate",
        "#6": "price",              # ✅ SALE PRICE
        "#7": "qty",
        "#8": "stock",
        "#9": "discount_percent",
        "#10": "gst_percent",
        "#11": "amount",
        "#12": "profit",
        "#13": "loss"
    }




    def clean_numeric(val):
        return val.replace("%", "").replace("₹", "").strip()


    # =================================================
    # UPDATE SALES DB (INLINE EDIT)
    # =================================================
    def update_sales_db(row_id, col, value):
        db_col = sales_col_map.get(col)
        if not db_col:
            return

        values = tree.item(row_id)["values"]

        # 🔒 hidden item_id
        item_id = values[-1]

        # ❌ SAFETY: item_id illa na DB update panna vendam
        if item_id in (None, "", "None"):
            print("⚠️ Skipping DB update: item_id is None")
            return

        # 🔥 TEXT
        if db_col == "product_name":
            value = value.strip()

        # 🔥 NUMERIC SAFETY
        elif db_col in (
            "mrp", "purchase_rate", "price", "qty", "stock",
            "discount_percent", "gst_percent", "amount", "profit", "loss"
        ):
            try:
                value = float(clean_numeric(str(value)))
            except:
                value = 0.0

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE billing_items
            SET {db_col} = %s
            WHERE item_id = %s
            """,
            (value, item_id)
        )

        conn.commit()
        conn.close()



    # =================================================
    # APPLY / CLEAR DATE FILTER – SALES PAGE
    # =================================================

    def prevent_future_date(event=None):
        today = date.today()

        # FROM date check
        if start_date.get_date() > today:
            messagebox.showerror(
                "Invalid Date",
                "Future date select panna mudiyadhu ❌"
            )
            start_date.set_date(today)

        # TO date check
        if end_date.get_date() > today:
            messagebox.showerror(
                "Invalid Date",
                "Future date select panna mudiyadhu ❌"
            )
            end_date.set_date(today)

    start_date.bind("<<DateEntrySelected>>", prevent_future_date)
    end_date.bind("<<DateEntrySelected>>", prevent_future_date)

 
    
    date_filter_active = False

    def toggle_date_filter():
        global date_filter_active

        from_dt = start_date.get_date()
        to_dt   = end_date.get_date()
        today   = date.today()

        # ❌ FUTURE DATE BLOCK
        if from_dt > today or to_dt > today:
            messagebox.showerror(
                "Invalid Date",
                "Future date select panna mudiyadhu ❌"
            )
            return

        # ❌ FROM > TO BLOCK
        if from_dt > to_dt:
            messagebox.showerror(
                "Invalid Range",
                "From date To date-kku munna irukkanum ❌"
            )
            return

        # ✅ APPLY / CLEAR
        if not date_filter_active:
            load_sales(
                search=search_var.get().strip(),
                from_dt=from_dt,
                to_dt=to_dt
            )
            btn_apply.config(text="Clear", bg="#DC2626")
            date_filter_active = True
        else:
            load_sales(search=search_var.get().strip())
            btn_apply.config(text="Apply", bg="#192987")
            date_filter_active = False


    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)
    
    
    # ---------------- DAY FILTER ----------------
    box_day = fixed_box(action_row, 220, 30)

    tk.Label(
        box_day,
        text="Day",
        bg="black",
        fg="white",
        font=("Segoe UI", 8)
    ).pack(side="left", padx=4)

    day_date = DateEntry(
        box_day,
        width=10,
        date_pattern="dd-mm-yyyy"
    )
    day_date.set_date(datetime.today().date())
    day_date.pack(side="left", padx=(0, 4))

    btn_day_apply = tk.Button(
        box_day,
        text="Apply",
        bg="#1D4ED8",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat"
    )
    btn_day_apply.pack(side="left", padx=4)


    def load_sales_by_day(selected_day):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                MAX(DATE(s.date_time))   AS bill_date,
                MAX(TIME(s.date_time))   AS bill_time,

                p.barcode1,
                p.product_name,
                p.mrp_rate,
                p.purchase_rate,

                si.price,
                SUM(si.quantity)         AS total_qty,
                p.stock,

                0 AS discount_percent,
                (p.gst_sgst + p.gst_cgst) AS gst_percent,

                SUM(si.subtotal)         AS total_amount,

                SUM(
                    CASE
                        WHEN si.price > p.purchase_rate
                        THEN (si.price - p.purchase_rate) * si.quantity
                        ELSE 0
                    END
                ) AS total_profit,

                SUM(
                    CASE
                        WHEN si.price < p.purchase_rate
                        THEN (p.purchase_rate - si.price) * si.quantity
                        ELSE 0
                    END
                ) AS total_loss

            FROM sales_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id

            WHERE DATE(s.date_time) = %s

            GROUP BY
                p.barcode1,
                p.product_name,
                p.mrp_rate,
                p.purchase_rate,
                si.price,
                p.stock,
                p.gst_sgst,
                p.gst_cgst

            ORDER BY total_qty DESC
        """

        cur.execute(query, (selected_day,))

        for i, r in enumerate(cur.fetchall(), start=1):
            if r[12] > 0:
                tag = "profit"
            elif r[13] > 0:
                tag = "loss"
            else:
                tag = "even" if i % 2 == 0 else "odd"

            tree.insert(
                "",
                "end",
                values=(
                    i,              # S.No
                    r[0],           # Date
                    r[1],           # Time
                    r[2],           # Barcode
                    r[3],           # Product
                    f"{r[4]:.2f}",  # MRP
                    f"{r[5]:.2f}",  # Purchase
                    f"{r[6]:.2f}",  # Price
                    r[7],           # TOTAL QTY
                    r[8],           # Stock
                    f"{r[9]:.2f}",  # Disc %
                    f"{r[10]:.2f}", # GST %
                    f"{r[11]:.2f}", # Amount
                    f"{r[12]:.2f}", # Profit
                    f"{r[13]:.2f}", # Loss
                    "🗑",
                    None
                ),
                tags=(tag,)
            )

        conn.close()
        update_sales_totals()



    def prevent_future_day(event=None):
        today = date.today()
        if day_date.get_date() > today:
            messagebox.showerror(
                "Invalid Date",
                "Future date select panna mudiyadhu ❌"
            )
            day_date.set_date(today)

    day_date.bind("<<DateEntrySelected>>", prevent_future_day)

    def apply_day_filter():
        selected_day = day_date.get_date()
        load_sales_by_day(selected_day)
    day_filter_active = False

    def toggle_day_filter():
        nonlocal day_filter_active   # 🔥 IMPORTANT FIX

        selected_day = day_date.get_date()
        today = date.today()

        # ❌ future date block
        if selected_day > today:
            messagebox.showerror(
                "Invalid Date",
                "Future date select panna mudiyadhu ❌"
            )
            day_date.set_date(today)
            return

        if not day_filter_active:
            # ✅ APPLY
            load_sales_by_day(selected_day)
            btn_day_apply.config(text="Clear", bg="#DC2626")
            day_filter_active = True
        else:
            # 🔄 CLEAR → normal sales
            load_sales()
            btn_day_apply.config(text="Apply", bg="#1D4ED8")
            day_filter_active = False


    btn_day_apply.config(command=toggle_day_filter)


    btn_apply = tk.Button(
        box_apply,
        text="Apply",
        command=apply_day_filter,
        bg="#1D4ED8",
        fg="white",
        font=("Segoe UI", 9, "bold")
    )
    btn_apply.pack(fill="both", expand=True)

    # =================================================
    # SEARCH (LIVE) – SALES PAGE
    # =================================================
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_sales(search=search_var.get().strip())
    )


    # =================================================
    # INITIAL LOAD – SALES
    # =================================================
    load_sales()

   
# ------------------------------------------------------------------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
import subprocess
from tkinter import messagebox


WORK_BG = "#F8FAFC"
ACCENT = "#3B82F6"
TITLE_COLOR = "#1E293B"
SELECTED_COLOR = "#BFDBFE"
bill_window_alive = False

def open_Estimate_bill_window(workspace,shop_id):
    workspace.unbind_all("<MouseWheel>")
    workspace.unbind_all("<Button-4>")
    workspace.unbind_all("<Button-5>")
    root = workspace.winfo_toplevel()

    # ❗ REMOVE EVERYTHING INSIDE WORKSPACE
    for child in workspace.winfo_children():
        child.destroy()

    # ✅ SINGLE ROOT CONTAINER
    content = tk.Frame(workspace, bg=WORK_BG)
    content.pack(fill="both", expand=True)

    # optional resize support
    content.rowconfigure(0, weight=1)
    content.columnconfigure(0, weight=1)

    # ✅ MAIN CARD (ONLY ONE BILL WINDOW)
    card = tk.Frame(
        content,
        bg="white",
        highlightbackground=ACCENT,
        highlightthickness=3
    )
    card.pack(fill="both", expand=True, padx=20, pady=20)
    root = workspace.winfo_toplevel()
    root = workspace.winfo_toplevel()
    global bill_window_alive, bill_tree
    bill_window_alive = True


    card.pack(fill="both", expand=True, padx=20, pady=20)

    toolbar = tk.Frame(card, bg="#F1F5F9")
    toolbar.pack(fill="x", padx=5, pady=(10, 5))

    payment_mode = tk.StringVar(value="")  # Cash / Credit

    top_frame = tk.Frame(card, bg="white")
    top_frame.pack(fill="x", padx=0, pady=0)
   


    def field(parent, text, w):
        f = tk.Frame(parent, bg="white")
        tk.Label(f, text=text, bg="white", fg=TITLE_COLOR, font=("Segoe UI", 11)).pack(anchor="w")
        e = tk.Entry(f, width=w, bg=WORK_BG, fg="#0F172A", relief="solid", bd=1, font=("Segoe UI", 11))
        e.pack()
        f.pack(side="left", padx=12)
        return e

    def clear_top():
        for w in top_frame.winfo_children():
            w.destroy()

    def show_product_fields():
        clear_top()
        global entry_barcode, entry_pid, entry_qty, edit_mode, edit_item

        edit_mode = False
        edit_item = None

        entry_barcode = field(top_frame, "Barcode / Name", 22)
        entry_pid     = field(top_frame, "Product ID", 14)
        entry_qty     = field(top_frame, "Quantity", 10)

        entry_barcode.bind("<Return>", lambda e: add_product("barcode"))
        entry_pid.bind("<Return>", lambda e: add_product("pid"))
        entry_qty.bind("<Return>", lambda e: add_product("barcode"))

        entry_barcode.focus_set()



    def show_customer_fields():
        clear_top()

        global entry_cid, entry_cname, entry_phone, entry_points, entry_address

        entry_phone   = field(top_frame, "Phone", 16)
        entry_cname   = field(top_frame, "Customer Name", 18)
        entry_cid     = field(top_frame, "Customer ID", 14)
        entry_address = field(top_frame, "Address", 18)
        entry_points  = field(top_frame, "Current Points", 14)

        # 🔥 ENTER triggers same search
        entry_phone.bind("<Return>", lambda e: search_customer())
        entry_cname.bind("<Return>", lambda e: search_customer())
        entry_cid.bind("<Return>", lambda e: search_customer())

        entry_phone.focus_set()



        

    def search_customer():
        cid   = entry_cid.get().strip()
        phone = entry_phone.get().strip()
        name  = entry_cname.get().strip()

        if not cid and not phone and not name:
            return

        conn = get_connection()
        cur = conn.cursor()

        row = None

       # 1️⃣ Search by Customer ID
        if cid:
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, current_points
                FROM customers
                WHERE shop_id=%s AND customer_id=%s AND status='ACTIVE'
                LIMIT 1
            """, (shop_id, cid))
            row = cur.fetchone()

        # 2️⃣ Search by Phone
        elif phone:
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, current_points
                FROM customers
                WHERE shop_id=%s AND phone_1=%s AND status='ACTIVE'
                LIMIT 1
            """, (shop_id, phone))
            row = cur.fetchone()

        # 3️⃣ Search by Name
        elif name:
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, current_points
                FROM customers
                WHERE shop_id=%s
                AND customer_name LIKE %s
                AND status='ACTIVE'
                ORDER BY customer_id DESC
                LIMIT 1
            """, (shop_id, f"%{name}%"))
            row = cur.fetchone()

        conn.close()

        if row:
            fill_customer_fields(row)
            return

        # ---- NOT FOUND ----
        if phone:
            open_add_customer_popup(phone)
        else:
            messagebox.showinfo("Not Found", "Customer not found")


            

        if row:
            fill_customer_fields(row)
        else:
            open_add_customer_popup(phone)
    
    def fill_customer_fields(row):
        entry_cid.delete(0, tk.END)
        entry_cname.delete(0, tk.END)
        entry_phone.delete(0, tk.END)
        entry_address.delete(0, tk.END)
        entry_points.delete(0, tk.END)

        entry_cid.insert(0, row[0])
        entry_cname.insert(0, row[1])
        entry_phone.insert(0, row[2])
        entry_address.insert(0, row[3] or "")
        entry_points.insert(0, row[4] or 0)


    from tkinter import messagebox

    def open_add_customer_popup(phone):
        parent = workspace.winfo_toplevel()

        win = tk.Toplevel(parent)
        win.title("Add Customer")
        win.resizable(False, False)
        win.configure(bg="white")

        # =========================
        # CENTER WINDOW
        # =========================
        win.update_idletasks()
        popup_w, popup_h = 380, 260

        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        x = px + (pw // 2) - (popup_w // 2)
        y = py + (ph // 2) - (popup_h // 2)

        win.geometry(f"{popup_w}x{popup_h}+{x}+{y}")
        win.focus_force()

        # =========================
        # SAFE CLOSE
        # =========================
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.bind("<Escape>", lambda e: win.destroy())

        # =========================
        # CARD UI
        # =========================
        card = tk.Frame(win, bg="white",
                        highlightbackground=ACCENT,
                        highlightthickness=2)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(
            card,
            text="Add Customer",
            bg="white",
            fg=ACCENT,
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(4, 14))

        def row(label, default=""):
            f = tk.Frame(card, bg="white")
            f.pack(fill="x", pady=6)

            tk.Label(
                f, text=label, width=10, anchor="w",
                bg="white", fg="#000000",
                font=("Segoe UI", 9)
            ).pack(side="left")

            e = tk.Entry(f, font=("Segoe UI", 9),
                        bg="white", fg="#000000")
            e.pack(side="left", fill="x", expand=True)
            e.insert(0, default)
            return e

        e_phone = row("Phone", phone)
        e_phone.config(state="readonly")

        e_name = row("Name")
        e_addr = row("Address")

        # =========================
        # ENTER KEY FLOW 🔥
        # =========================
        e_name.bind("<Return>", lambda e: e_addr.focus_set())
        e_addr.bind("<Return>", lambda e: save_customer())

        e_name.focus_set()

        # =========================
        # SAVE LOGIC
        # =========================
        def save_customer():
            name = e_name.get().strip()
            addr = e_addr.get().strip()

            if not phone or not name:
                messagebox.showwarning(
                    "Missing Details",
                    "Please fill Phone and Name"
                )
                return

            conn = get_connection()
            cur = conn.cursor()

            # INSERT CUSTOMER
            cur.execute("""
                INSERT INTO customers
                (shop_id, customer_name, phone_1, address, status)
                VALUES (%s,%s,%s,%s,'ACTIVE')
            """, (
                shop_id,
                name,
                phone,
                addr
            ))

            customer_id = cur.lastrowid   # ✅ VERY IMPORTANT

            conn.commit()

            # 🔥 FETCH SAME CUSTOMER IMMEDIATELY
            cur.execute("""
                SELECT customer_id, customer_name, phone_1, address, total_points
                FROM customers
                WHERE customer_id = %s
            """, (customer_id,))

            row = cur.fetchone()
            conn.close()

            messagebox.showinfo("Success", "Customer saved successfully")

            win.destroy()

            # ✅ DIRECTLY FILL BILLING FIELDS
            if row:
                fill_customer_fields(row)

        tk.Button(
            card,
            text="Save",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            width=12,
            command=save_customer
        ).pack(pady=14)

# customer  details show until  bill print
    # =========================
    # GLOBAL STATE
    # =========================
    current_customer = {
        "id": None,
        "name": "",
        "phone": "",
        "address": "",
        "points": 0
    }


    def show_customer_fields():
        """
        Customer button click:
        - UI recreate pannum
        - Global current_customer data irundha fill pannum
        """

        clear_top()          # 🔥 recreate UI safely
        create_customer_fields()

        if current_customer["id"] is None:
            return   # no customer yet

        entry_phone.insert(0, current_customer["phone"])
        entry_cname.insert(0, current_customer["name"])
        entry_cid.insert(0, current_customer["id"])
        entry_address.insert(0, current_customer["address"])
        entry_points.insert(0, current_customer["points"])

    def create_customer_fields():
        global entry_cid, entry_cname, entry_phone, entry_points, entry_address

        entry_phone   = field(top_frame, "Phone", 16)
        entry_cname   = field(top_frame, "Customer Name", 18)
        entry_cid     = field(top_frame, "Customer ID", 14)
        entry_address = field(top_frame, "Address", 18)
        entry_points  = field(top_frame, "Current Points", 14)

        entry_phone.bind("<Return>", lambda e: search_customer())
        entry_cname.bind("<Return>", lambda e: search_customer())
        entry_cid.bind("<Return>", lambda e: search_customer())



    def fill_customer_fields(row):
        current_customer["id"] = row[0]
        current_customer["name"] = row[1]
        current_customer["phone"] = row[2]
        current_customer["address"] = row[3] or ""
        current_customer["points"] = row[4] or 0

        show_customer_fields()



    # =========================
    # CLEAR FUNCTIONS
    # =========================
    def clear_customer_fields():
        for e in (entry_cid, entry_cname, entry_phone, entry_address, entry_points):
            e.delete(0, tk.END)

    def clear_product_fields():
        entry_barcode.delete(0, tk.END)
        entry_pid.delete(0, tk.END)
        entry_qty.delete(0, tk.END)
        entry_barcode.focus_set()


    # =========================
    # PRODUCT ADD
    # =========================
    def add_product():
        # 🚫 customer select pannama product allow panna koodaadhu
        if current_customer["id"] is None:
            messagebox.showwarning("Select Customer", "Please select customer first")
            return

        pid = entry_pid.get().strip()
        barcode = entry_barcode.get().strip()
        qty = entry_qty.get().strip()

        qty = int(qty) if qty else 1

        conn = get_connection()
        cur = conn.cursor()

        if pid:
            cur.execute("""
                SELECT product_id, product_name, selling_price
                FROM products
                WHERE product_id=%s AND status='ACTIVE'
            """, (pid,))
        else:
            cur.execute("""
                SELECT product_id, product_name, selling_price
                FROM products
                WHERE barcode=%s AND status='ACTIVE'
            """, (barcode,))

        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "Product not found")
            return

        pid, name, price = row
        total = qty * price

        bill_tree.insert(
            "", "end",
            values=(pid, name, price, qty, total)
        )

        clear_product_fields()   # ✅ ONLY PRODUCT CLEAR




    # =========================
    # Cash / Credit toggle with tick
    # =========================
    def toggle_payment(mode):
        if payment_mode.get() == mode:
            payment_mode.set("")
        else:
            payment_mode.set(mode)
        update_payment_buttons()

    def update_payment_buttons():
        if payment_mode.get() == "Cash":
            cash_btn.config(bg=SELECTED_COLOR, text="✔ Cash")
            credit_btn.config(bg="#E5E7EB", text="Credit")
        elif payment_mode.get() == "Credit":
            credit_btn.config(bg=SELECTED_COLOR, text="✔ Credit")
            cash_btn.config(bg="#E5E7EB", text="Cash")
        else:
            cash_btn.config(bg="#E5E7EB", text="Cash")
            credit_btn.config(bg="#E5E7EB", text="Credit")

    # =========================
    # Toolbar buttons sequence
    # =========================
    btn_product = tk.Button(toolbar, text="Product", bg="#E5E7EB", fg="#0F172A",
                            font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                            padx=14, pady=4, command=show_product_fields)
    btn_product.pack(side="left", padx=4)

    btn_customer = tk.Button(toolbar, text="Customer", bg="#E5E7EB", fg="#0F172A",
                             font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                             padx=14, pady=4, command=show_customer_fields)
    btn_customer.pack(side="left", padx=4)


    # 🔥 EDIT BUTTON (CENTER)
    btn_customer = tk.Button(
        toolbar, text="Customer",
        bg="#E5E7EB", fg="#0F172A",
        font=("Segoe UI", 10, "bold"),
        relief="solid", bd=1,
        padx=14, pady=4,
        command=show_customer_fields   # 🔥 NOT recreate
    )
    edit_btn = tk.Button(toolbar, text="Edit", bg="#E5E7EB", fg="#0F172A",
                         font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                         padx=14, pady=4, command=lambda:None)
    edit_btn.pack(side="left", padx=4)

    cash_btn = tk.Button(toolbar, text="Cash", bg="#E5E7EB", fg="#0F172A",
                         font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                         padx=14, pady=4, command=lambda: toggle_payment("Cash"))
    cash_btn.pack(side="left", padx=4)

    credit_btn = tk.Button(toolbar, text="Credit", bg="#E5E7EB", fg="#0F172A",
                           font=("Segoe UI", 10, "bold"), relief="solid", bd=1,
                           padx=14, pady=4, command=lambda: toggle_payment("Credit"))
    credit_btn.pack(side="left", padx=4)

    top_row = tk.Frame(card, bg="white")
    top_row.pack(fill="x", padx=20, pady=(5, 10))

    spacer = tk.Frame(toolbar, bg="#F1F5F9")
    spacer.pack(side="left", expand=True, fill="x")

    status_frame = tk.Frame(toolbar, bg="#F1F5F9")
    status_frame.pack(side="right", padx=(0, 6))



    right_status = tk.Frame(top_row, bg="white")
    right_status.pack(side="right", anchor="e", padx=10)


    

    import socket

    def is_network_connected():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False

    net_canvas = tk.Canvas(
        status_frame,
        width=28,
        height=28,
        bg="#F1F5F9",
        highlightthickness=0
    )
    net_canvas.pack(side="left", padx=(0, 8))

    square = net_canvas.create_rectangle(2, 2, 26, 26, outline="")
    icon = net_canvas.create_text(
        14, 14,
        font=("Segoe UI", 12, "bold")
    )

    def update_network_status():
        if is_network_connected():
            net_canvas.itemconfig(square, fill="#22c55e")
            net_canvas.itemconfig(icon, text="✔", fill="white")
        else:
            net_canvas.itemconfig(square, fill="#ef4444")
            net_canvas.itemconfig(icon, text="✖", fill="white")

        net_canvas.after(3000, update_network_status)

    update_network_status()




    # -------------------------------
    # 🔘 MODERN TOGGLE (BORDER FIXED)
    # -------------------------------
    sms_enabled = load_sms_state()



    toggle = tk.Canvas(
        status_frame,
        width=90,
        height=30,
        bg="#F1F5F9",
        highlightthickness=0
    )
    toggle.pack(side="left")

    bg = toggle.create_rectangle(
        1, 1, 89, 29,
        outline="#9ca3af",
        fill="#e5e7eb"
    )

    knob = toggle.create_oval(
        4, 4, 26, 26,
        fill="white",
        outline="#9ca3af"
    )

    label = toggle.create_text(
        45, 15,
        font=("Segoe UI", 9, "bold")
    )

    def draw_toggle():
        if sms_enabled:
            toggle.itemconfig(bg, fill="#2563eb")
            toggle.coords(knob, 62, 4, 86, 26)
            toggle.itemconfig(label, text="ON", fill="white")
        else:
            toggle.itemconfig(bg, fill="#e5e7eb")
            toggle.coords(knob, 4, 4, 26, 26)
            toggle.itemconfig(label, text="OFF", fill="#111827")

    



    def toggle_sms(event=None):
        nonlocal sms_enabled
        sms_enabled = not sms_enabled
        save_sms_state(sms_enabled)

        if sms_enabled:
            enable_sms_sending()
        else:
            disable_sms_sending()

        draw_toggle()

    toggle.bind("<Button-1>", toggle_sms)
    draw_toggle()


    # -------------------------------
    # SMS METHODS (YOUR REAL LOGIC HERE)
    # -------------------------------
    def enable_sms_sending():
        print("✅ SMS SENDING ENABLED")

    def disable_sms_sending():
        print("❌ SMS SENDING DISABLED")
    
    # =============================
    # TABLE FRAME
    # =============================
    table_frame = tk.Frame(card, bg="white", bd=1, relief="solid")
    table_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=(10, 0)
    )

    # 🔥 IMPORTANT: stop auto resize
    table_frame.pack_propagate(False)

    # =============================
    # INNER CONTAINER (FOR SCROLL)
    # =============================
    table_container = tk.Frame(table_frame, bg="white")
    table_container.pack(fill="both", expand=True)

    # =============================
    # TREEVIEW
    # =============================
    columns = ("no", "pid", "name", "mrp", "price", "qty", "amount", "delete", "edit")

    tree = ttk.Treeview(
        table_container,
        columns=columns,
        show="headings"
    )

    headings = {
        "no": "No",
        "pid": "P.ID",
        "name": "Name",
        "mrp": "MRP",
        "price": "Price",
        "qty": "Qty",
        "amount": "Amount",
        "delete": "Delete",
        "edit": "Edit"
    }

    for c in columns:
        tree.heading(c, text=headings[c])
        tree.column(c, anchor="center", width=90)

    tree.column("name", width=220)

    # =============================
    # SCROLLBAR
    # =============================
    table_scroll = ttk.Scrollbar(
        table_container,
        orient="vertical",
        command=tree.yview
    )

    tree.configure(yscrollcommand=table_scroll.set)

    # =============================
    # PACK ORDER (VERY IMPORTANT)
    # =============================
    tree.pack(side="left", fill="both", expand=True)
    table_scroll.pack(side="right", fill="y")


    # =============================
    # TABLE CLICK LOGIC
    # =============================
    def on_table_click(event):
        global inline_edit_active, editing_from_icon

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not row_id:
            return

        values = list(tree.item(row_id, "values"))
        col_index = int(col.replace("#", "")) - 1
        cell_value = values[col_index]

        # ❌ DELETE (disable during inline edit)
        if cell_value == "❌":
            if inline_edit_active:
                return
            tree.delete(row_id)
            refresh_row_numbers()
            calculate_total()
            return

        # ✏ EDIT BUTTON CLICK
        if cell_value == "✏":
            inline_edit_active = True        # 🔒 BLOCK PANEL
            editing_from_icon = True
            tree.selection_set(row_id)
            start_inline_edit(row_id)
            return


    def start_inline_edit(row_id):
        global editing_row, edit_entries, inline_edit_active

        inline_edit_active = True
        editing_row = row_id
        edit_entries = {}
        values = list(tree.item(row_id, "values"))

        for col_index in range(7):  # No → Amount
            bbox = tree.bbox(row_id, f"#{col_index+1}")
            if not bbox:
                continue

            x, y, w, h = bbox
            e = tk.Entry(tree, font=("Segoe UI", 10))
            e.place(x=x, y=y, width=w, height=h)
            e.insert(0, values[col_index])
            e.focus()

            e.bind("<Return>", save_inline_edit)
            e.bind("<FocusOut>", save_inline_edit)

            edit_entries[col_index] = e


    def save_inline_edit(event=None):
        global editing_row, edit_entries, inline_edit_active, editing_from_icon

        if not editing_row:
            return

        values = list(tree.item(editing_row, "values"))

        for i, e in edit_entries.items():
            values[i] = e.get()
            e.destroy()

        try:
            price = float(values[4])
            qty = int(values[5])
            values[6] = round(price * qty, 2)
        except:
            values[6] = 0

        values[7] = "❌"
        values[8] = "✏"

        tree.item(editing_row, values=values)

        editing_row = None
        edit_entries = {}
        inline_edit_active = False      # 🔓 UNLOCK PANEL
        editing_from_icon = False

        calculate_total()

    def on_row_select(event=None):
        global inline_edit_active

        if inline_edit_active:
            return    # 🚫 STOP TOP PANEL WHEN ✏ EDITING

        sel = tree.selection()
        if not sel:
            return

        item = sel[0]
        vals = tree.item(item, "values")

        clear_top()

        global entry_pid, entry_barcode, entry_qty
        entry_pid = field(top_frame, "Product ID", 14)
        entry_barcode = field(top_frame, "Product Name", 22)
        entry_qty = field(top_frame, "Quantity", 10)

        entry_pid.insert(0, vals[1])
        entry_barcode.insert(0, vals[2])
        entry_qty.insert(0, vals[5])

        entry_qty.focus_set()
        entry_qty.bind("<KeyRelease>", live_qty_update)
        entry_qty.bind("<Return>", finish_qty_edit)

    def refresh_row_numbers():
        for i, item in enumerate(tree.get_children(), start=1):
            vals = list(tree.item(item, "values"))
            vals[0] = i
            tree.item(item, values=vals)


    def calculate_total():
        total = 0
        for item in tree.get_children():
            vals = tree.item(item, "values")
            total += float(vals[6])

        entry_total.delete(0, tk.END)
        entry_total.insert(0, f"{total:.2f}")


    # ✅ BIND MUST BE LAST
    tree.bind("<Button-1>", on_table_click)

    # default fields
    show_product_fields()


    def center_window(win, parent):
        win.update_idletasks()

        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        ww = win.winfo_width()
        wh = win.winfo_height()

        x = px + (pw // 2) - (ww // 2)
        y = py + (ph // 2) - (wh // 2)

        win.geometry(f"+{x}+{y}")


    # ===============================
    # DB CONNECTION
    # ===============================
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="billing",
            password="billing123",
            database="billing_db"
        )

    # ===============================
    # FETCH PRODUCT
    # ===============================
    def fetch_product(by):
        db = get_db()
        cur = db.cursor(dictionary=True)

        if by == "barcode":
            val = entry_barcode.get().strip()

            # ❌ EMPTY → STOP
            if not val:
                db.close()
                return None

            cur.execute("""
                SELECT *
                FROM products
                WHERE barcode1=%s
                OR barcode2=%s
                OR barcode3=%s
                OR product_name LIKE %s
                LIMIT 1
            """, (val, val, val, f"%{val}%"))

        else:
            pid = entry_pid.get().strip()

            # ❌ EMPTY → STOP
            if not pid:
                db.close()
                return None

            cur.execute(
                "SELECT * FROM products WHERE product_id=%s",
                (pid,)
            )

        row = cur.fetchone()
        db.close()
        return row
    
    def find_existing_row(product_id):
        for item in tree.get_children():
            vals = tree.item(item, "values")
            if str(vals[1]) == str(product_id):
                return item
        return None




    # ===============================
    # ADD PRODUCT TO BILL TABLE
    # ===============================
   

    def add_product(by):
        product = fetch_product(by)
 # ✅ ONLY product clear


        # ❌ PRODUCT NOT FOUND
        if not product:
            ask_add_product()
            return

        try:
            qty = int(entry_qty.get() or 1)
        except:
            qty = 1

        price = float(product["selling_price"])
        existing = find_existing_row(product["product_id"])

        if existing:
            vals = list(tree.item(existing, "values"))
            vals[5] = int(vals[5]) + qty
            vals[6] = vals[5] * price
            tree.item(existing, values=vals)
        else:
            tree.insert("", "end", values=(
                len(tree.get_children()) + 1,   # row_no
                product["product_id"],          # pid
                product["product_name"],        # name
                product["mrp_rate"],            # mrp
                price,                          # price
                qty,                            # qty
                qty * price,                    # amount
                "❌",                            # delete
                            "✏"                             # edit
            ))


        entry_barcode.delete(0, tk.END)
        entry_pid.delete(0, tk.END)
        entry_qty.delete(0, tk.END)
        entry_barcode.focus_set()
        recalc_total()


    def open_add_product_minimized(root, shop_id):

        if hasattr(root, "add_product_win") and root.add_product_win.winfo_exists():
            root.add_product_win.deiconify()
            root.add_product_win.lift()
            return

        win = tk.Toplevel(root)
        root.add_product_win = win

        win.title("Add Product")
        win.geometry("800x500")
        win.minsize(800, 500)
        win.transient(root)

        # ❌ DO NOT USE grab_set()

        topbar = tk.Frame(win, bg="#1E293B", height=36)
        topbar.pack(fill="x")

        tk.Label(
            topbar,
            text="Add Product",
            bg="#1E293B",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=10)

        tk.Button(topbar, text="—", command=win.withdraw,
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)

        tk.Button(topbar, text="▢", command=lambda: win.state("zoomed"),
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)

        tk.Button(topbar, text="✕", command=win.destroy,
                bg="#EF4444", fg="white", width=3).pack(side="right", padx=4)

        container = tk.Frame(win)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scroll.set,
                        xscrollcommand=h_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        open_add_product_window(scroll_frame, shop_id)

  

        # =============================
        # CUSTOM TOP BAR
        # =============================
        topbar = tk.Frame(win, bg="#1E293B", height=36)
        topbar.pack(fill="x")

        tk.Label(
            topbar,
            text="Add Product",
            bg="#1E293B",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=10)

        def hide_win():
            win.withdraw()

        def maximize_win():
            win.state("zoomed")

        def close_win():
            win.destroy()

        tk.Button(topbar, text="—", command=hide_win,
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)
        tk.Button(topbar, text="▢", command=maximize_win,
                bg="#334155", fg="white", width=3).pack(side="right", padx=4)
        tk.Button(topbar, text="✕", command=close_win,
                bg="#EF4444", fg="white", width=3).pack(side="right", padx=4)

        # =============================
        # SCROLLABLE BODY
        # =============================
        container = tk.Frame(win)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scroll.set,
                        xscrollcommand=h_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        # 🔥 IMPORTANT: load your EXISTING add product UI here
        open_add_product_window(scroll_frame, shop_id)

        center_window(win, root)



    def ask_add_product():
        popup = tk.Toplevel(root)
        popup.title("Product Not Found")
        popup.geometry("360x160")
        popup.resizable(False, False)
        popup.transient(root)
        popup.grab_set()

        tk.Label(
            popup,
            text="❌ Product not found",
            font=("Segoe UI", 12, "bold"),
            pady=25
        ).pack()

        tk.Label(
            popup,
            text="Please add product first",
            font=("Segoe UI", 10)
        ).pack()

        def close_popup(event=None):
            popup.destroy()
            entry_barcode.focus_set()

        tk.Button(
            popup,
            text="OK",
            width=12,
            bg="#2563EB",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=close_popup
        ).pack(pady=15)

        # 🔥 Enter / Esc key support
        popup.bind("<Return>", close_popup)
        popup.bind("<Escape>", close_popup)

        center_window(popup, root)

    
    def on_barcode_enter(event=None):
        if entry_barcode.get().strip() == "":
            return
        add_product("barcode")

    def on_pid_enter(event=None):
        if entry_pid.get().strip() == "":
            return
        add_product("pid")
    
  
    

    def confirm_qty_edit(event=None):
        global edit_mode, edit_item
        edit_mode = False
        edit_item = None
        show_product_fields()


    def recalc_total():
        total = 0.0
        for item in tree.get_children():
            vals = tree.item(item, "values")
            try:
                total += float(vals[6])  # amount column
            except:
                pass

        entry_total.delete(0, tk.END)
        entry_total.insert(0, f"{total:.2f}")

    # ===============================
    # LIVE QTY UPDATE
    # ===============================
    def live_qty_update(event=None):
        sel = tree.selection()
        if not sel:
            return
        try:
            qty = int(entry_qty.get())
        except:
            return

        item = sel[0]
        vals = list(tree.item(item, "values"))
        vals[5] = qty
        vals[6] = qty * float(vals[4])
        tree.item(item, values=vals)
        calculate_total()   # 🔥 TOTAL LIVE UPDATE




    tree.column("name", width=220)
    tree.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", on_row_select)



    bottom = tk.Frame(card, bg="white")
    bottom.pack(side="bottom", fill="x", padx=20, pady=12)


    def finish_qty_edit(event=None):
        calculate_total()              # 🔥 FINAL TOTAL UPDATE
        tree.selection_remove(tree.selection())
        show_product_fields()          # back to barcode / pid / qty
                # back to add product mode
  

    def total_box(parent, text):
        f = tk.Frame(parent, bg="white")

        lbl = tk.Label(
            f,
            text=text,
            bg="white",
            fg=TITLE_COLOR,
            font=("Segoe UI", 12, "bold")
        )
        lbl.pack(anchor="e")

        e = tk.Entry(
            f,
            width=16,
            font=("Segoe UI", 12, "bold"),
            bg="#BDC9D4",
            fg="black",
            relief="solid",
            bd=1,
            justify="right"
        )
        e.pack()

        return f, lbl, e

    box_total,  lbl_total,  entry_total  = total_box(bottom, "TOTAL")
    box_give,   lbl_give,   entry_give   = total_box(bottom, "Customer Give")
    box_return, lbl_return, entry_return = total_box(bottom, "Return")

    box_return.pack(side="right", padx=12)
    box_give.pack(side="right", padx=12)
    box_total.pack(side="right", padx=12)

    def validate_given_against_total(event=None):
        try:
            total_text = entry_total.get().strip()
            give_text = entry_give.get().strip()

            if total_text == "" or give_text == "":
                stop_blink(entry_give, lbl_give)
                return

            total = float(total_text)
            given = float(give_text)

            if given < total:
                start_blink(entry_give, lbl_give)
            else:
                stop_blink(entry_give, lbl_give)

        except ValueError:
            start_blink(entry_give, lbl_give)

    # =============================
    # BLINK ERROR
    # =============================
    def start_blink(entry, label):
        global blink_running

        if blink_running:
            return  # already blinking

        blink_running = True

        def blink():
            if not blink_running:
                entry.config(bg="#D4D5E3")
                label.config(fg=TITLE_COLOR)
                return

            current = entry.cget("bg")
            new = "red" if current != "red" else "#CBD3DC"

            entry.config(bg=new)
            label.config(fg=new)

            entry.after(300, blink)

        blink()


    def stop_blink(entry, label):
        global blink_running
        blink_running = False
        entry.config(bg="#C8C8DC")
        label.config(fg=TITLE_COLOR)




    # =============================
    # CALCULATE RETURN
    # =============================
    def calculate_return(event=None):
        try:
            total_text = entry_total.get().strip()
            give_text = entry_give.get().strip()

            if total_text == "" or give_text == "":
                entry_return.delete(0, tk.END)
                stop_blink(entry_give, lbl_give)
                return

            total = float(total_text)
            given = float(give_text)

            # ❌ INVALID → BLINK
            if given < 0 or given < total:
                entry_return.delete(0, tk.END)
                start_blink(entry_give, lbl_give)
                return

            # ✅ VALID (THIS IS WHAT YOU WANT)
            # total == given  OR  given > total
            stop_blink(entry_give, lbl_give)

            ret = given - total
            entry_return.delete(0, tk.END)
            entry_return.insert(0, f"{ret:.2f}")
            entry_return.focus_set()

        except ValueError:
            entry_return.delete(0, tk.END)
            start_blink(entry_give, lbl_give)

    entry_total.bind("<Return>", lambda e: entry_give.focus_set())

    entry_give.bind("<KeyRelease>", calculate_return)
    entry_give.bind("<Return>", calculate_return)
    entry_total.bind("<KeyRelease>", validate_given_against_total)
    entry_total.bind("<FocusOut>", validate_given_against_total)


    entry_total.focus_set()

    def is_printer_connected():
        try:
            out = subprocess.check_output(["lpstat", "-r"], stderr=subprocess.STDOUT)
            text = out.decode().lower()

            # scheduler must be running
            if "scheduler is running" not in text:
                return False

            # check at least one enabled printer
            out2 = subprocess.check_output(["lpstat", "-p"], stderr=subprocess.STDOUT)
            lines = out2.decode().lower().splitlines()

            for line in lines:
                if "enabled" in line:
                    return True

            return False
        except:
            return False

    def save_and_print(event=None):

        # -----------------------------
        # 1️⃣ PRODUCT CHECK
        # -----------------------------
        if len(tree.get_children()) == 0:
            messagebox.showwarning("Add Product", "Please add product")
            return

        # -----------------------------
        # 2️⃣ TOTAL / GIVEN / RETURN
        # -----------------------------
        try:
            total = float(entry_total.get().strip())
            given = float(entry_give.get().strip())
            ret   = float(entry_return.get().strip())
        except:
            messagebox.showwarning("Missing Amount", "Enter Total / Given / Return")
            return

        if total <= 0:
            messagebox.showwarning("Invalid Bill", "Bill total is zero")
            return

        if given < total:
            messagebox.showwarning("Payment Incomplete", "Given amount is less than total")
            return

        # -----------------------------
        # 3️⃣ COLLECT ITEMS
        # -----------------------------
        items = []

        for i, row in enumerate(tree.get_children(), start=1):
            vals = tree.item(row, "values")

            product_name = vals[2]
            mrp          = float(vals[3])
            price        = float(vals[4])
            qty          = int(vals[5])
            amount       = float(vals[6])

            items.append((i, product_name, mrp, price, qty, amount))

        # -----------------------------
        # 4️⃣ SAVE TO bill_estimates ONLY
        # -----------------------------
        conn = get_db()
        cur = conn.cursor()

        estimate_no = datetime.now().strftime("EST-%Y%m%d-%H%M%S")

        for sno, name, mrp, price, qty, amount in items:
            cur.execute("""
                INSERT INTO bill_estimates (
                    estimate_no,
                    sno,
                    product_name,
                    mrp,
                    price,
                    qty,
                    amount,
                    total_amount,
                    given_amount,
                    return_amount
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                estimate_no,
                sno,
                name,
                mrp,
                price,
                qty,
                amount,
                total,
                given,
                ret
            ))

        conn.commit()
        conn.close()

        # -----------------------------
        # 5️⃣ ESTIMATE POPUP
        # -----------------------------
        def show_printer_popup():
            popup = tk.Toplevel(root)
            popup.title("Estimate Ready")
            popup.resizable(False, False)
            popup.transient(root)
            popup.grab_set()

            w, h = 380, 190
            x = root.winfo_rootx() + (root.winfo_width() // 2) - (w // 2)
            y = root.winfo_rooty() + (root.winfo_height() // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")

            frame = tk.Frame(
                popup,
                bg="white",
                highlightbackground="#0EA5E9",
                highlightthickness=2
            )
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            tk.Label(
                frame,
                text="🧾 BILL ESTIMATE SAVED",
                fg="#0EA5E9",
                bg="white",
                font=("Segoe UI", 13, "bold")
            ).pack(pady=(25, 6))

            tk.Label(
                frame,
                text=f"Estimate No : {estimate_no}",
                fg="#111827",
                bg="white",
                font=("Segoe UI", 10, "bold")
            ).pack(pady=(0, 6))

            tk.Label(
                frame,
                text="Printer connect pannina print eduthukalaam",
                fg="#374151",
                bg="white",
                font=("Segoe UI", 10)
            ).pack(pady=(0, 15))

            tk.Button(
                frame,
                text="OK",
                width=10,
                bg="#0EA5E9",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                command=popup.destroy
            ).pack()

            popup.bind("<Return>", lambda e: popup.destroy())
            popup.bind("<Escape>", lambda e: popup.destroy())

        root.after(100, show_printer_popup)

        # -----------------------------
        # 6️⃣ CLEAR UI (IMPORTANT 🔥)
        # -----------------------------
        tree.delete(*tree.get_children())

        for w in (entry_total, entry_give, entry_return):
            try:
                w.delete(0, "end")
            except:
                pass

        # optional customer fields clear
        for name in ("entry_cid", "entry_cname", "entry_phone", "entry_address", "entry_points"):
            if name in globals():
                try:
                    globals()[name].delete(0, "end")
                except:
                    pass


    root.bind("<Shift-Return>", save_and_print)


def open_transaction_page(workspace,shop_id):
    import tkinter as tk
    from tkinter import ttk
    from tkcalendar import DateEntry
    from datetime import datetime
    import mysql.connector

    WORK_BG = "#F8FAFC"
    search_active = False
    last_search_keyword = ""

    def set_search_active(val):
        nonlocal search_active
        search_active = val

    def set_last_keyword(val):
        nonlocal last_search_keyword
        last_search_keyword = val


    # ---------------- CLEAR WORKSPACE ----------------
    for w in workspace.winfo_children():
        w.destroy()
    workspace.configure(bg=WORK_BG)

    # ---------------- DB ----------------
    def get_db():
        return mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",
            database="billing_db"
        )

    # ---------------- FIXED BOX ----------------
    def fixed_box(parent, w, h):
        box = tk.Frame(parent, width=w, height=h, bg="white")
        box.pack_propagate(False)
        box.pack(side="left", padx=6)
        return box

    # ---------------- MAIN CARD ----------------
    main = tk.Frame(
        workspace,
        bg="white",
        highlightbackground="#0EA5E9",
        highlightthickness=2
    )
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------- TITLE ----------------
    tk.Label(
        main,
        text="Banks",
        font=("Segoe UI", 14, "bold"),
        fg="#0EA5E9",
        bg="white"
    ).pack(pady=(15, 10))

    # =================================================
    # ACTION ROW
    # =================================================
    action_row = tk.Frame(main, bg="white")
    action_row.pack(fill="x", padx=15, pady=(0, 12))


    def apply_search_highlight():
        for item in tree.get_children():
            values = tree.item(item, "values")

            # Income row full text
            row_text = " ".join(str(v).lower() for v in values)

            if last_search_keyword in row_text:
                tree.item(item, tags=("match",))
                tree.see(item)



    def search_and_highlight(event=None):
        keyword = search_var.get().strip().lower()

        # Empty search → reset
        if not keyword:
            set_search_active(False)
            set_last_keyword("")
            restore_zebra()
            return

        set_search_active(True)
        set_last_keyword(keyword)

        # Reset zebra first
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

        # Apply highlight safely
        tree.after_idle(apply_search_highlight)



    
    # ---------------- SEARCH ----------------
    tk.Label(
        action_row, text="Search",
        bg="white", fg="black",
        font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        action_row,
        textvariable=search_var,
        width=22,
        bg="white",
        fg="black",
        insertbackground="black",
        relief="solid", bd=1
    )
    search_entry.pack(side="left", padx=(6, 12))

    search_entry.bind("<Return>", search_and_highlight)

    search_entry.focus_set()


    
    


    # ---------------- ADD EXPENSE BUTTON ----------------
    box_add = fixed_box(action_row, 140, 30)

    btn_add_expense = tk.Button(
        box_add,
        text="➕ Add Banks",
        bg="#0EA5E9",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=lambda: open_add_bank_window(workspace, shop_id, bank_id=None)
    )

    btn_add_expense.pack(fill="both", expand=True)


    # ---------------- FROM DATE ----------------
    box_from = fixed_box(action_row, 150, 30)
    tk.Label(box_from, text="From", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    start_date = DateEntry(
        box_from,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    start_date.pack(side="left")

    # ---------------- TO DATE ----------------
    box_to = fixed_box(action_row, 150, 30)
    tk.Label(box_to, text="To", bg="black", fg="white",
             font=("Segoe UI", 8)).pack(side="left", padx=4)

    end_date = DateEntry(
        box_to,
        width=10,
        date_pattern="dd-mm-yyyy",
        maxdate=datetime.today().date()
    )
    end_date.set_date(datetime.today().date())
    end_date.pack(side="left")

    # ---------------- APPLY / CLEAR ----------------
    box_apply = fixed_box(action_row, 90, 30)

    date_filter_active = False

   # ---------------- TABLE FRAME ----------------
    # ---------------- TRANSACTION TABLE FRAME ----------------
    table_frame = tk.Frame(main, bg="white")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    columns = (
        "bill_no",
        "customer_name",
        "phone",
        "type",
        "total",
        "given",
        "return",
        "status",
        "date",
        "time",
        "delete",        # 🗑 delete button
        "id"             # 🔒 hidden transaction_id
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=12
    )

    # ---------------- TAG COLORS ----------------
    tree.tag_configure("even", background="#EEF2F7")
    tree.tag_configure("odd", background="#FFFFFF")
    tree.tag_configure("paid", background="#BBF7D0")     # green
    tree.tag_configure("unpaid", background="#FECACA")   # red

    # ---------------- HEADERS ----------------
    headers = [
        "Bill No",
        "Customer Name",
        "Phone",
        "Type",
        "Bill Total",
        "Given",
        "Return",
        "Status",
        "Date",
        "Time",
        "Delete"
    ]

    for c, h in zip(columns, headers):
        tree.heading(c, text=h)

    # ---------------- COLUMN WIDTHS ----------------
    tree.column("bill_no", width=100, anchor="center")
    tree.column("customer_name", width=160, anchor="w")
    tree.column("phone", width=120, anchor="center")

    tree.column("type", width=90, anchor="center")

    tree.column("total", width=120, anchor="e")
    tree.column("given", width=120, anchor="e")
    tree.column("return", width=120, anchor="e")

    tree.column("status", width=100, anchor="center")

    tree.column("date", width=110, anchor="center")
    tree.column("time", width=100, anchor="center")

    tree.column("delete", width=70, anchor="center")
    tree.column("id", width=0, stretch=False)   # 🔒 hidden

    tree.pack(fill="both", expand=True)

    # ---------------- SCROLLBARS ----------------
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

     # =================================================
    # TOTAL SUMMARY BAR (BELOW TABLE)
    # =================================================
    summary_bar = tk.Frame(main, bg="#F1F5F9", height=40)
    summary_bar.pack(fill="x", padx=15, pady=(0, 12))

    summary_bar.pack_propagate(False)

    lbl_total = tk.Label(
        summary_bar,
        text="Total : ₹0",
        bg="#F1F5F9",
        fg="black",
        font=("Segoe UI", 10, "bold")
    )
    lbl_total.pack(side="left", padx=20)

    lbl_cash = tk.Label(
        summary_bar,
        text="Cash : ₹0",
        bg="#F1F5F9",
        fg="#16A34A",
        font=("Segoe UI", 10, "bold")
    )
    lbl_cash.pack(side="left", padx=20)

    lbl_credit = tk.Label(
        summary_bar,
        text="Credit : ₹0",
        bg="#F1F5F9",
        fg="#DC2626",
        font=("Segoe UI", 10, "bold")
    )
    lbl_credit.pack(side="left", padx=20)

    def update_bank_totals():
        total = 0
        cash_total = 0
        other_total = 0

        for item in tree.get_children():
            values = tree.item(item, "values")

            # safety
            if len(values) < 9:
                continue

            # ✅ CURRENT BALANCE (index 6)
            bal_str = str(values[6]).replace("₹", "").replace(",", "").strip()
            try:
                bal = float(bal_str)
            except:
                bal = 0

            # ✅ BANK TYPE (index 4)
            bank_type = str(values[4]).lower().strip()

            total += bal

            if bank_type == "cash":
                cash_total += bal
            else:
                other_total += bal

        lbl_total.config(text=f"Total : ₹{total:,.0f}")
        lbl_cash.config(text=f"Cash : ₹{cash_total:,.0f}")
        lbl_credit.config(text=f"Other : ₹{other_total:,.0f}")



    update_bank_totals()


   
   # =================================================
    # LOAD TRANSACTIONS (SINGLE FUNCTION)
    # =================================================
    def load_transactions(search="", from_dt=None, to_dt=None):
        tree.delete(*tree.get_children())

        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT
                transaction_id,
                bill_no,
                customer_name,
                customer_phone,
                transaction_type,
                bill_total,
                amount_given,
                return_amount,
                status,
                trans_date,
                trans_time
            FROM transactions
            WHERE 1=1
        """

        params = []

        # 🔍 SEARCH
        if search:
            query += """
                AND (
                    bill_no LIKE %s OR
                    customer_name LIKE %s OR
                    customer_phone LIKE %s OR
                    transaction_type LIKE %s OR
                    status LIKE %s
                )
            """
            s = f"%{search}%"
            params.extend([s, s, s, s, s])

        # 📅 DATE FILTER
        if from_dt and to_dt:
            query += " AND trans_date BETWEEN %s AND %s"
            params.extend([from_dt, to_dt])

        query += " ORDER BY transaction_id DESC"

        cur.execute(query, tuple(params))

        for i, r in enumerate(cur.fetchall()):

            # status based color
            tag = "paid" if r[8] == "PAID" else "unpaid"

            tree.insert(
                "",
                "end",
                values=(
                    r[1],                       # bill no
                    r[2],                       # customer name
                    r[3],                       # phone
                    r[4],                       # CASH / CREDIT
                    f"₹{r[5]:,.2f}",            # total
                    f"₹{r[6]:,.2f}",            # given
                    f"₹{r[7]:,.2f}",            # return
                    r[8],                       # status
                    r[9].strftime("%d-%m-%Y"),  # date
                    r[10],                      # time
                    "🗑",                       # delete
                    r[0]                        # 🔒 transaction_id
                ),
                tags=(tag,)
            )

        conn.close()

        update_bank_totals()


        


    def delete_bank(bank_id):
        if not messagebox.askyesno("Confirm", "Delete this bank?"):
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM banks WHERE bank_id=%s", (bank_id,))
        conn.commit()
        conn.close()

        load_transactions()


      


    def on_tree_click(event):
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id:
            return

        # 🗑 DELETE column = #12
        if col_id == "#12":
            values = tree.item(row_id, "values")

            if len(values) < 13:
                return

            bank_id = values[12]   # 🔒 hidden bank_id
            delete_bank(bank_id)


    tree.bind("<Button-1>", on_tree_click)
    load_transactions()

   # ---------------- ZEBRA RESTORE ----------------
    def restore_zebra():
        for i, item in enumerate(tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.item(item, tags=(tag,))

    tree.tag_configure("even", background="#F8FAFC")
    tree.tag_configure("odd", background="#EEF2F7")

    # ---------------- INLINE EDIT ----------------
    edit_entry = None

    def on_double_click(event):
        global edit_entry

        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        # ❌ Delete & hidden ID editable illa
        if not row_id or col in ("#12", "#13"):
            return

        x, y, w, h = tree.bbox(row_id, col)
        value = tree.set(row_id, col)

        edit_entry = tk.Entry(tree, bg="white", fg="black", relief="solid", bd=1)
        edit_entry.place(x=x, y=y, width=w, height=h)

        # ₹ strip pannitu show
        edit_entry.insert(0, value.replace("₹", "").replace(",", ""))
        edit_entry.focus()

        def save_edit(event=None):
            new_val = edit_entry.get().strip()
            edit_entry.destroy()

            if not new_val:
                restore_zebra()
                return

            # 🔥 Numeric columns (Opening / Current Balance)
            if col in ("#6", "#7"):
                try:
                    new_val_fmt = f"₹{float(new_val):,.2f}"
                except:
                    new_val_fmt = "₹0.00"
                tree.set(row_id, col, new_val_fmt)
            else:
                tree.set(row_id, col, new_val)

            update_bank_db(row_id, col, new_val)

            update_bank_totals()   # ✅ LIVE TOTAL UPDATE

            restore_zebra()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())


    tree.bind("<Double-1>", on_double_click)

    bank_col_map = {
        "#1": "bank_name",
        "#2": "account_holder",
        "#3": "account_no",
        "#4": "ifsc_code",
        "#5": "bank_type",
        "#6": "opening_balance",     # 🔥 numeric
        "#7": "current_balance",     # 🔥 numeric
        "#8": "remarks",
        "#9": "status"
    }



    def clean_numeric(val):
        return val.replace("₹", "").replace(",", "").strip()


    # ---------------- UPDATE DB ----------------
    def update_bank_db(row_id, col, value):
        db_col = bank_col_map.get(col)
        if not db_col:
            return

        bank_id = tree.item(row_id)["values"][-1]  # 🔒 bank_id

        # Numeric cleanup
        if db_col in ("opening_balance", "current_balance"):
            value = clean_numeric(value)
            try:
                value = float(value)
            except:
                value = 0

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE banks
            SET {db_col}=%s
            WHERE bank_id=%s
            """,
            (value, bank_id)
        )

        conn.commit()
        conn.close()



    # ---------------- APPLY / CLEAR LOGIC ----------------
    date_filter_active = False

    def toggle_date_filter():
        nonlocal date_filter_active

        if not date_filter_active:
            # ✅ DateEntry → DATE object
            from_date = start_date.get_date()
            to_date   = end_date.get_date()

            load_transactions(
                search=search_var.get().strip(),
                from_dt=from_date,
                to_dt=to_date
            )

            btn_apply.config(text="Clear", bg="#dc2626")
            date_filter_active = True

        else:
            load_transactions(search=search_var.get().strip())
            btn_apply.config(text="🔍 Apply", bg="#192987")
            date_filter_active = False


    btn_apply = tk.Button(
        box_apply,
        text="🔍 Apply",
        bg="#192987",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        command=toggle_date_filter
    )
    btn_apply.pack(fill="both", expand=True)


    # ---------------- SEARCH BIND ----------------
    search_entry.bind(
        "<KeyRelease>",
        lambda e: load_transactions(search=search_var.get().strip())
    )

    # ---------------- INITIAL LOAD ----------------
    load_transactions()


import tkinter as tk
from tkinter import ttk

# -----------------------------
# TRENDING COLORS & FONT
# -----------------------------
TOP_BG = "#0F172A"
TOP_BTN_BG = "#1E293B"
TOP_BTN_HOVER = "#334155"

SIDEBAR_BG = "#EAF6FF"        # very light sky background
SIDEBAR_BTN_BG = "#BEE7FF"    # lite sky blue
SIDEBAR_BTN_HOVER = "#8FD3FF" # hover sky blue
TITLE_COLOR = "#003A5C"       # dark blue text


WORK_BG = "#F4F4F4"
ACCENT = "#25D1EB"
TITLE_COLOR = "#0F172A"

BUTTON_FONT = ("Helvetica", 13, "bold")
TITLE_FONT = ("Helvetica", 28, "bold")
WELCOME_FONT = ("Helvetica", 22, "bold")

# -----------------------------
# HOVER EFFECT
# -----------------------------
def apply_hover(widget, normal_color, hover_color):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_color))
    widget.bind("<Leave>", lambda e: widget.config(bg=normal_color))


# -----------------------------
# MAIN DASHBOARD
# -----------------------------
def show_dashboard(root, shop_id, owner_name):

    dash = tk.Toplevel(root)
    dash.title("Dashboard - Sri Krishna Department Store")
    dash.configure(bg=WORK_BG)

    try:
        dash.state("zoomed")
    except:
        dash.attributes("-zoomed", True)

    # =============================
    # FILE DROPDOWN STATE (ONLY ONE)
    # =============================
    file_dropdown = {"frame": None}

    def on_dash_close():
        root.deiconify()
        dash.destroy()

    dash.protocol("WM_DELETE_WINDOW", on_dash_close)

    # =============================
    # TITLE
    # =============================
    tk.Label(
        dash,
        text="Sri Krishna Department Store",
        font=TITLE_FONT,
        bg=WORK_BG,
        fg=ACCENT
    ).pack(pady=15)

    # =============================
    # BODY
    # =============================
    body = tk.Frame(dash, bg=WORK_BG)
    body.pack(fill="both", expand=True)

    body.grid_columnconfigure(0, weight=0)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=0)
    body.grid_rowconfigure(1, weight=1)

    # =============================
    # SIDEBAR
    # =============================
    sidebar = tk.Frame(
        body, bg=SIDEBAR_BG, width=220,
        highlightbackground=ACCENT, highlightthickness=3
    )
    sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")
    sidebar.grid_propagate(False)

    def side_btn(text, cmd):
        b = tk.Label(
            sidebar, text=text, font=BUTTON_FONT,
            bg=SIDEBAR_BTN_BG, fg=TITLE_COLOR,
            padx=12, pady=14, cursor="hand2"
        )
        b.pack(fill="x", pady=10, padx=12)
        b.bind("<Button-1>", lambda e: cmd())
        apply_hover(b, SIDEBAR_BTN_BG, SIDEBAR_BTN_HOVER)

    side_btn("Billing", lambda:open_billing_window(workspace,shop_id))
    side_btn("Add Product", lambda: open_add_product_window(workspace, shop_id))

    side_btn("Update Product", lambda: open_update_product_window(workspace, shop_id))

    side_btn("Offer",lambda:open_offer_window(workspace, shop_id)),
    side_btn("Exit", on_dash_close)

    # =============================
    # TOP MENU
    # =============================
    top_menu = tk.Frame(body, bg=TOP_BG, height=44)
    top_menu.grid(row=0, column=1, sticky="ew")
    top_menu.grid_propagate(False)

    # =============================
    # ACTIONS
    # =============================
    def do_logout():
        on_dash_close()

    # =============================
    # FILE DROPDOWN MENU (STABLE)
    # =============================
    file_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    file_menu.add_command(
        label="Change Passwor",
        command=lambda: print("Change Password")
    )

    file_menu.add_command(
        label="Settings",
        command=lambda: print("Settings")
    )

    file_menu.add_command(
        label="User Info",
        command=lambda: print("User Info")
    )

    file_menu.add_separator()

    file_menu.add_command(
        label="Logout",
        command=lambda: on_dash_close()
    )
  
    # =============================
    # BOSS 1 DROPDOWN MENU
    # =============================
    boss1_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    boss1_menu.add_command(
        label="Product",
        command=lambda: open_product_details_page(workspace,shop_id)
    )
    boss1_menu.add_command(
        label="Customer",
        command=lambda: open_customer_window(workspace, shop_id)
    )
    boss1_menu.add_command(
        label="Suppliers",
        command=lambda: open_suppliers(workspace,shop_id)
    )
    boss1_menu.add_command(
        label="Staff",
        command=lambda: open_staff(workspace, shop_id)
    )
    boss1_menu.add_command(
        label="Admin",
        command=lambda: open_admin(workspace, shop_id)
    )
    boss1_menu.add_separator()
    boss1_menu.add_command(
        label="Shop Details",
        command=lambda: open_shop_details(workspace)
    )
    # boss1_menu.add_command(
    #     label="Product Update",
    #     command=lambda: print("Product Update")
    # )
    # boss1_menu.add_command(
    #     label="Bulk Update",
    #     command=lambda: print("Bulk Update")
    # )


    # =============================
    # BOSS 2 DROPDOWN MENU
    # =============================
    boss2_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    boss2_menu.add_command(
        label="Expenses",
        command=lambda: open_expenses_page(workspace,shop_id)
    )
    boss2_menu.add_command(
        label="Income",
        command=lambda: open_income_page(workspace,shop_id)
    )
    boss2_menu.add_command(
        label="Banks",
        command=lambda: open_banks_page(workspace,shop_id)
    )
    boss2_menu.add_command(
        label="Taxes",
        command=lambda: open_taxes_page(workspace,shop_id)
    )
    boss2_menu.add_command(
        label="Categories",
        command=lambda: open_categories_page(workspace,shop_id)
    )
   # transaction options  

    transaction_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    transaction_menu.add_command(label="Purchase", command=lambda: open_purchase_page(workspace,shop_id))
    transaction_menu.add_command(label="Sales", command=lambda: open_sales_page(workspace,shop_id))
    transaction_menu.add_command(label="Estimate Bill", command=lambda: open_Estimate_bill_window(workspace,shop_id))
    transaction_menu.add_command(label="Points Use", command=lambda: print("Points Use"))
    transaction_menu.add_command(label="Transaction Customer", command=lambda: open_transaction_page(workspace,shop_id))
    transaction_menu.add_command(label="Barcode Print", command=lambda: print("Barcode Print"))
    transaction_menu.add_command(label="Transaction Supplies", command=lambda: print("Transaction Supplies"))
    transaction_menu.add_command(label="Bank Billing", command=lambda: print("Bank Billing"))
    transaction_menu.add_command(label="Income Billing", command=lambda: print("Income Billing"))
    transaction_menu.add_command(label="Expense Billing", command=lambda: print("Expense Billing"))
    transaction_menu.add_command(label="Convert To Tax", command=lambda: print("Convert To Tax"))


    # stock options

    stock_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    stock_menu.add_command(
        label="Stock Management",
        command=lambda: print("Stock Management")
    )

    # reports options

    report_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    report_menu.add_command(label="Auditor Report", command=lambda: print("Auditor Report"))
    report_menu.add_command(label="Tax Invoice Report", command=lambda: print("Tax Invoice Report"))
    report_menu.add_command(label="Sales Report Estimate", command=lambda: print("Sales Report Estimate"))
    report_menu.add_command(label="Purchase Report Estimate", command=lambda: print("Purchase Report Estimate"))
    report_menu.add_command(label="Purchase Report", command=lambda: print("Purchase Report"))
    report_menu.add_command(label="Points Use Report", command=lambda: print("Points Use Report"))
    report_menu.add_command(label="Customer Bill Report", command=lambda: print("Customer Bill Report"))
    report_menu.add_command(label="Customer Balance Report", command=lambda: print("Customer Balance Report"))
    report_menu.add_command(label="Product Sales Details", command=lambda: print("Product Sales Details"))
    report_menu.add_command(label="Total Report", command=lambda: print("Total Report"))
    report_menu.add_command(label="Profit And Loss Report", command=lambda: print("Profit And Loss Report"))
    report_menu.add_command(label="Bill Type Report", command=lambda: print("Bill Type Report"))
    report_menu.add_command(label="Min Qty Alert", command=lambda: print("Min Qty Alert"))

    # transactions report options
    transaction_report_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    transaction_report_menu.add_command(label="Bank Report", command=lambda: print("Bank Report"))
    transaction_report_menu.add_command(label="Income Report", command=lambda: print("Income Report"))
    transaction_report_menu.add_command(label="Expense Report", command=lambda: print("Expense Report"))
    transaction_report_menu.add_command(label="Transaction Customer", command=lambda: print("Transaction Customer"))
    transaction_report_menu.add_command(label="Transaction Income", command=lambda: print("Transaction Income"))
    transaction_report_menu.add_command(label="Transaction Supplies", command=lambda: print("Transaction Supplies"))



    # others menu options 

    others_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    others_menu.add_command(label="Search", command=lambda: print("Search"))
    others_menu.add_command(label="Backup", command=lambda: print("Backup"))
    others_menu.add_command(label="Restore", command=lambda: print("Restore"))
    others_menu.add_command(label="Backup Settings", command=lambda: print("Backup Settings"))
    others_menu.add_command(label="Shortcut Keys", command=lambda: print("Shortcut Keys"))
    others_menu.add_command(label="Barcode Settings", command=lambda: print("Barcode Settings"))
    others_menu.add_command(label="Hide Side Bar", command=lambda: print("Hide Side Bar"))

    # help menu options 

    help_menu = tk.Menu(dash, tearoff=0, bg="white", fg="black")

    help_menu.add_command(
        label="Contact",
        command=lambda: print("Contact")
    )


    # =============================
    # TOP BUTTONS
    # =============================
    menu_items = [
        ("FILE", None),
        ("BOSS 1", None),
        ("BOSS 2", None),
        ("TRANSACTION",None),
        ("STOCK", None),
        ("REPORT", None),
        ("TRANSACTION REPORT", None),
        ("OTHERS", None),
        ("HELP", None)
    ]

    for text, cmd in menu_items:
        btn = tk.Label(
            top_menu,
            text=text,
            font=("Helvetica", 11, "bold"),
            bg=TOP_BTN_BG,
            fg="white",
            padx=26 if text in ("FILE", "BOSS 1", "BOSS 2") else 14,
            pady=4,
            cursor="hand2"
        )
        btn.pack(side="left", padx=4, pady=6)

        if text == "FILE":
            btn.bind(
                "<Button-1>",
                lambda e, b=btn: file_menu.tk_popup(
                    b.winfo_rootx(),
                    b.winfo_rooty() + b.winfo_height()
                )
            )
        
        elif text == "BOSS 1":
            btn.bind(
                "<Button-1>",
                lambda e, b=btn: boss1_menu.tk_popup(
                    b.winfo_rootx(),
                    b.winfo_rooty() + b.winfo_height()
                )
            )


        elif text == "BOSS 2":
            btn.bind(
                "<Button-1>",
                lambda e, b=btn: boss2_menu.tk_popup(
                    b.winfo_rootx(),
                    b.winfo_rooty() + b.winfo_height()
                )
            )

        elif text == "TRANSACTION":
            btn.bind("<Button-1>", lambda e, b=btn:
                transaction_menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
            )

        elif text == "STOCK":
            btn.bind("<Button-1>", lambda e, b=btn:
                stock_menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
            )

        elif text == "REPORT":
            btn.bind("<Button-1>", lambda e, b=btn:
                report_menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
            )

        elif text == "TRANSACTION REPORT":
            btn.bind("<Button-1>", lambda e, b=btn:
                transaction_report_menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
            )

        elif text == "OTHERS":
            btn.bind("<Button-1>", lambda e, b=btn:
                others_menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
            )

        elif text == "HELP":
            btn.bind("<Button-1>", lambda e, b=btn:
                help_menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())
            )
    # =============================
    # WORKSPACE
    # =============================
    workspace = tk.Frame(body, bg=WORK_BG)
    workspace.grid(row=1, column=1, sticky="nsew")

    card = tk.Frame(
        workspace, bg="white",
        highlightbackground=ACCENT,
        highlightthickness=3,
        padx=50, pady=50
    )
    card.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        card,
        text="Welcome to Dashboard",
        font=WELCOME_FONT,
        fg=ACCENT,
        bg="white"
    ).pack()



        # -----------------------------
    # LOGOUT FUNCTION
    # -----------------------------
    def do_logout():
        try:
            dash.destroy()
            root.deiconify()
        except:
            pass

    def toggle_file_menu(widget):
        # if already open → close
        if show_dashboard.file_menu and show_dashboard.file_menu.winfo_exists():
            show_dashboard.file_menu.destroy()
            show_dashboard.file_menu = None
            return

        # create popup
        fm = tk.Frame(
            dash,
            bg="#FFFFFF",
            highlightbackground=ACCENT,
            highlightthickness=2
        )

        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        fm.place(x=x, y=y)

        logout_btn = tk.Label(
            fm,
            text="Logout",
            font=("Helvetica", 11, "bold"),
            bg="#FFFFFF",
            fg="red",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        logout_btn.pack(fill="x")
        logout_btn.bind("<Button-1>", lambda e: do_logout())
        apply_hover(logout_btn, "#FFFFFF", "#FEE2E2")

        show_dashboard.file_menu = fm

        for text, cmd in menu_items:
            btn = tk.Label(
                top_menu,
                text=text,
                font=("Helvetica", 11, "bold"),
                bg=TOP_BTN_BG,
                fg="white",
                padx=14,
                pady=4,
                bd=0,
                cursor="hand2"
            )
            btn.pack(side="left", padx=4, pady=6)

            if text == "FILE":
                btn.bind("<Button-1>", lambda e, b=btn: toggle_file_menu(b))
            else:
                btn.bind("<Button-1>", lambda e, c=cmd: c())

            apply_hover(btn, TOP_BTN_BG, TOP_BTN_HOVER)


def login_window():
    root = tk.Tk()
    root.title("Login - Billing System")
    root.configure(bg=WORK_BG)
    center_window(root, 520, 380)

    # =============================
    # TITLE
    # =============================
    tk.Label(
        root,
        text="SRI KRISHNA DEPARTMENT STORE",
        bg=WORK_BG,
        fg=ACCENT,
        font=("Segoe UI", 18, "bold")
    ).pack(pady=(25, 5))

    tk.Label(
        root,
        text="Billing Management System",
        bg=WORK_BG,
        fg=TITLE_COLOR,
        font=("Segoe UI", 11)
    ).pack(pady=(0, 20))

    # =============================
    # CARD
    # =============================
    card = tk.Frame(
        root,
        bg="white",
        padx=45,
        pady=35
    )
    card.pack()

    card.config(highlightbackground="#D1D5DB", highlightthickness=1)

    # =============================
    # USERNAME
    # =============================
    tk.Label(
        card,
        text="Username",
        bg="white",
        fg="#374151",
        font=("Segoe UI", 11)
    ).grid(row=0, column=0, sticky="w")

    entry_user = tk.Entry(
        card,
        width=32,
        font=("Segoe UI", 11),
        bg="#F9FAFB",
        fg=TITLE_COLOR,
        relief="solid",
        bd=1,
        insertbackground=TITLE_COLOR
    )
    entry_user.grid(row=1, column=0, pady=(6, 18), ipady=6)

    # =============================
    # PASSWORD
    # =============================
    tk.Label(
        card,
        text="Password",
        bg="white",
        fg="#374151",
        font=("Segoe UI", 11)
    ).grid(row=2, column=0, sticky="w")

    entry_pass = tk.Entry(
        card,
        show="*",
        width=32,
        font=("Segoe UI", 11),
        bg="#F9FAFB",
        fg=TITLE_COLOR,
        relief="solid",
        bd=1,
        insertbackground=TITLE_COLOR
    )
    entry_pass.grid(row=3, column=0, pady=(6, 25), ipady=6)

    # =============================
    # LOGIN FUNCTION
    # =============================
    def do_login():
        username = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Warning", "Enter username & password")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT shop_id, owner_name FROM shops WHERE username=%s AND password=%s",
                (username, password)
            )
            row = cur.fetchone()
            conn.close()

            if row:
                shop_id, owner_name = row
                root.withdraw()
                show_dashboard(root, shop_id, owner_name)
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")

        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    # =============================
    # LOGIN BUTTON
    # =============================
    btn_login = tk.Button(
        card,
        text="LOGIN",
        font=("Segoe UI", 12, "bold"),
        bg=ACCENT1,
        fg="white",
        activebackground=ACCENT,
        relief="flat",
        width=28,
        pady=10,
        cursor="hand2",
        command=do_login
    )
    btn_login.grid(row=4, column=0)

    root.mainloop()



# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    login_window()
