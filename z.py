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
# DB table ensure
# -------------------------
def ensure_tables_exist(shop_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL,
            name VARCHAR(255),
            phone VARCHAR(255) UNIQUE,
            address VARCHAR(255),
            total_spent DOUBLE DEFAULT 0,
            joined_date DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL,
            customer_phone VARCHAR(255),
            total_amount DOUBLE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT,
            product_id VARCHAR(255),
            quantity INT,
            price DOUBLE,
            subtotal DOUBLE
        ) ENGINE=InnoDB
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            mrp DOUBLE NOT NULL DEFAULT 0,
            selling_price DOUBLE NOT NULL DEFAULT 0,
            barcode VARCHAR(255),
            gst DOUBLE DEFAULT 0,
            brand VARCHAR(255),
            stock INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("Ensure tables error:", e)

# -------------------------
# SMS placeholder (replace with Twilio or your provider)
# -------------------------
def send_sms(phone, message):
    # placeholder - replace with Twilio or other provider
    print(f"[SMS -> {phone}]: {message}")

# -------------------------
# Printer helpers
# -------------------------
def is_printer_connected_unix():
    # Uses lpstat -p output — returns True if at least one printer is found
    try:
        out = subprocess.check_output("lpstat -p", shell=True, stderr=subprocess.STDOUT).decode(errors="ignore")
        # If lpstat prints nothing or error, treat as no printers.
        return "printer" in out.lower() or "printer " in out.lower()
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def send_pdf_to_printer(path):
    """
    Try to send PDF to printer; return (success: bool, message:str)
    Supports Unix (lp/lpr) and Windows (os.startfile with "print").
    """
    system = platform.system().lower()
    if system == "windows":
        try:
            # This will open the default print action
            os.startfile(os.path.abspath(path), "print")
            return True, "Sent to printer (Windows print)"
        except Exception as e:
            return False, f"Windows print error: {e}"
    else:
        # Unix-like - try lp then lpr fallback
        try:
            # prefer lp if available
            if shutil_which("lp"):
                p = subprocess.run(["lp", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif shutil_which("lpr"):
                p = subprocess.run(["lpr", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                return False, "No lp/lpr available on system"
            if p.returncode == 0:
                return True, "Sent to printer (lp/lpr)"
            else:
                return False, p.stderr.decode(errors="ignore")
        except Exception as e:
            return False, str(e)

def shutil_which(cmd):
    # small wrapper to avoid importing shutil at top-level repeatedly
    from shutil import which
    return which(cmd)

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

# -------------------------
# Add Product Window
# -------------------------
def open_add_product_window(parent, shop_id):
    win = tk.Toplevel(parent)
    win.title("Add Product")
    win.configure(bg=BG)
    center_window(win, 600, 380)

    frm = tk.Frame(win, bg=BG)
    frm.pack(pady=12, padx=12, fill="both", expand=True)

    tk.Label(frm, text="Product ID (auto):", bg=BG, fg=TEXT).grid(row=0, column=0, sticky="e", padx=6, pady=6)
    lbl_pid = tk.Label(frm, text="(will be assigned)", bg=BG, fg=TEXT)
    lbl_pid.grid(row=0, column=1, sticky="w", padx=6, pady=6)

    tk.Label(frm, text="Product Name:", bg=BG, fg=TEXT).grid(row=1, column=0, sticky="e", padx=6, pady=6)
    entry_name = tk.Entry(frm, bg=CARD, fg=TEXT, width=36, insertbackground=TEXT)
    entry_name.grid(row=1, column=1, padx=6, pady=6)

    tk.Label(frm, text="MRP:", bg=BG, fg=TEXT).grid(row=2, column=0, sticky="e", padx=6, pady=6)
    entry_mrp = tk.Entry(frm, bg=CARD, fg=TEXT, width=20, insertbackground=TEXT)
    entry_mrp.grid(row=2, column=1, sticky="w", padx=6, pady=6)

    tk.Label(frm, text="Selling Price:", bg=BG, fg=TEXT).grid(row=3, column=0, sticky="e", padx=6, pady=6)
    entry_price = tk.Entry(frm, bg=CARD, fg=TEXT, width=20, insertbackground=TEXT)
    entry_price.grid(row=3, column=1, sticky="w", padx=6, pady=6)

    tk.Label(frm, text="Barcode:", bg=BG, fg=TEXT).grid(row=4, column=0, sticky="e", padx=6, pady=6)
    entry_barcode = tk.Entry(frm, bg=CARD, fg=TEXT, width=30, insertbackground=TEXT)
    entry_barcode.grid(row=4, column=1, sticky="w", padx=6, pady=6)

    tk.Label(frm, text="Stock:", bg=BG, fg=TEXT).grid(row=5, column=0, sticky="e", padx=6, pady=6)
    entry_stock = tk.Entry(frm, bg=CARD, fg=TEXT, width=10, insertbackground=TEXT)
    entry_stock.grid(row=5, column=1, sticky="w", padx=6, pady=6)

    tk.Label(frm, text="Brand (opt):", bg=BG, fg=TEXT).grid(row=6, column=0, sticky="e", padx=6, pady=6)
    entry_brand = tk.Entry(frm, bg=CARD, fg=TEXT, width=30, insertbackground=TEXT)
    entry_brand.grid(row=6, column=1, sticky="w", padx=6, pady=6)

    def lookup_by_barcode(event=None):
        code = entry_barcode.get().strip()
        if code == "":
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT product_id, product_name, mrp, selling_price, stock, brand FROM products WHERE barcode=%s", (code,))
            row = cur.fetchone()
            conn.close()
            if row:
                pid, name, mrp, price, stock, brand = row
                lbl_pid.config(text=str(pid))
                entry_name.delete(0, tk.END); entry_name.insert(0, name or "")
                entry_mrp.delete(0, tk.END); entry_mrp.insert(0, str(mrp or ""))
                entry_price.delete(0, tk.END); entry_price.insert(0, str(price or ""))
                entry_stock.delete(0, tk.END); entry_stock.insert(0, str(stock or ""))
                entry_brand.delete(0, tk.END); entry_brand.insert(0, brand or "")
                messagebox.showinfo("Found", f"Product found (ID: {pid}) - fields filled")
            else:
                lbl_pid.config(text="(will be assigned)")
                messagebox.showinfo("Not found", "Barcode not in DB. Enter product details and Save.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    entry_barcode.bind("<Return>", lookup_by_barcode)

    def save_product():
        name = entry_name.get().strip()
        try:
            mrp = float(entry_mrp.get().strip()) if entry_mrp.get().strip() != "" else 0.0
        except:
            messagebox.showwarning("Invalid", "MRP must be a number")
            return
        try:
            price = float(entry_price.get().strip()) if entry_price.get().strip() != "" else 0.0
        except:
            messagebox.showwarning("Invalid", "Selling price must be a number")
            return
        barcode = entry_barcode.get().strip()
        try:
            stock = int(entry_stock.get().strip()) if entry_stock.get().strip() != "" else 0
        except:
            messagebox.showwarning("Invalid", "Stock must be an integer")
            return
        brand = entry_brand.get().strip()

        if name == "":
            messagebox.showwarning("Missing", "Enter product name")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO products (shop_id, product_name, mrp, selling_price, barcode, brand, stock)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (shop_id, name, mrp, price, barcode, brand, stock))
            conn.commit()
            pid = cur.lastrowid
            conn.close()
            lbl_pid.config(text=str(pid))
            messagebox.showinfo("Saved", f"Product saved with ID: {pid}")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    btn_save = tk.Button(frm, text="Save Product", bg=ACCENT1, fg=BUTTON_TEXT, command=save_product)
    btn_save.grid(row=7, column=1, pady=12, sticky="w")

# -------------------------
# Billing Window (with working print + bindings + SMS + printer checks)
# -------------------------
def start_billing_app(parent, shop_id, owner_name):
    ensure_tables_exist(shop_id)

    billing = tk.Toplevel(parent)
    billing.title(f"Billing - {owner_name}")
    billing.configure(bg=BG)
    try:
        billing.state('zoomed')
    except:
        billing.attributes('-zoomed', True)

    header = tk.Frame(billing, bg=BG)
    header.pack(fill="x", pady=6)
    lbl_title = tk.Label(header, text="SRI KRISHNA DEPARTMENT STORE", font=("Helvetica", 20, "bold"), fg=TEXT, bg=BG)
    lbl_title.pack()
    sub = tk.Label(header, text=f"Shop Owner: {owner_name} | Shop ID: {shop_id}", bg=BG, fg=ACCENT1)
    sub.pack()

    top = tk.Frame(billing, bg=BG)
    top.pack(pady=8, anchor="w", padx=12)

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

    # item entry and treeview
    item_frame = tk.Frame(billing, bg=BG)
    item_frame.pack(pady=6, fill="x", padx=12)
    tk.Label(item_frame, text="Item ID / Barcode:", bg=BG, fg=TEXT).grid(row=0, column=0, padx=6)
    entry_item = tk.Entry(item_frame, width=30, bg=CARD, fg=TEXT, insertbackground=TEXT)
    entry_item.grid(row=0, column=1, padx=6)

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

    bill_items = []
    sno = 1

    def find_bill_index_by_pid(pid):
        for i, rec in enumerate(bill_items):
            if str(rec[1]) == str(pid):
                return i
        return None

    def add_item(event=None):
        nonlocal sno
        pid_or_code = entry_item.get().strip()
        if pid_or_code == "":
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT product_id, product_name, mrp, selling_price FROM products
                WHERE product_id=%s OR barcode=%s
            """, (pid_or_code, pid_or_code))
            row = cur.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Error", "Invalid product id or barcode")
                return
            pid_db, name, mrp, price = row

            idx = find_bill_index_by_pid(pid_db)
            if idx is not None:
                rec = bill_items[idx]
                rec[2] = int(rec[2]) + 1
                rec[4] = float(rec[2]) * float(rec[3])
                iid = rec[0]
                vals = list(tree.item(iid, "values"))
                vals[4] = rec[2]
                vals[5] = f"{rec[4]:.2f}"
                tree.item(iid, values=vals)
            else:
                qty = 1
                amount = float(price) * qty
                iid = tree.insert("", "end", values=(sno, name, mrp, price, qty, f"{amount:.2f}", "X"))
                bill_items.append([iid, str(pid_db), qty, float(price), float(amount)])
                sno += 1

            entry_item.delete(0, tk.END)
            calculate_total()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    entry_item.bind("<Return>", add_item)

    def on_tree_click(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        if col == f"#{len(cols)}":
            remove_index = None
            for i, rec in enumerate(bill_items):
                if rec[0] == row_id:
                    remove_index = i
                    break
            if remove_index is not None:
                bill_items.pop(remove_index)
            tree.delete(row_id)
            renumber()
            calculate_total()

    tree.bind("<ButtonRelease-1>", on_tree_click)

    def on_tree_double_click(event):
        iid = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not iid:
            return
        if col == "#5":
            vals = list(tree.item(iid, "values"))
            try:
                current_qty = int(vals[4])
            except:
                current_qty = 1
            new_qty = simpledialog.askinteger("Quantity", "Enter quantity:", initialvalue=current_qty, minvalue=1)
            if new_qty is None:
                return
            price = float(vals[3])
            new_amount = new_qty * price
            vals[4] = new_qty
            vals[5] = f"{new_amount:.2f}"
            tree.item(iid, values=vals)
            for rec in bill_items:
                if rec[0] == iid:
                    rec[2] = int(new_qty)
                    rec[4] = float(new_amount)
                    break
            calculate_total()

    tree.bind("<Double-1>", on_tree_double_click)

    def renumber():
        i = 1
        for iid in tree.get_children():
            vals = list(tree.item(iid, "values"))
            vals[0] = i
            tree.item(iid, values=vals)
            i += 1

    bottom = tk.Frame(billing, bg=BG)
    bottom.pack(pady=8, fill="x", padx=12)

    lbl_total = tk.Label(bottom, text="Total: 0.00", bg=BG, fg=TEXT, font=("Helvetica", 12, "bold"))
    lbl_total.pack(side="left", padx=(0,10))

    tk.Label(bottom, text="Customer Given:", bg=BG, fg=TEXT).pack(side="left")
    entry_given = tk.Entry(bottom, width=12, bg=CARD, fg=TEXT, insertbackground=TEXT)
    entry_given.pack(side="left", padx=(6,10))

    lbl_return = tk.Label(bottom, text="Return: 0.00", bg=BG, fg=TEXT, font=("Helvetica", 12, "bold"))
    lbl_return.pack(side="left", padx=10)

    right_btn_frame = tk.Frame(bottom, bg=BG)
    right_btn_frame.pack(side="right")
    print_btn = tk.Button(right_btn_frame, text="PRINT", bg=ACCENT2, fg=BUTTON_TEXT, width=12)
    print_btn.pack(padx=4, pady=2)

    def calculate_total():
        total = 0.0
        for iid in tree.get_children():
            try:
                amt = tree.item(iid)["values"][5]
                val = float(amt)
            except:
                val = 0.0
            total += val
        lbl_total.config(text=f"Total: {total:.2f}")
        update_return()
        return total

    def update_return(event=None):
        try:
            given = float(entry_given.get())
        except:
            given = 0.0
        try:
            total_text = lbl_total.cget("text").replace("Total: ", "")
            total = float(total_text)
        except:
            total = 0.0
        ret = given - total
        lbl_return.config(text=f"Return: {ret:.2f}")

    entry_given.bind("<KeyRelease>", update_return)

    # ---------------- core: save_and_print ----------------
    def is_printer_connected():
        system = platform.system().lower()

        # Linux & Mac
        if system in ["linux", "darwin"]:
            try:
                output = subprocess.check_output(["lpstat", "-p"], stderr=subprocess.STDOUT).decode()
                return ("printer" in output.lower() or 
                        "idle" in output.lower() or 
                        "enabled" in output.lower())
            except:
                return False

        # Windows
        if system == "windows":
            try:
                import subprocess
                default = subprocess.GetDefaultPrinter()
                return bool(default)
            except:
                return False

        return False



    def save_and_print(event=None):
        nonlocal sno, bill_items

        phone = entry_phone.get().strip()
        phone_for_db = phone if phone else None

        # customer name
        name_text = lbl_name.cget("text").replace("Name: ", "").strip()
        customer_name_display = "" if name_text in ("------", "NEW CUSTOMER") else name_text

        total = calculate_total()
        if total <= 0:
            messagebox.showwarning("Empty Bill", "Add items before printing.")
            return

        # SAVE TO DB (NO customer_phone column!)
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("INSERT INTO sales (total_amount) VALUES (%s)", (total,))
            sale_id = cur.lastrowid

            for rec in bill_items:
                iid, pid, qty, price, amt = rec
                cur.execute("""
                    INSERT INTO bill_items (sale_id, product_id, quantity, price, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sale_id, pid, qty, price, amt))

                cur.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (qty, pid))

            # Update customer spending only if phone exists
            if phone_for_db:
                cur.execute("UPDATE customers SET total_spent = total_spent + %s WHERE phone = %s",
                            (total, phone_for_db))

            conn.commit()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        # GENERATE PDF
        pdf_filename = f"bill_{sale_id}.pdf"
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 8, txt="SRI KRISHNA DEPARTMENT STORE", ln=True, align='C')
            pdf.ln(3)
            pdf.cell(200, 8, txt=f"Bill No: {sale_id}", ln=True)
            pdf.cell(200, 8, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

            if phone_for_db:
                pdf.cell(200, 8, txt=f"Customer Phone: {phone_for_db}", ln=True)

            if customer_name_display:
                pdf.cell(200, 8, txt=f"Customer Name: {customer_name_display}", ln=True)

            pdf.ln(5)
            pdf.cell(80, 8, "Item", border=1)
            pdf.cell(20, 8, "Qty", border=1)
            pdf.cell(30, 8, "Price", border=1)
            pdf.cell(30, 8, "Amount", border=1, ln=True)

            for rec in bill_items:
                iid, pid, qty, price, amount = rec
                vals = tree.item(iid)["values"]
                name = str(vals[1])
                pdf.cell(80, 8, name[:30], border=1)
                pdf.cell(20, 8, str(qty), border=1)
                pdf.cell(30, 8, f"{price:.2f}", border=1)
                pdf.cell(30, 8, f"{amount:.2f}", border=1, ln=True)

            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, txt=f"TOTAL: ₹{total:.2f}", ln=True)

            pdf.output(pdf_filename)

        except Exception as e:
            messagebox.showerror("Print Error", f"Could not generate PDF: {e}")
            return

        # PRINTER CHECK
        if is_printer_connected():
            ok, msg = send_pdf_to_printer(pdf_filename)
            if not ok:
                messagebox.showerror("Print failed", msg)
        else:
            messagebox.showerror("Printer Error", "Printer not connected. Please connect the printer.")

        # SEND SMS
        if phone_for_db:
            try:
                sms_text = f"Thank you! Your bill no {sale_id}. Total ₹{total:.2f}."
                send_sms(phone_for_db, sms_text)
            except:
                print("SMS error")

        # RESET UI
        for iid in tree.get_children():
            tree.delete(iid)

        bill_items.clear()
        sno = 1

        entry_item.delete(0, tk.END)
        entry_phone.delete(0, tk.END)
        lbl_name.config(text="Name: ------")
        lbl_total.config(text="Total: 0.00")
        entry_given.delete(0, tk.END)
        lbl_return.config(text="Return: 0.00")

        messagebox.showinfo("Saved", f"Bill saved as {pdf_filename}")




    # BIND KEYS
  
    billing.bind("<Shift-Return>", save_and_print)
   
   
    print_btn.config(command=save_and_print)

# -------------------------
# Dashboard
# -------------------------
def show_dashboard(root, shop_id, owner_name):
    dash = tk.Toplevel(root)
    dash.title("Dashboard")
    dash.configure(bg=BG)
    try:
        dash.state('zoomed')
    except:
        dash.attributes('-zoomed', True)

    def on_dash_close():
        try:
            root.deiconify()
        except:
            pass
        dash.destroy()

    dash.protocol("WM_DELETE_WINDOW", on_dash_close)

    header = tk.Label(dash, text=f"Welcome, {owner_name}", bg=BG, fg=TEXT, font=("Helvetica", 16, "bold"))
    header.pack(pady=12)

    frame = tk.Frame(dash, bg=BG)
    frame.pack(pady=20)

    billing_btn = animated_square(frame, "BILLING", lambda: start_billing_app(dash, shop_id, owner_name), size=140)
    billing_btn.grid(row=0, column=0, padx=16, pady=16)

    add_prod_btn = animated_square(frame, "ADD PRODUCT", lambda: open_add_product_window(dash, shop_id), size=140)
    add_prod_btn.grid(row=0, column=1, padx=20, pady=12)

    def do_logout():
        if messagebox.askyesno("Logout", "Logout and return to login?"):
            dash.destroy()
            try:
                root.deiconify()
            except:
                pass

    logout_btn = tk.Button(frame, text="LOGOUT", width=12, bg=ACCENT1, fg=BUTTON_TEXT, command=do_logout)
    logout_btn.grid(row=1, column=0, columnspan=2, pady=(8,0))

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
            cur.execute("SELECT shop_id, owner_name FROM shops WHERE username=%s AND password=%s", (username, password))
            row = cur.fetchone()
            conn.close()
            if row:
                shop_id, owner_name = row
                root.withdraw()
                show_dashboard(root, shop_id, owner_name)
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
