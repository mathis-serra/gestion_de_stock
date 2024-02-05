import mysql.connector
import csv
import tkinter as tk, tkinter.ttk as ttk, tkinter.messagebox as messagebox


class Application:
    def __init__(self, master):
        # Database setup
        self.mydb = mysql.connector.connect(host="localhost", user="root", password="Minecraft01@", database="boutique")
        self.my_cursor = self.mydb.cursor()

        # GUI setup
        self.master = master
        self.master.title("Gestion de stock")

        # Create a treeview to display the products
        self.tree = ttk.Treeview(self.master, columns=("id", "nom", "description", "prix", "quantite", "categorie"),
        show="headings")
        [self.tree.heading(col, text=text) for col, text in
         zip(("id", "nom", "description", "prix", "quantite", "categorie"),
             ("ID", "Nom", "Description", "Prix", "Quantité", "Catégorie"))]
        self.tree.pack()

        # Product buttons frame
        product_buttons_frame = tk.LabelFrame(self.master, text="Produit", padx=5, pady=5)
        [tk.Button(product_buttons_frame, text=text, command=command).pack(expand=True) for text, command in
         [("Ajouter", self.add_product), ("Supprimer", self.delete_product), ("Modifier", self.edit_product)]]
        product_buttons_frame.pack(side="left", padx=10, pady=10, fill="y", expand=True)

        # Category buttons frame
        category_buttons_frame = tk.LabelFrame(self.master, text="Catégorie", padx=5, pady=5)
        tk.Button(category_buttons_frame, text="Ajouter catégorie", command=self.add_category).pack()
        tk.Button(category_buttons_frame, text="Supprimer catégorie", command=self.delete_category).pack()
        category_buttons_frame.pack(side="left", padx=10, pady=10, fill="y", expand=True)

        # Export button frame
        export_button_frame = tk.LabelFrame(self.master, text="Exporter", padx=5, pady=5)
        tk.Button(export_button_frame, text="Exporter vers CSV", command=lambda: self.export_csv("produit.csv")).pack()
        export_button_frame.pack(side="left", padx=10, pady=10, fill="y", expand=True)

        self.load_products()

    def load_products(self):
        self.tree.delete(*self.tree.get_children())

        self.my_cursor.execute("SELECT * FROM produit")
        rows = self.my_cursor.fetchall()

        for row in rows:
            product = (row[0], row[1], row[2], row[3], row[4], self.get_categorie_by_id(row[5]))
            self.tree.insert("", "end", values=product[:-1] + (product[-1][1] if product[-1] else "None",))

    def add_product(self):
        add_window = tk.Toplevel(self.master)
        add_window.title("Ajouter un produit")

        details = ["Nom", "Description", "Prix", "Quantité"]
        entries = [tk.Entry(add_window) for _ in range(len(details))]
        for detail, entry in zip(details, entries):
            tk.Label(add_window, text=f"{detail}:").pack()
            entry.pack()

        tk.Label(add_window, text="Catégorie:").pack()
        categorie_combobox = ttk.Combobox(add_window, values=self.get_categories())
        categorie_combobox.pack()

        def save_product():
            self.save_product(*[entry.get() for entry in entries], categorie_combobox.get(), add_window)

        tk.Button(add_window, text="Enregistrer", command=save_product).pack()

    def save_product(self, nom, description, prix, quantite, categorie_nom, window):
        # if caterorie_nom is not in the database, add it
        if not self.get_categorie_by_nom(categorie_nom):
            self.my_cursor.execute("INSERT INTO categorie (nom) VALUES (%s)", (categorie_nom,))
            self.mydb.commit()
        categorie = self.get_categorie_by_nom(categorie_nom)
        categorie_id = self.my_cursor.lastrowid if categorie is None else categorie[0]

        self.my_cursor.execute(
            "INSERT INTO produit (nom, description, prix, quantite, id_categorie) VALUES (%s, %s, %s, %s, %s)",
            (nom, description, prix, quantite, categorie_id))
        self.mydb.commit()

        messagebox.showinfo("Succès", "Le produit a été ajouté avec succès.")
        self.load_products()
        window.destroy()

    def delete_product(self):
        selected_item = self.tree.selection()
        if selected_item:
            if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce produit?"):
                self.my_cursor.execute("DELETE FROM produit WHERE id = %s",
                                       (self.tree.item(selected_item[0])["values"][0],))
                self.mydb.commit()

                self.tree.delete(selected_item)

    def edit_product(self):
        selected_item = self.tree.selection()[0]
        values = self.tree.item(selected_item)["values"]
        product_id = values[0]

        self.my_cursor.execute("SELECT * FROM produit WHERE id = %s", (product_id,))
        row = self.my_cursor.fetchone()
        categorie = self.get_categorie_by_id(row[5])
        product = (row[0], row[1], row[2], row[3], row[4], categorie)

        edit_window = tk.Toplevel(self.master)
        edit_window.title("Modifier le produit")

        details = ["Nom", "Description", "Prix", "Quantité"]
        entries = []
        for detail in details:
            tk.Label(edit_window, text=f"{detail}:").pack()
            entry = tk.Entry(edit_window)
            entry.insert(0, product[details.index(detail) + 1])
            entry.pack()
            entries.append(entry)

        # Add a label and combobox to select the category
        tk.Label(edit_window, text="Catégorie:").pack()
        categorie_box = ttk.Combobox(edit_window, values=self.get_categories())
        categorie_box.set(product[-1][1] if product[-1] else "None")
        categorie_box.pack()

        tk.Button(edit_window, text="Enregistrer",
            command=lambda: self.save_edited_product(product_id, *[entry.get() for entry in entries],
                                                            categorie_box.get(), edit_window)).pack()

    def save_edited_product(self, product_id, nom, description, prix, quantite, categorie_nom, window):
        categorie = self.get_categorie_by_nom(categorie_nom)
        if categorie is None:
            self.my_cursor.execute("INSERT INTO categorie (nom) VALUES (%s)", (categorie_nom,))
            self.mydb.commit()
            categorie = (self.my_cursor.lastrowid, categorie_nom)

        self.my_cursor.execute(
            "UPDATE produit SET nom = %s, description = %s, prix = %s, quantite = %s, id_categorie = %s WHERE id = %s",
            (nom, description, prix, quantite, categorie[0], product_id))
        self.mydb.commit()

        messagebox.showinfo("Succès", "Le produit a été modifié avec succès.")
        self.load_products()
        window.destroy()

    def get_categorie_by_id(self, categorie_id):
        # Fetch a category from the database by ID
        self.my_cursor.execute("SELECT * FROM categorie WHERE id = %s", (categorie_id,))
        row = self.my_cursor.fetchone()
        return (row[0], row[1]) if row else None

    def get_categorie_by_nom(self, categorie_nom):
        # Fetch a category from the database by name
        self.my_cursor.execute("SELECT * FROM categorie WHERE nom = %s", (categorie_nom,))
        row = self.my_cursor.fetchone()
        return (row[0], row[1]) if row else None

    def add_category(self):
        add_window = tk.Toplevel(self.master)
        add_window.title("Ajouter une catégorie")

        nom_label = tk.Label(add_window, text="Nom:")
        nom_label.pack()
        nom_entry = tk.Entry(add_window)
        nom_entry.pack()

        save_button = tk.Button(add_window, text="Enregistrer",
                                command=lambda: self.save_category(nom_entry.get(), add_window))
        save_button.pack()

    def save_category(self, nom, window):
        # Insert the new category into the database
        self.my_cursor.execute("INSERT INTO categorie (nom) VALUES (%s)", (nom,))
        self.mydb.commit()

        messagebox.showinfo("Succès", "La catégorie a été ajoutée avec succès.")
        window.destroy()

    def delete_category(self):
        remove_window = tk.Toplevel(self.master)
        remove_window.title("Supprimer une catégorie")

        nom_label = tk.Label(remove_window, text="Nom:")
        nom_label.pack()

        nom_box = ttk.Combobox(remove_window, values=self.get_categories())
        nom_box.pack()

        save_button = tk.Button(remove_window, text="Supprimer",
                                command=lambda: self.remove_category(nom_box.get(), remove_window))
        save_button.pack()

    def remove_category(self, nom, window):
        self.my_cursor.execute("DELETE FROM categorie WHERE nom = %s", (nom,))
        self.mydb.commit()
        messagebox.showinfo("Succès", "La catégorie a été supprimée avec succès.")
        window.destroy()

    def get_categories(self):
        self.my_cursor.execute("SELECT nom FROM categorie")
        rows = self.my_cursor.fetchall()
        return rows

    def get_all_products(self):
        self.my_cursor.execute("SELECT * FROM produit")
        rows = self.my_cursor.fetchall()
        return rows

    def export_csv(self, filename):
        self.my_cursor.execute("SELECT * FROM produit")
        data = self.my_cursor.fetchall()

        # Write the data to a CSV file
        with open(filename, 'w', newline='') as csvfile:
            # Write the header row using the column names from self.my_cursor.description
            fieldnames = [i[0] for i in self.my_cursor.description]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Write the data rows
            for row in data:
                writer.writerow(dict(zip(fieldnames, row)))

        messagebox.showinfo("Succès", "Les données ont été exportées avec succès.")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Gestion de stock")
    app = Application(root)
    root.mainloop()