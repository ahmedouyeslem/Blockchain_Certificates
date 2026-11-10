import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

# CertiChain - Educational blockchain demo
# This is a local simulation, not a public blockchain.

def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def canonical_json(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def normalize_matricule(value):
    """Normalize matricule text for duplicate detection."""
    return " ".join(str(value).split()).casefold()

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        return sha256(canonical_json(content))

class CertificateBlockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, datetime.now().isoformat(timespec="seconds"),
                     {"message": "Genesis Block"}, "0")

    def add_certificate(self, certificate):
        previous = self.chain[-1]
        block = Block(len(self.chain), datetime.now().isoformat(timespec="seconds"),
                      certificate, previous.hash)
        self.chain.append(block)
        return block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False, f"Le hash du Block {i} a été modifié."
            if current.previous_hash != previous.hash:
                return False, f"Le lien avec le Block {i - 1} est invalide."
        return True, "La chaîne Blockchain est valide."

class CertiChainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CertiChain | Vérification des diplômes")
        self.root.geometry("850x650")
        self.root.minsize(760, 580)
        self.blockchain = CertificateBlockchain()
        self.certificates = {}
        self.dataset_path = Path(__file__).resolve().with_name("certificates_dataset.json")
        self.dataset_loaded_count = 0
        self.load_dataset()

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#14564f")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#555555")
        style.configure("TButton", padding=7)
        style.configure("Treeview", rowheight=26)

        header = ttk.Frame(root, padding=(18, 15))
        header.pack(fill="x")
        ttk.Label(header, text="CertiChain", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Certification et authentification des diplômes par Blockchain (simulation pédagogique)",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.issue_tab = ttk.Frame(self.notebook, padding=16)
        self.verify_tab = ttk.Frame(self.notebook, padding=16)
        self.chain_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.issue_tab, text="Émettre un diplôme")
        self.notebook.add(self.verify_tab, text="Vérifier")
        self.notebook.add(self.chain_tab, text="Blockchain")

        self.build_issue_tab()
        self.build_verify_tab()
        self.build_chain_tab()
        self.refresh_chain_view()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event=None):
        if self.notebook.select() == str(self.chain_tab):
            self.refresh_chain_view()

    def load_dataset(self):
        """Load the JSON dataset into the in-memory blockchain."""
        if not self.dataset_path.exists():
            messagebox.showwarning(
                "Fichier JSON introuvable",
                "Le fichier certificates_dataset.json est absent.\\n\\n"
                f"Placez-le dans le même dossier que :\\n{Path(__file__).resolve()}"
            )
            return
        try:
            with self.dataset_path.open("r", encoding="utf-8") as file:
                dataset = json.load(file)
            records = dataset.get("certificates", [])
            loaded_matricules = set()
            for record in records:
                if not isinstance(record, dict):
                    continue
                certificate = dict(record)
                normalized = normalize_matricule(certificate.get("matricule", ""))
                if not normalized or normalized in loaded_matricules:
                    continue
                loaded_matricules.add(normalized)
                certificate.pop("certificate_hash", None)
                certificate["certificate_hash"] = sha256(canonical_json(certificate))
                block = self.blockchain.add_certificate(certificate)
                self.certificates[str(block.index)] = certificate
                self.dataset_loaded_count += 1
        except (OSError, json.JSONDecodeError, TypeError) as error:
            messagebox.showwarning(
                "Dataset JSON",
                f"Impossible de charger certificates_dataset.json :\\n{error}"
            )

    def save_dataset(self):
        """Persist issued certificates to the JSON dataset."""
        records = []
        for certificate in self.certificates.values():
            records.append({
                key: value for key, value in certificate.items()
                if key != "certificate_hash"
            })
        payload = {
            "dataset_name": "CertiChain university diploma demo dataset",
            "note": (
                "Records are fictional demonstration data, not verified real people "
                "or official university credentials."
            ),
            "certificates": records,
        }
        try:
            with self.dataset_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showwarning(
                "Enregistrement JSON",
                f"Impossible d'enregistrer le dataset :\\n{error}"
            )

    def build_issue_tab(self):
        ttk.Label(self.issue_tab, text="Émission d'un diplôme", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
        )
        fields = [
            ("Matricule de l'étudiant", "matricule"),
            ("Nom de l'étudiant", "student"),
            ("Université", "university"),
            ("Filière", "field"),
            ("Diplôme", "degree"),
            ("Année d'obtention", "year"),
        ]
        self.entries = {}
        for row, (label, key) in enumerate(fields, start=1):
            ttk.Label(self.issue_tab, text=label + " :").grid(row=row, column=0, sticky="w", pady=7)
            entry = ttk.Entry(self.issue_tab, width=48)
            entry.grid(row=row, column=1, sticky="ew", pady=7, padx=(12, 0))
            self.entries[key] = entry

        self.issue_tab.columnconfigure(1, weight=1)
        ttk.Button(self.issue_tab, text="Émettre le diplôme et l'ajouter à la Blockchain",
                   command=self.issue_certificate).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(18, 10)
        )
        self.issue_result = tk.Text(self.issue_tab, height=7, wrap="word", state="disabled",
                                    font=("Consolas", 9))
        self.issue_result.grid(row=8, column=0, columnspan=2, sticky="nsew")
        self.issue_tab.rowconfigure(8, weight=1)

    def build_verify_tab(self):
        ttk.Label(self.verify_tab, text="Vérification d'un diplôme", style="Title.TLabel").pack(
            anchor="w", pady=(0, 12)
        )
        line = ttk.Frame(self.verify_tab)
        line.pack(fill="x")
        ttk.Label(line, text="ID du diplôme / Matricule :").pack(side="left")
        self.verify_id = ttk.Entry(line, width=28)
        self.verify_id.pack(side="left", padx=10)
        ttk.Button(line, text="Vérifier", command=self.verify_certificate).pack(side="left")
        self.verify_result = tk.Text(self.verify_tab, height=15, wrap="word", state="disabled")
        self.verify_result.pack(fill="both", expand=True, pady=(16, 0))

    def build_chain_tab(self):
        self.blockchain_title = ttk.Label(
            self.chain_tab, text="Blockchain — détails des blocs",
            style="Title.TLabel"
        )
        self.blockchain_title.pack(anchor="w", pady=(0, 10))

        columns = ("index", "date", "matricule", "student", "hash")
        self.tree = ttk.Treeview(self.chain_tab, columns=columns,
                                 show="headings", height=8)
        headings = {
            "index": "Block", "date": "Date", "matricule": "Matricule",
            "student": "Étudiant", "hash": "Hash du bloc"
        }
        widths = {"index": 55, "date": 150, "matricule": 120,
                  "student": 180, "hash": 220}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="x", expand=False)
        self.tree.bind("<<TreeviewSelect>>", self.show_selected_block_details)

        ttk.Label(self.chain_tab,
                  text="Informations complètes du bloc sélectionné :").pack(
                      anchor="w", pady=(10, 4))

        details_frame = ttk.Frame(self.chain_tab)
        details_frame.pack(fill="both", expand=True)
        self.block_details = tk.Text(details_frame, wrap="word", height=10,
                                     state="disabled", font=("Consolas", 9))
        details_scroll = ttk.Scrollbar(details_frame, orient="vertical",
                                       command=self.block_details.yview)
        self.block_details.configure(yscrollcommand=details_scroll.set)
        self.block_details.pack(side="left", fill="both", expand=True)
        details_scroll.pack(side="right", fill="y")

        bottom = ttk.Frame(self.chain_tab)
        bottom.pack(fill="x", pady=(10, 0))
        ttk.Button(bottom, text="Afficher tous les blocs",
                   command=self.show_all_block_details).pack(side="left")
        ttk.Button(bottom, text="Vérifier l'intégrité de la chaîne",
                   command=self.check_chain).pack(side="left", padx=(8, 0))
        self.chain_status = ttk.Label(bottom, text="Chaîne prête.")
        self.chain_status.pack(side="left", padx=12)

    def show_selected_block_details(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        try:
            block_index = int(self.tree.item(selection[0], "values")[0])
            block = self.blockchain.chain[block_index]
        except (ValueError, IndexError, TypeError):
            return

        details = {
            "index": block.index,
            "timestamp": block.timestamp,
            "data": block.data,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "calculated_hash": block.calculate_hash(),
            "hash_matches": block.hash == block.calculate_hash()
        }
        self.set_text(self.block_details,
                      json.dumps(details, ensure_ascii=False, indent=2))

    def show_all_block_details(self):
        details = []
        for block in self.blockchain.chain:
            details.append({
                "index": block.index,
                "timestamp": block.timestamp,
                "data": block.data,
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "calculated_hash": block.calculate_hash(),
                "hash_matches": block.hash == block.calculate_hash()
            })
        self.set_text(self.block_details,
                      json.dumps(details, ensure_ascii=False, indent=2))

    def set_text(self, widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def issue_certificate(self):
        certificate = {key: entry.get().strip() for key, entry in self.entries.items()}
        if any(not value for value in certificate.values()):
            messagebox.showwarning("Champs manquants", "Veuillez remplir tous les champs.")
            return

        # Keep student matricules unique so they can be used for reliable lookup.
        matricule = normalize_matricule(certificate["matricule"])
        if any(
            normalize_matricule(existing.get("matricule", "")) == matricule
            for existing in self.certificates.values()
        ):
            messagebox.showwarning(
                "Matricule déjà utilisé",
                "Ce matricule existe déjà. Veuillez saisir un matricule unique."
            )
            return

        certificate["certificate_hash"] = sha256(canonical_json(certificate))
        block = self.blockchain.add_certificate(certificate)
        cert_id = str(block.index)
        self.certificates[cert_id] = certificate
        self.save_dataset()
        self.verify_id.delete(0, "end")
        self.verify_id.insert(0, cert_id)

        result = (
            "Diplôme émis avec succès !\n\n"
            f"ID du diplôme : {cert_id}\n"
            f"Matricule : {certificate['matricule']}\n"
            f"Étudiant : {certificate['student']}\n"
            f"Diplôme : {certificate['degree']} {certificate['field']}\n"
            f"Université : {certificate['university']}\n"
            f"Année : {certificate['year']}\n\n"
            f"Hash du diplôme :\n{certificate['certificate_hash']}\n\n"
            f"Hash du bloc :\n{block.hash}\n"
        )
        self.set_text(self.issue_result, result)
        self.refresh_chain_view()
        # Reset the form after successful issuance so the next record starts blank.
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.entries["matricule"].focus_set()
        messagebox.showinfo("CertiChain", f"Le diplôme a été ajouté au Block {cert_id}.")

    def verify_certificate(self):
        search_value = self.verify_id.get().strip()
        cert_id = search_value
        certificate = self.certificates.get(search_value)

        # If the input is not a block/certificate ID, search by student matricule.
        if certificate is None:
            for stored_id, stored_certificate in self.certificates.items():
                if stored_certificate.get("matricule", "").casefold() == search_value.casefold():
                    cert_id = stored_id
                    certificate = stored_certificate
                    break

        if not certificate:
            self.set_text(
                self.verify_result,
                "Diplôme introuvable. Vérifiez l'ID du diplôme ou le matricule de l'étudiant."
            )
            return

        current_data = {k: v for k, v in certificate.items() if k != "certificate_hash"}
        calculated = sha256(canonical_json(current_data))
        chain_valid, chain_message = self.blockchain.is_valid()
        is_valid = calculated == certificate["certificate_hash"] and chain_valid

        status = "DIPLÔME AUTHENTIQUE" if is_valid else "DIPLÔME INVALIDE OU MODIFIÉ"
        result = (
            f"Résultat : {status}\n\n"
            f"ID du diplôme : {cert_id}\n"
            f"Matricule : {certificate.get('matricule', '')}\n"
            f"Étudiant : {certificate.get('student', '')}\n"
            f"Université : {certificate.get('university', '')}\n"
            f"Diplôme : {certificate.get('degree', '')} {certificate.get('field', '')}\n"
            f"Année : {certificate.get('year', '')}\n\n"
            f"Vérification Blockchain : {chain_message}\n"
            f"Hash enregistré : {certificate['certificate_hash']}\n"
            f"Hash recalculé : {calculated}\n"
        )
        self.set_text(self.verify_result, result)

    def tamper_certificate(self):
        cert_id = self.verify_id.get().strip()
        certificate = self.certificates.get(cert_id)
        if not certificate:
            messagebox.showwarning("Aucun diplôme", "Émettez ou choisissez un diplôme valide d'abord.")
            return
        certificate["student"] = certificate.get("student", "") + " (MODIFIÉ)"
        self.set_text(
            self.verify_result,
            "Une modification de démonstration a été appliquée au nom de l'étudiant.\n"
            "Cliquez maintenant sur « Vérifier » : le hash ne correspondra plus.\n\n"
            "Ceci illustre la détection d'une modification des données."
        )
        self.refresh_chain_view()

    def check_chain(self):
        valid, message = self.blockchain.is_valid()
        self.chain_status.configure(text=("VALIDÉE — " if valid else "ERREUR — ") + message)
        messagebox.showinfo("Intégrité Blockchain", message)

    def refresh_chain_view(self):
        self.blockchain_title.configure(
            text=f"Blockchain — détails des blocs ({len(self.blockchain.chain)} blocs)"
        )
        for item in self.tree.get_children():
            self.tree.delete(item)
        for block in self.blockchain.chain:
            data = block.data
            self.tree.insert(
                "", "end", iid=str(block.index),
                values=(block.index, block.timestamp,
                        data.get("matricule", "—"),
                        data.get("student", "Genesis Block"), block.hash)
            )
        self.show_all_block_details()

if __name__ == "__main__":
    root = tk.Tk()
    app = CertiChainApp(root)
    root.mainloop()
