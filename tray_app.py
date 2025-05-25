import pystray
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import json
import os
import sys
from datetime import datetime

class SupportPaymentTray:
    def __init__(self):
        self.icon = None
        self.root = None
        self.is_admin = False
        self.support_requests = []
        self.payment_requests = []
        
        # Check if running as admin
        try:
            self.is_admin = os.getuid() == 0
        except AttributeError:
            self.is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    def create_image(self):
        # Create an icon image
        width = 64
        height = 64
        color1 = "#3498db"  # Blue
        color2 = "#2ecc71"  # Green
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            [(width // 4, height // 4), (width * 3 // 4, height * 3 // 4)],
            fill=color2)
        
        return image

    def show_support_dialog(self):
        if not self.root:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the main window
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Request Support")
        dialog.geometry("400x300")
        
        # Support request form
        ttk.Label(dialog, text="Support Request").pack(pady=10)
        
        ttk.Label(dialog, text="Subject:").pack()
        subject_entry = ttk.Entry(dialog, width=40)
        subject_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Description:").pack()
        description_text = tk.Text(dialog, width=40, height=10)
        description_text.pack(pady=5)
        
        def submit_request():
            subject = subject_entry.get()
            description = description_text.get("1.0", tk.END)
            
            if subject and description.strip():
                # Save support request
                request = {
                    "subject": subject,
                    "description": description.strip(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending"
                }
                self.support_requests.append(request)
                self.save_requests()
                
                messagebox.showinfo("Success", "Support request submitted successfully!")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Please fill in all fields!")
        
        ttk.Button(dialog, text="Submit", command=submit_request).pack(pady=10)

    def show_admin_panel(self):
        if not self.root:
            self.root = tk.Tk()
            self.root.withdraw()
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Admin Panel")
        dialog.geometry("800x600")
        
        # Create tabs
        tab_control = ttk.Notebook(dialog)
        
        # Support Requests Tab
        support_tab = ttk.Frame(tab_control)
        tab_control.add(support_tab, text="Support Requests")
        
        # Payment Requests Tab
        payment_tab = ttk.Frame(tab_control)
        tab_control.add(payment_tab, text="Payment Requests")
        
        tab_control.pack(expand=1, fill="both")
        
        # Support Requests Table
        support_tree = ttk.Treeview(support_tab, columns=("Subject", "Status", "Timestamp"))
        support_tree.heading("#0", text="ID")
        support_tree.heading("Subject", text="Subject")
        support_tree.heading("Status", text="Status")
        support_tree.heading("Timestamp", text="Timestamp")
        support_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Payment Requests Table
        payment_tree = ttk.Treeview(payment_tab, columns=("Amount", "User", "Status", "Timestamp"))
        payment_tree.heading("#0", text="ID")
        payment_tree.heading("Amount", text="Amount")
        payment_tree.heading("User", text="User")
        payment_tree.heading("Status", text="Status")
        payment_tree.heading("Timestamp", text="Timestamp")
        payment_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load existing requests
        self.load_requests()
        
        # Populate tables
        for i, request in enumerate(self.support_requests):
            support_tree.insert("", "end", text=str(i), values=(
                request["subject"],
                request["status"],
                request["timestamp"]
            ))
            
        for i, payment in enumerate(self.payment_requests):
            payment_tree.insert("", "end", text=str(i), values=(
                payment["amount"],
                payment["user"],
                payment["status"],
                payment["timestamp"]
            ))
        
        # Add action buttons
        def update_support_status():
            selected = support_tree.selection()
            if selected:
                item = support_tree.item(selected[0])
                request_id = int(item["text"])
                self.support_requests[request_id]["status"] = "resolved"
                self.save_requests()
                support_tree.item(selected[0], values=(
                    item["values"][0],
                    "resolved",
                    item["values"][2]
                ))
        
        def update_payment_status(status):
            selected = payment_tree.selection()
            if selected:
                item = payment_tree.item(selected[0])
                payment_id = int(item["text"])
                self.payment_requests[payment_id]["status"] = status
                self.save_requests()
                payment_tree.item(selected[0], values=(
                    item["values"][0],
                    item["values"][1],
                    status,
                    item["values"][3]
                ))
        
        ttk.Button(support_tab, text="Mark as Resolved", 
                  command=update_support_status).pack(pady=5)
        
        ttk.Button(payment_tab, text="Accept Payment", 
                  command=lambda: update_payment_status("accepted")).pack(pady=5)
        ttk.Button(payment_tab, text="Reject Payment", 
                  command=lambda: update_payment_status("rejected")).pack(pady=5)

    def save_requests(self):
        data = {
            "support_requests": self.support_requests,
            "payment_requests": self.payment_requests
        }
        with open("requests.json", "w") as f:
            json.dump(data, f)

    def load_requests(self):
        try:
            with open("requests.json", "r") as f:
                data = json.load(f)
                self.support_requests = data.get("support_requests", [])
                self.payment_requests = data.get("payment_requests", [])
        except FileNotFoundError:
            self.support_requests = []
            self.payment_requests = []

    def run(self):
        # Create menu items
        menu = (
            pystray.MenuItem("Request Support", self.show_support_dialog),
            pystray.MenuItem("Admin Panel", self.show_admin_panel) if self.is_admin else None,
            pystray.MenuItem("Exit", lambda: self.icon.stop())
        )
        
        # Create and run the icon
        self.icon = pystray.Icon(
            "support_payment_icon",
            self.create_image(),
            "Support & Payment System",
            menu
        )
        
        # Run the icon in a separate thread
        threading.Thread(target=self.icon.run, daemon=True).start()

if __name__ == "__main__":
    app = SupportPaymentTray()
    app.run()
    
    # Keep the main thread running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        sys.exit(0) 