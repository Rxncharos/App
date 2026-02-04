from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from datetime import datetime
import json, os

KV = """
<BudgetApp>:
    orientation: "vertical"
    padding: dp(10)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.12,0.12,0.14,1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "💰 Budget Tracker"
        font_size: dp(24)
        size_hint_y: None
        height: dp(50)
        bold: True
        color: 1,1,1,1

    # Balance Card
    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(100)
        padding: dp(10)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: 0.18,0.2,0.23,1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15,]
        Label:
            text: "Τρέχον Υπόλοιπο"
            font_size: dp(14)
            color: 0.7,0.7,0.7,1
        Label:
            text: root.balance_text
            font_size: dp(28)
            color: root.balance_color
            bold: True

    # Add Transaction Section
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: 0.18,0.2,0.23,1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12,]

        TextInput:
            id: desc_input
            hint_text: "Περιγραφή..."
            multiline: False
            size_hint_y: None
            height: dp(40)
            background_color: 0.15,0.15,0.17,1
            foreground_color: 1,1,1,1

        TextInput:
            id: amount_input
            hint_text: "Ποσό (€)..."
            multiline: False
            size_hint_y: None
            height: dp(40)
            input_filter: "float"
            background_color: 0.15,0.15,0.17,1
            foreground_color: 1,1,1,1

        Spinner:
            id: category_spinner
            text: "Φαγητό"
            values: ["Φαγητό","Μεταφορά","Ψυχαγωγία","Λογαριασμοί","Αγορές","Μισθός","Άλλο"]
            size_hint_y: None
            height: dp(40)
            background_color: 0.15,0.15,0.17,1
            color: 1,1,1,1

        BoxLayout:
            spacing: dp(5)
            size_hint_y: None
            height: dp(45)
            Button:
                text: "➕ Έσοδο"
                background_color: 0,0.7,0.4,1
                on_release: root.add_transaction("income")
            Button:
                text: "➖ Έξοδο"
                background_color: 0.84,0.19,0.19,1
                on_release: root.add_transaction("expense")

    # Transactions Header
    BoxLayout:
        size_hint_y: None
        height: dp(30)
        Label:
            text: "Πρόσφατες Συναλλαγές"
            color: 1,1,1,1
        Button:
            text: "🗑️"
            size_hint_x: None
            width: dp(40)
            on_release: root.clear_all()

    ScrollView:
        GridLayout:
            id: trans_list
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            row_default_height: dp(60)
            row_force_default: True
            spacing: dp(5)
"""

class BudgetApp(BoxLayout):
    transactions = ListProperty([])
    balance_text = StringProperty("€0.00")
    income_text = StringProperty("€0.00")
    expense_text = StringProperty("€0.00")
    balance_color = ListProperty([0,1,0,1])

    data_file = "budget_data.json"
    icons = {"Φαγητό":"🍔","Μεταφορά":"🚗","Ψυχαγωγία":"🎮","Λογαριασμοί":"📄","Αγορές":"🛒","Μισθός":"💼","Άλλο":"📌"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_data()
        self.refresh_transactions()

    def add_transaction(self, trans_type):
        desc = self.ids.desc_input.text.strip()
        amount_str = self.ids.amount_input.text.strip()
        category = self.ids.category_spinner.text
        if not desc or not amount_str:
            self.show_popup("Προσοχή","Συμπληρώστε όλα τα πεδία!")
            return
        try:
            amount = float(amount_str.replace(",", "."))
            if amount<=0: raise ValueError
        except ValueError:
            self.show_popup("Σφάλμα","Μη έγκυρο ποσό!")
            return
        transaction = {
            "id": len(self.transactions)+1,
            "type": trans_type,
            "description": desc,
            "amount": amount,
            "category": category,
            "date": datetime.now().strftime("%d/%m %H:%M")
        }
        self.transactions.insert(0, transaction)
        self.ids.desc_input.text = ""
        self.ids.amount_input.text = ""
        self.save_data()
        self.refresh_transactions()

    def delete_transaction(self, trans_id):
        self.transactions = [t for t in self.transactions if t["id"] != trans_id]
        self.save_data()
        self.refresh_transactions()

    def clear_all(self):
        if not self.transactions: return
        popup = Popup(title="Επιβεβαίωση", size_hint=(.6,.4))
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="Διαγραφή όλων των συναλλαγών;"))
        btns = BoxLayout(spacing=10)
        btn_yes = Button(text="Ναι")
        btn_no = Button(text="Όχι")
        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        content.add_widget(btns)
        popup.content = content
        btn_yes.bind(on_release=lambda x: self._confirm_clear(popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def _confirm_clear(self, popup):
        self.transactions = []
        self.save_data()
        self.refresh_transactions()
        popup.dismiss()

    def refresh_transactions(self):
        income = sum(t["amount"] for t in self.transactions if t["type"]=="income")
        expense = sum(t["amount"] for t in self.transactions if t["type"]=="expense")
        balance = income - expense
        self.balance_text = f"€{balance:,.2f}"
        self.income_text = f"€{income:,.2f}"
        self.expense_text = f"€{expense:,.2f}"
        self.balance_color = [0,1,0,1] if balance>=0 else [1,0,0,1]

        self.ids.trans_list.clear_widgets()
        if not self.transactions:
            self.ids.trans_list.add_widget(Label(text="Δεν υπάρχουν συναλλαγές", color=(0.6,0.6,0.6,1)))
            return

        for t in self.transactions[:20]:
            color = [0,1,0,1] if t["type"]=="income" else [1,0,0,1]
            row = BoxLayout(size_hint_y=None, height=60, spacing=5, padding=[5,5])
            # Icon + Description
            desc_box = BoxLayout(orientation='vertical')
            desc_box.add_widget(Label(text=f"{self.icons.get(t['category'],'📌')} {t['description']}", halign='left', color=(1,1,1,1), text_size=(0,None)))
            desc_box.add_widget(Label(text=f"{t['category']} • {t['date']}", halign='left', font_size=12, color=(0.7,0.7,0.7,1), text_size=(0,None)))
            row.add_widget(desc_box)
            # Amount
            row.add_widget(Label(text=f"{'+' if t['type']=='income' else '-'}€{t['amount']:.2f}", size_hint_x=None, width=80, color=color))
            # Delete button
            btn = Button(text="×", size_hint_x=None, width=30, background_color=(0,0,0,0), color=(1,1,1,1))
            btn.bind(on_release=lambda x, tid=t["id"]: self.delete_transaction(tid))
            row.add_widget(btn)
            self.ids.trans_list.add_widget(row)

    def save_data(self):
        with open(self.data_file,"w",encoding="utf-8") as f:
            json.dump(self.transactions,f,ensure_ascii=False, indent=2)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file,"r",encoding="utf-8") as f:
                    self.transactions = json.load(f)
            except:
                self.transactions = []

    def show_popup(self,title,message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(.6,.4))
        popup.open()

class BudgetTrackerApp(App):
    def build(self):
        Builder.load_string(KV)
        return BudgetApp()

if __name__=="__main__":
    BudgetTrackerApp().run()