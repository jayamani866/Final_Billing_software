def save_and_print(event=None):
        nonlocal sno

        # customer phone optional
        phone = entry_phone.get().strip()
        phone_for_db = phone if phone != "" else None

        # customer name optional
        name_text = lbl_name.cget("text").replace("Name: ", "")
        customer_name_display = "" if name_text in ("------", "NEW CUSTOMER") else name_text

        # total
        total = calculate_total()

        try:
            given = float(entry_given.get()) if entry_given.get().strip() != "" else 0.0
        except:
            given = 0.0

        # if bill empty → block
        if total <= 0:
            messagebox.showwarning("Empty Bill", "Add items before printing.")
            return

        # -------------- SAVE SALE --------------
        try:
            conn = get_connection()
            cur = conn.cursor()

            # insert sale (phone nullable)
            cur.execute("""
                INSERT INTO sales (customer_phone, total_amount)
                VALUES (%s, %s)
            """, (phone_for_db, total))

            sale_id = cur.lastrowid

            # save items
            for rec in bill_items:
                pid = rec[1]
                qty = rec[2]
                price = rec[3]
                amt = rec[4]

                cur.execute("""
                    INSERT INTO bill_items (sale_id, product_id, quantity, price, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sale_id, pid, qty, price, amt))

            conn.commit()
            conn.close()

        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        # -------------- PRINT PDF (name/phone optional) --------------
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="*** BILL ***", ln=1, align="C")

        pdf.cell(200, 10, txt=f"Customer: {customer_name_display}", ln=1)
        pdf.cell(200, 10, txt=f"Phone: {phone}", ln=1)

        pdf.ln(5)

        # table header
        pdf.cell(80, 10, "Item", 1)
        pdf.cell(30, 10, "Qty", 1)
        pdf.cell(40, 10, "Price", 1)
        pdf.cell(40, 10, "Total", 1)
        pdf.ln()

        for rec in bill_items:
            name = tree.item(rec[0])["values"][1]
            qty = rec[2]
            price = rec[3]
            amt = rec[4]

            pdf.cell(80, 10, name, 1)
            pdf.cell(30, 10, str(qty), 1)
            pdf.cell(40, 10, f"{price:.2f}", 1)
            pdf.cell(40, 10, f"{amt:.2f}", 1)
            pdf.ln()

        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Total: {total:.2f}", ln=1)
        pdf.cell(200, 10, txt=f"Given: {given:.2f}", ln=1)
        pdf.cell(200, 10, txt=f"Return: {given-total:.2f}", ln=1)

        pdf.output("bill.pdf")

        messagebox.showinfo("Success", "Bill printed successfully!")

        # bind shift-enter to save and print 
        billing.bind("<Shift-Return>", save_and_print)




# load customer 
    def load_customers(start_dt=None, end_dt=None):
        global all_customer_rows

        all_customer_rows.clear()
        tree_customers.delete(*tree_customers.get_children())

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT
                customer_id,
                customer_name,
                phone_1,
                address,
                last_purchase_amount,
                lifetime_total,
                total_points
            FROM customers
            WHERE shop_id = %s
            AND status = 'ACTIVE'
        """

        params = [shop_id]

        # ❌ date filter REMOVE pannirukom
        # because last_purchase_datetime use panna vendam

        query += " ORDER BY customer_id DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            values = (
                r[0],                     # customer_id
                r[1],                     # name
                r[2],                     # phone
                r[3] or "-",              # address
                f"₹ {r[4]:.2f}",          # ✅ LAST PURCHASE AMOUNT
                f"₹ {r[5]:.2f}",          # lifetime total
                r[6],                     # points
                "View"
            )

            all_customer_rows.append(values)

        refresh_table(all_customer_rows)












    # # =========================
    # # SAFE GLOBAL SHORTCUT HANDLER (FINAL)
    # # =========================
   
    # root = workspace.winfo_toplevel()

    # def on_close_billing():
    #     global bill_window_alive
    #     bill_window_alive = False
    #     workspace.destroy()

       
    # root = workspace.winfo_toplevel()
    # root.protocol("WM_DELETE_WINDOW", on_close_billing)
    # # ======================================================
    # # ✅ GLOBAL BILL SHORTCUT FIX (FINAL – WORKING)
    # # ======================================================

    # def setup_billing_shortcuts(root):
    #     global bill_window_alive
    #     bill_window_alive = True

    #     def handle_shortcut(event):
    #         if not bill_window_alive:
    #             return "break"

    #         if bill_tree is None:
    #             return "break"

    #         try:
    #             if not bill_tree.winfo_exists():
    #                 return "break"
    #         except:
    #             return "break"

    #         key = event.keysym.lower()
    #         state = event.state

    #         ctrl  = (state & 0x0004) != 0
    #         shift = (state & 0x0001) != 0

    #         # 🔥 SHIFT + ENTER
    #         if shift and key == "return":
    #             print("🔥 SHIFT + ENTER")
    #             print_bill()
    #             return "break"

    #         # 🔥 CTRL + ENTER
    #         if ctrl and key == "return":
    #             print("🔥 CTRL + ENTER")
    #             print_bill()
    #             return "break"

    #         # 🔥 CTRL + B
    #         if ctrl and key == "b":
    #             print("🔥 CTRL + B")
    #             print_bill()
    #             return "break"

    #         # 🔥 SHIFT + SPACE
    #         if shift and key == "space":
    #             print("🔥 SHIFT + SPACE")
    #             print_bill()
    #             return "break"

    #         return None


    #     # 🔥 VERY IMPORTANT:
    #     # override Entry / ttk.Entry / Treeview default behavior
    #     for cls in ("Entry", "TEntry", "Treeview"):
    #         try:
    #             root.bind_class(cls, "<Key>", handle_shortcut)
    #         except:
    #             pass

    #     # fallback (window level)
    #     root.bind("<Key>", handle_shortcut)


    # # CALL THIS ONCE AFTER UI LOAD
    # setup_billing_shortcuts(workspace.winfo_toplevel())