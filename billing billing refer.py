# -------------------------
# Billing Window (with working print + bindings + SMS + printer checks)
# -------------------------
def start_billing_app(workspace, shop_id, owner_name):

    ensure_tables_exist(shop_id)

    # ---------- OPEN INSIDE DASHBOARD WORKSPACE ----------
    for w in workspace.winfo_children():
        w.destroy()

    workspace.configure(bg=BG)

    billing = tk.Frame(workspace, bg=BG)
    billing.pack(fill="both", expand=True, padx=20, pady=20)

    # -------- OUTER BORDER (like Update Product) --------
    border = tk.Frame(billing, padx=2, pady=2)
    border.pack(fill="both", expand=True)

    container = tk.Frame(border, bg=BG)
    container.pack(fill="both", expand=True)

    # -------- HEADER --------
    header = tk.Frame(container, bg=BG)
    header.pack(fill="x", pady=10)

    tk.Label(
        header,
        text="SRI KRISHNA DEPARTMENT STORE",
        font=("Helvetica", 22, "bold"),
        fg=ACCENT1,
        bg=BG
    ).pack()

    tk.Label(
        header,
        text=f"Shop Owner: {owner_name} | Shop ID: {shop_id}",
        bg=BG,
        fg="#555555"
    ).pack()
    
    # -------- CUSTOMER BAR --------
    top = tk.Frame(container, bg=BG)
    top.pack(pady=10, anchor="w", padx=20)

    tk.Label(top, text="Customer Phone", bg=BG, fg=TEXT).grid(row=0, column=0, padx=6)
    entry_phone = tk.Entry(top, width=18, bg=CARD)
    entry_phone.grid(row=0, column=1, padx=6)

    lbl_name = tk.Label(top, text="Name : ------", bg=BG, fg=TEXT)
    lbl_name.grid(row=0, column=2, padx=12)

    tick_lbl = tk.Label(top, text="", bg=BG, fg=GOOD, font=("Arial", 14))
    tick_lbl.grid(row=0, column=3)

    btn_save = tk.Button(
        top,
        text="Save Customer",
        bg=ACCENT1,
        fg=BUTTON_TEXT,
        width=14
    )
    btn_save.grid(row=0, column=4, padx=10)

    # -------- ITEM ENTRY --------
    item_frame = tk.Frame(container, bg=BG)
    item_frame.pack(fill="x", padx=20)

    tk.Label(item_frame, text="Item ID / Barcode", bg=BG).grid(row=0, column=0, padx=6)
    entry_item = tk.Entry(item_frame, width=30, bg=CARD)
    entry_item.grid(row=0, column=1, padx=6)

    # -------- TABLE --------
    cols = ("sno", "item", "mrp", "price", "qty", "amount", "del")

    tree = ttk.Treeview(container, columns=cols, show="headings", height=14)
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=BG,
        fieldbackground=BG,
        foreground=TEXT,
        rowheight=26
    )
    style.map("Treeview", background=[("selected", "#D1FAFE")])

    headings = ["SNO", "ITEM", "MRP", "PRICE", "QTY", "AMOUNT", "DEL"]
    widths = [60, 360, 100, 100, 80, 120, 60]

    for c, h, w in zip(cols, headings, widths):
        tree.heading(c, text=h)
        tree.column(c, width=w, anchor="center")

    tree.pack(fill="both", expand=True, padx=20, pady=10)

    # -------- BOTTOM BAR --------
    bottom = tk.Frame(container, bg=BG)
    bottom.pack(fill="x", padx=20, pady=10)

    lbl_total = tk.Label(bottom, text="Total : 0.00", bg=BG, fg=TEXT, font=("Helvetica", 12, "bold"))
    lbl_total.pack(side="left", padx=10)

    tk.Label(bottom, text="Customer Given", bg=BG).pack(side="left")
    entry_given = tk.Entry(bottom, width=12, bg=CARD)
    entry_given.pack(side="left", padx=6)

    lbl_return = tk.Label(bottom, text="Return : 0.00", bg=BG, fg=TEXT, font=("Helvetica", 12, "bold"))
    lbl_return.pack(side="left", padx=10)

    tk.Button(
        bottom,
        text="PRINT",
        bg=ACCENT1,
        fg=BUTTON_TEXT,
        width=12
    ).pack(side="right", padx=10)

    def lookup_customer(event=None):
        phone = entry_phone.get().strip()
        if phone == "":
            lbl_name.config(text="Name: ------")
            tick_lbl.config(text="")
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT customer_id, name FROM customers WHERE phone=%s AND shop_id=%s", (phone, shop_id))
            row = cur.fetchone()
            conn.close()
            if row:
                cid, name = row
                lbl_name.config(text=f"{name}" if name else "Name: ------")
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
        # if user hasn't provided name via lookup, ask
        if name_text in ("------", "NEW CUSTOMER", ""):
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
                WHERE product_id=%s OR barcode=%s AND shop_id=%s
            """, (pid_or_code, pid_or_code, shop_id))
            row = cur.fetchone()
            conn.close()
            if not row:
                # fallback: attempt search by barcode only without shop_id (some DBs)
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT product_id, product_name, mrp, selling_price FROM products WHERE product_id=%s OR barcode=%s", (pid_or_code, pid_or_code))
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
                bill_items.append([iid, int(pid_db), qty, float(price), float(amount)])
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
    def save_and_print(self_event=None):
        nonlocal sno, bill_items

        # ------------------------------
        # READ PHONE + NAME
        # ------------------------------
        phone = entry_phone.get().strip()
        phone_for_db = phone if phone else None

        name_label_text = lbl_name.cget("text").replace("Name:", "").strip()
        if name_label_text in ("", "------", "NEW CUSTOMER"):
            customer_name = "NEW CUSTOMER"
        else:
            customer_name = name_label_text

        total = calculate_total()
        customer_id = None

        # =====================================================
        # 1) ALWAYS UPDATE CUSTOMER — EVEN IF NO PHONE GIVEN
        # =====================================================
        try:
            conn = get_connection()
            cur = conn.cursor()

            # CASE 1 — phone empty → treat as anonymous customer bucket
            if not phone_for_db:
                phone_for_db = ""   # store empty phone safely

            # Check exists (by phone + shop)
            cur.execute("""
                SELECT customer_id, total_spent
                FROM customers
                WHERE phone=%s AND shop_id=%s
            """, (phone_for_db, shop_id))
            row = cur.fetchone()

            if row:
                # Existing customer
                customer_id = row[0]
                old_total = float(row[1])

                cur.execute("""
                    UPDATE customers SET
                        name = %s,
                        last_purchase = NOW(),
                        last_amount = %s,
                        total_spent = %s
                    WHERE customer_id = %s
                """, (
                    customer_name,
                    total,
                    old_total + total,
                    customer_id
                ))

            else:
                # Create new customer
                cur.execute("""
                    INSERT INTO customers
                    (shop_id, name, phone, total_spent, last_purchase, last_amount)
                    VALUES (%s, %s, %s, %s, NOW(), %s)
                """, (
                    shop_id,
                    customer_name,
                    phone_for_db,
                    total,
                    total
                ))
                customer_id = cur.lastrowid

            conn.commit()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Customer update failed: {e}")

        # =====================================================
        # 2) IF NO ITEMS — ONLY CUSTOMER SAVED, STOP HERE
        # =====================================================
        if total <= 0:
            messagebox.showinfo("Saved", "Customer saved successfully.")
            return

        # =====================================================
        # 3) SAVE SALE + ITEMS
        # =====================================================
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO sales (shop_id, customer_id, total_amount, discount, payment_method)
                VALUES (%s, %s, %s, %s, %s)
            """, (shop_id, customer_id, total, 0.0, ""))

            sale_id = cur.lastrowid

            for rec in bill_items:
                iid, pid, qty, price, amount = rec

                cur.execute("""
                    INSERT INTO bill_items (sale_id, product_id, quantity, price, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sale_id, pid, qty, price, amount))

                cur.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (qty, pid))

            # Billing history
            cur.execute("""
                INSERT INTO billing (shop_id, customer_phone, amount, bill_time)
                VALUES (%s, %s, %s, NOW())
            """, (shop_id, phone_for_db, total))

            conn.commit()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Sale save failed: {e}")
            return

        # =====================================================
        # 4) PDF GENERATE
        # =====================================================
        pdf_filename = f"bill_{sale_id}.pdf"

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 8, txt="SRI KRISHNA DEPARTMENT STORE", ln=True, align='C')
            pdf.ln(4)
            pdf.cell(200, 8, txt=f"Bill No: {sale_id}", ln=True)
            pdf.cell(200, 8, txt=f"Total: Rs. {total:.2f}", ln=True)
            pdf.cell(200, 8, txt=f"Customer: {customer_name}", ln=True)
            pdf.cell(200, 8, txt=f"Phone: {phone_for_db}", ln=True)

            pdf.ln(6)
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

            pdf.output(pdf_filename)

        except Exception as e:
            messagebox.showerror("PDF Error", f"PDF failed: {e}")

        # =====================================================
        # 5) PRINT
        # =====================================================
        try:
            if is_printer_connected_system():
                ok, msg = send_pdf_to_printer(pdf_filename)
                if not ok:
                    messagebox.showwarning("Print Error", msg)
            else:
                messagebox.showwarning("Printer", "Printer offline. PDF saved.")
        except:
            pass

        # =====================================================
        # 6) RESET UI
        # =====================================================
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


    billing.bind("<Shift-Return>", save_and_print)
    print_btn.config(command=save_and_print)




        

    # --------------------------------------------------------
# CUSTOMER PURCHASE TRACKING (AUTO-UPDATE)
# --------------------------------------------------------
    total_amount = calculate_total()  # your existing function

    phone = entry_phone.get().strip()
    name_val = lbl_name.cget("text").replace("Name:", "").strip()

    if phone != "":
        try:
            conn = get_connection()
            cur = conn.cursor()

            # 1. CHECK if customer exists
            cur.execute("""
                SELECT customer_id FROM customers
                WHERE phone=%s AND shop_id=%s
            """, (phone, shop_id))
            result = cur.fetchone()

            # 2. If not exist → insert new customer
            if not result:
                cur.execute("""
                    INSERT INTO customers (shop_id, name, phone, total_spent)
                    VALUES (%s, %s, %s, %s)
                """, (shop_id, name_val, phone, total_amount))

            else:
                # 3. Update total spent
                cur.execute("""
                    UPDATE customers
                    SET total_spent = total_spent + %s
                    WHERE phone=%s AND shop_id=%s
                """, (total_amount, phone, shop_id))

            # 4. Add billing entry table (purchase history)
            cur.execute("""
                INSERT INTO billing (shop_id, customer_phone, amount)
                VALUES (%s, %s, %s)
            """, (shop_id, phone, total_amount))

            conn.commit()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", f"Customer update failed:\n{e}")
