from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, W, filedialog, messagebox
import tkinter as tk
from tkinter import ttk

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

APP_NAME = "EmbedLab Board Tester"
BAUDRATE = 115200


def app_path(*parts: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base).joinpath(*parts)
    return Path(__file__).resolve().parents[1].joinpath(*parts)


def load_json(*parts: str):
    return json.loads(app_path(*parts).read_text(encoding="utf-8"))


class SerialAgent:
    def __init__(self):
        self.ser = None

    def connect(self, port: str) -> str:
        if serial is None:
            raise RuntimeError("pyserial n'est pas installé.")
        if not port:
            raise RuntimeError("Aucun port COM sélectionné.")
        self.close()
        self.ser = serial.Serial(port, BAUDRATE, timeout=1)
        time.sleep(1.5)
        self.ser.reset_input_buffer()
        return self.command("PING", timeout=2)

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def command(self, cmd: str, timeout: float = 1.2) -> str:
        if self.ser is None:
            raise RuntimeError("Port série non connecté.")
        self.ser.write((cmd.strip() + "\n").encode("utf-8"))
        self.ser.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.ser.readline()
            if line:
                return line.decode(errors="replace").strip()
        return "TIMEOUT"


class EmbedLabTester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1220x760")
        self.minsize(1080, 680)

        self.boards = load_json("profiles", "boards.json")
        self.modules = load_json("tests", "modules.json")
        self.pin_mappings = load_json("profiles", "pin_mappings.json")
        self.agent = SerialAgent()
        self.results = []
        self.status_var = tk.StringVar(value="Prêt.")

        self.configure(bg="#f4f8fc")
        self.style_ui()
        self.build_ui()
        self.refresh_ports()
        self.refresh_board_info()
        self.refresh_modules()

    def style_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f4f8fc")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Title.TLabel", background="#f4f8fc", foreground="#061E39", font=("Segoe UI", 22, "bold"))
        style.configure("H.TLabel", background="#ffffff", foreground="#061E39", font=("Segoe UI", 12, "bold"))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 9))
        style.configure("TLabel", background="#ffffff", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#eef6ff", foreground="#0B4775", font=("Segoe UI", 9, "bold"))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def build_ui(self):
        header = ttk.Frame(self, padding=16)
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor=W)
        ttk.Label(
            header,
            text="Diagnostic guidé : choix microcontrôleur, mapping des broches, câblage, test et rapport.",
            background="#f4f8fc",
            foreground="#0B4775",
        ).pack(anchor=W)

        main = ttk.Frame(self, padding=(16, 0, 16, 16))
        main.pack(fill=BOTH, expand=True)

        left = ttk.Frame(main, padding=12, style="Card.TFrame")
        left.pack(side=LEFT, fill="y", padx=(0, 12))

        right = ttk.Frame(main, padding=12, style="Card.TFrame")
        right.pack(side=RIGHT, fill=BOTH, expand=True)

        ttk.Label(left, text="1. Configuration", style="H.TLabel").pack(anchor=W)
        ttk.Label(left, text="Microcontrôleur").pack(anchor=W, pady=(12, 2))
        self.board_id = tk.StringVar(value=self.boards[0]["id"])
        self.board_combo = ttk.Combobox(left, textvariable=self.board_id, values=[b["id"] for b in self.boards], state="readonly", width=30)
        self.board_combo.pack(anchor=W)
        self.board_combo.bind("<<ComboboxSelected>>", lambda _e: self.on_board_changed())

        ttk.Label(left, text="Port COM").pack(anchor=W, pady=(12, 2))
        self.port = tk.StringVar()
        self.port_combo = ttk.Combobox(left, textvariable=self.port, values=[], state="readonly", width=30)
        self.port_combo.pack(anchor=W)
        ttk.Button(left, text="Actualiser les ports", command=self.refresh_ports).pack(anchor=W, pady=(6, 0))

        ttk.Label(left, text="Type de test").pack(anchor=W, pady=(12, 2))
        self.mode = tk.StringVar(value="rapide")
        for text, value in [("Rapide", "rapide"), ("Complet", "complet"), ("Ciblé", "cible")]:
            ttk.Radiobutton(left, text=text, value=value, variable=self.mode, command=self.refresh_modules).pack(anchor=W)

        ttk.Button(left, text="Téléverser firmware agent", command=self.upload_firmware, style="Accent.TButton").pack(fill="x", pady=(16, 4))
        ttk.Button(left, text="Connecter / PING", command=self.connect_serial).pack(fill="x", pady=4)
        ttk.Button(left, text="Exporter rapport CSV", command=self.export_csv).pack(fill="x", pady=4)

        status_frame = ttk.Frame(left, padding=8, style="Card.TFrame")
        status_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel", wraplength=300).pack(fill="x")

        ttk.Label(left, text="Plan de câblage", style="H.TLabel").pack(anchor=W, pady=(14, 0))
        self.board_text = tk.Text(left, height=15, width=39, bg="#eef6ff", relief="flat", wrap="word")
        self.board_text.pack(fill="x", pady=(6, 0))

        ttk.Label(right, text="2. Modules à tester", style="H.TLabel").pack(anchor=W)
        ttk.Label(right, text="La colonne Étape indique quand il faut changer le câblage si la carte manque de broches.", style="Muted.TLabel").pack(anchor=W)
        columns = ("id", "module", "stage", "mapping")
        self.module_table = ttk.Treeview(right, columns=columns, show="headings", height=9)
        self.module_table.heading("id", text="ID")
        self.module_table.heading("module", text="Module")
        self.module_table.heading("stage", text="Étape")
        self.module_table.heading("mapping", text="Brochage proposé")
        self.module_table.column("id", width=130)
        self.module_table.column("module", width=280)
        self.module_table.column("stage", width=210)
        self.module_table.column("mapping", width=360)
        self.module_table.pack(fill="x", pady=(6, 10))
        self.module_table.bind("<<TreeviewSelect>>", lambda _e: self.show_selected_module())

        btns = ttk.Frame(right, style="Card.TFrame")
        btns.pack(fill="x")
        ttk.Button(btns, text="Afficher câblage", command=self.show_selected_module).pack(side=LEFT, padx=(0, 8))
        ttk.Button(btns, text="Lancer commandes possibles", command=self.run_selected_module, style="Accent.TButton").pack(side=LEFT, padx=8)
        ttk.Button(btns, text="Résultat OK", command=lambda: self.add_result("OK")).pack(side=LEFT, padx=8)
        ttk.Button(btns, text="Défaut", command=lambda: self.add_result("DEFAUT")).pack(side=LEFT, padx=8)
        ttk.Button(btns, text="Non testé", command=lambda: self.add_result("NON_TESTE")).pack(side=LEFT, padx=8)

        ttk.Label(right, text="3. Câblage et protocole", style="H.TLabel").pack(anchor=W, pady=(12, 0))
        self.details = tk.Text(right, height=11, bg="#ffffff", relief="solid", borderwidth=1, wrap="word", font=("Segoe UI", 10))
        self.details.pack(fill=BOTH, expand=True, pady=(6, 8))

        ttk.Label(right, text="4. Journal", style="H.TLabel").pack(anchor=W)
        self.log = tk.Text(right, height=7, bg="#111827", fg="#e5e7eb", relief="flat", wrap="word", font=("Consolas", 9))
        self.log.pack(fill="x", expand=False, pady=(6, 0))
        self.write_log("Journal prêt. Les messages de compilation/téléversement apparaîtront ici.")

    def current_board(self):
        return next(b for b in self.boards if b["id"] == self.board_id.get())

    def current_mapping_profile(self):
        return self.pin_mappings.get(self.board_id.get(), {"stages": []})

    def module_by_id(self, module_id: str):
        return next(m for m in self.modules if m["id"] == module_id)

    def selected_module_id(self):
        sel = self.module_table.selection()
        if not sel:
            return None
        return self.module_table.item(sel[0], "values")[0]

    def selected_module(self):
        module_id = self.selected_module_id()
        if not module_id:
            return None
        return self.module_by_id(module_id)

    def on_board_changed(self):
        self.refresh_board_info()
        self.refresh_modules()

    def refresh_ports(self):
        ports = [p.device for p in list_ports.comports()] if list_ports else []
        self.port_combo["values"] = ports
        if ports and not self.port.get():
            self.port.set(ports[0])
        self.set_status(f"{len(ports)} port(s) COM détecté(s)." if ports else "Aucun port COM détecté.")

    def set_status(self, text: str):
        self.status_var.set(text)
        self.update_idletasks()

    def refresh_board_info(self):
        b = self.current_board()
        mapping = self.current_mapping_profile()
        lines = [
            f"Carte : {b['name']}",
            f"Tension logique : {b['logic_voltage']}",
            f"Téléversement : {b['upload_mode']}",
            f"Stratégie : {b.get('recommended_strategy', 'non précisée')}",
            "",
            "Rappels :",
            "- J10 sur 5 V pour Arduino Uno/Nano/Mega.",
            "- J10 sur 3,3 V pour ESP32/STM32.",
            "- GND commun obligatoire.",
            "- Moteurs/charges sur alimentation externe.",
            "",
            "Étapes de câblage prévues :",
        ]
        for idx, stage in enumerate(mapping.get("stages", []), start=1):
            modules = ", ".join(stage.get("modules", {}).keys())
            lines.append(f"{idx}. {stage['name']} : {modules}")
        lines.extend(["", b.get("notes", "")])
        self.board_text.delete("1.0", END)
        self.board_text.insert("1.0", "\n".join(lines))

    def module_mapping(self, module_id: str):
        profile = self.current_mapping_profile()
        for stage in profile.get("stages", []):
            modules = stage.get("modules", {})
            if module_id in modules:
                return stage, modules[module_id]
        return None, None

    def mapping_summary(self, mapping) -> str:
        if not mapping:
            return "à définir manuellement"
        pairs = []
        for key in ("pin", "pin1", "pin2", "pin3", "pin4", "pin5", "pin6", "pin7", "pin8", "sda", "scl", "ds", "st", "sh", "rs", "en", "d4", "d5", "d6", "d7", "addr"):
            if key in mapping:
                pairs.append(f"{key}={mapping[key]}")
        if "pins" in mapping:
            pairs.append("pins=" + ",".join(mapping["pins"]))
        return " ; ".join(pairs) if pairs else mapping.get("note", "voir détails")

    def refresh_modules(self):
        for item in self.module_table.get_children():
            self.module_table.delete(item)
        mode = self.mode.get()
        mods = self.modules
        if mode == "rapide":
            mods = [m for m in mods if m.get("level") == "basic"][:7]
        for m in mods:
            stage, mapping = self.module_mapping(m["id"])
            stage_name = stage["name"] if stage else "manuel"
            self.module_table.insert(
                "",
                END,
                iid=m["id"],
                values=(m["id"], m["name"], stage_name, self.mapping_summary(mapping)),
            )

    def show_selected_module(self):
        m = self.selected_module()
        if not m:
            messagebox.showwarning(APP_NAME, "Sélectionnez un module.")
            return
        stage, mapping = self.module_mapping(m["id"])
        lines = [
            f"MODULE : {m['name']}",
            f"Famille : {m['category']} | Niveau : {m['level']}",
            "",
            "ÉTAPE DE CÂBLAGE :",
            stage["name"] if stage else "Mapping manuel à définir",
            "",
            "BROCHAGE PROPOSÉ :",
        ]
        if mapping:
            if "embedlab" in mapping:
                lines.append(f"- Côté EmbedLab : {mapping['embedlab']}")
            for key, value in mapping.items():
                if key in ("embedlab", "note"):
                    continue
                if isinstance(value, list):
                    lines.append(f"- {key} microcontrôleur : {', '.join(value)}")
                else:
                    lines.append(f"- {key} microcontrôleur : {value}")
            if mapping.get("note"):
                lines.append(f"- Note : {mapping['note']}")
        else:
            lines.append("- Aucun mapping automatique disponible pour cette carte/module.")
        lines.extend([
            "",
            "CÂBLAGE À RÉALISER :",
            *[f"- {x}" for x in m.get("wiring", [])],
            "",
            "PROTOCOLE DE TEST :",
            *[f"- {x}" for x in m.get("protocol", [])],
            "",
            "RÉSULTAT ATTENDU :",
            m.get("expected", ""),
            "",
            "PISTE DE DÉPANNAGE SI ÉCHEC :",
            m.get("fault_hint", ""),
        ])
        self.details.delete("1.0", END)
        self.details.insert("1.0", "\n".join(lines))

    def write_log(self, text: str):
        self.log.insert(END, text + "\n")
        self.log.see(END)
        self.update_idletasks()

    def upload_firmware(self):
        b = self.current_board()
        port = self.port.get()
        self.write_log("=== Demande de téléversement du firmware agent ===")
        self.set_status("Préparation du téléversement...")

        if not port:
            self.set_status("Téléversement impossible : aucun port COM sélectionné.")
            messagebox.showwarning(APP_NAME, "Sélectionnez d'abord le port COM du microcontrôleur.")
            return

        if b.get("upload_mode") != "arduino-cli" or not b.get("fqbn"):
            self.set_status("Profil non compatible avec le téléversement automatique.")
            messagebox.showinfo(
                APP_NAME,
                "Le téléversement automatique n'est pas encore activé pour ce profil.\n"
                "Utilisez le mode guidé ou ajoutez la méthode de flash adaptée.",
            )
            return

        arduino_cli = shutil.which("arduino-cli")
        if arduino_cli is None:
            self.set_status("arduino-cli introuvable : impossible de téléverser automatiquement.")
            self.write_log("ERREUR : arduino-cli introuvable dans le PATH.")
            messagebox.showerror(
                APP_NAME,
                "arduino-cli est introuvable.\n\n"
                "Installez Arduino CLI ou ajoutez arduino-cli.exe au PATH Windows, puis relancez l'application.\n\n"
                "Test rapide dans PowerShell :\narduino-cli version",
            )
            return

        firmware = app_path("firmware", "arduino_agent")
        if not firmware.exists():
            self.set_status("Dossier firmware introuvable.")
            self.write_log(f"ERREUR : dossier firmware introuvable : {firmware}")
            messagebox.showerror(APP_NAME, f"Dossier firmware introuvable :\n{firmware}")
            return

        commands = [
            [arduino_cli, "compile", "--fqbn", b["fqbn"], str(firmware)],
            [arduino_cli, "upload", "-p", port, "--fqbn", b["fqbn"], str(firmware)],
        ]

        self.write_log(f"Carte : {b['name']}")
        self.write_log(f"Port : {port}")
        self.write_log(f"FQBN : {b['fqbn']}")
        self.write_log(f"Firmware : {firmware}")
        self.write_log(f"Arduino CLI : {arduino_cli}")
        self.set_status("Compilation en cours... Consultez le journal en bas à droite.")
        messagebox.showinfo(
            APP_NAME,
            "Le téléversement est lancé.\n\n"
            "Regardez le journal en bas à droite pour voir la compilation et l'upload.\n"
            "Si l'Arduino redémarre, attendez la fin avant de cliquer sur Connecter / PING.",
        )

        def ui_log(text: str):
            self.after(0, self.write_log, text)

        def ui_status(text: str):
            self.after(0, self.set_status, text)

        def ui_error(text: str):
            self.after(0, messagebox.showerror, APP_NAME, text)

        def ui_info(text: str):
            self.after(0, messagebox.showinfo, APP_NAME, text)

        def worker():
            for index, cmd in enumerate(commands, start=1):
                phase = "Compilation" if index == 1 else "Téléversement"
                ui_status(f"{phase} en cours...")
                ui_log("> " + " ".join(cmd))
                try:
                    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
                except FileNotFoundError:
                    ui_status("arduino-cli introuvable.")
                    ui_log("ERREUR : arduino-cli introuvable.")
                    ui_error("arduino-cli est introuvable. Ajoutez-le au PATH Windows.")
                    return
                if p.stdout:
                    ui_log(p.stdout.strip())
                if p.stderr:
                    ui_log(p.stderr.strip())
                if p.returncode:
                    ui_status(f"{phase} échouée. Voir le journal.")
                    ui_log(f"ERREUR : code retour {p.returncode}")
                    ui_error(f"{phase} échouée. Consultez le journal en bas à droite.")
                    return
            ui_status("Firmware agent téléversé. Cliquez maintenant sur Connecter / PING.")
            ui_log("OK : firmware agent téléversé.")
            ui_info("Firmware agent téléversé. Cliquez maintenant sur Connecter / PING.")

        threading.Thread(target=worker, daemon=True).start()

    def connect_serial(self):
        try:
            self.set_status("Connexion série en cours...")
            response = self.agent.connect(self.port.get())
            self.write_log("> PING")
            self.write_log("< " + response)
            self.set_status("Connexion série OK : " + response)
            messagebox.showinfo(APP_NAME, "Connexion série OK : " + response)
        except Exception as exc:
            self.set_status("Connexion série impossible.")
            messagebox.showerror(APP_NAME, str(exc))

    def resolve_command(self, cmd: str, mapping) -> str | None:
        if not mapping:
            return None
        resolved = cmd
        for key, value in mapping.items():
            if isinstance(value, str):
                resolved = resolved.replace("{" + key + "}", value)
        if "{pin}" in resolved and isinstance(mapping.get("pins"), list) and mapping["pins"]:
            resolved = resolved.replace("{pin}", mapping["pins"][0])
        if "{" in resolved or "}" in resolved:
            return None
        return resolved

    def run_selected_module(self):
        m = self.selected_module()
        if not m:
            messagebox.showwarning(APP_NAME, "Sélectionnez un module.")
            return
        stage, mapping = self.module_mapping(m["id"])
        self.write_log("=== " + m["name"] + " ===")
        if stage:
            self.write_log("Étape de câblage : " + stage["name"])
        if mapping:
            self.write_log("Brochage : " + self.mapping_summary(mapping))
        else:
            self.write_log("Aucun mapping automatique : test manuel.")

        for raw_cmd in m.get("commands", []):
            cmd = self.resolve_command(raw_cmd, mapping)
            if cmd is None:
                self.write_log("À paramétrer : " + raw_cmd)
                continue
            if cmd.startswith("WAIT "):
                try:
                    delay = int(cmd.split()[1]) / 1000
                    self.write_log(f"Attente {delay:.1f} s")
                    time.sleep(delay)
                except ValueError:
                    self.write_log("Commande WAIT invalide : " + cmd)
                continue
            try:
                response = self.agent.command(cmd)
                self.write_log("> " + cmd)
                self.write_log("< " + response)
            except Exception as exc:
                self.write_log("ERREUR : " + str(exc))
                break
        self.write_log("Observation : " + m.get("expected", ""))

    def add_result(self, result: str):
        m = self.selected_module()
        if not m:
            messagebox.showwarning(APP_NAME, "Sélectionnez un module.")
            return
        stage, mapping = self.module_mapping(m["id"])
        self.results.append({
            "date": datetime.now().isoformat(timespec="seconds"),
            "microcontroleur": self.current_board()["name"],
            "port": self.port.get(),
            "etape": stage["name"] if stage else "manuel",
            "module": m["name"],
            "brochage": self.mapping_summary(mapping),
            "resultat": result,
            "note": m.get("fault_hint", "") if result == "DEFAUT" else "",
        })
        self.write_log(f"Résultat enregistré : {m['name']} -> {result}")

    def export_csv(self):
        if not self.results:
            messagebox.showinfo(APP_NAME, "Aucun résultat à exporter.")
            return
        name = "rapport_test_embedlab_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=name, filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.results[0].keys()))
            writer.writeheader()
            writer.writerows(self.results)
        messagebox.showinfo(APP_NAME, "Rapport exporté.")


if __name__ == "__main__":
    EmbedLabTester().mainloop()
