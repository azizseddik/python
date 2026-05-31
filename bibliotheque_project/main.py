import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
import chatbot as chat

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = '#1a1d2e'
SIDEBAR  = '#252840'
CARD     = '#2d3153'
ACCENT   = '#5b8cff'
SUCCESS  = '#3ddc84'
DANGER   = '#ff5c5c'
WARNING  = '#ffb347'
TEXT     = '#e8eaf6'
DIM      = '#8c8fa8'
BORDER   = '#3a3f6b'
USER_CLR = '#7ec8e3'
BOT_CLR  = '#b0c4ff'


# ── Helpers ───────────────────────────────────────────────────────────────────
def flat_btn(parent, text, command, bg=ACCENT, fg='white', **kw):
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
        font=('Segoe UI', 10, 'bold'), relief='flat',
        cursor='hand2', padx=14, pady=8, **kw
    )


def label(parent, text, size=10, bold=False, color=TEXT, **kw):
    font = ('Segoe UI', size, 'bold' if bold else 'normal')
    return tk.Label(parent, text=text, bg=parent['bg'], fg=color,
                    font=font, **kw)


def entry(parent, textvariable=None, width=30, **kw):
    return tk.Entry(
        parent, textvariable=textvariable, width=width,
        bg=CARD, fg=TEXT, insertbackground=TEXT,
        font=('Segoe UI', 11), relief='flat', **kw
    )


# ── Dialog: Add / Edit Livre ──────────────────────────────────────────────────
class LivreDialog(tk.Toplevel):
    CATEGORIES = ['Roman', 'Science', 'Histoire', 'Informatique',
                  'Philosophie', 'Poésie', 'Biographie', 'Autre']
    STATUTS    = ['disponible', 'emprunté', 'réservé']

    def __init__(self, parent, on_save, titre_fenetre='Livre', livre=None):
        super().__init__(parent)
        self.title(titre_fenetre)
        self.configure(bg=SIDEBAR)
        self.resizable(False, False)
        self.grab_set()
        self.on_save = on_save

        W, H = 520, 500
        self.geometry(f'{W}x{H}')
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry(f'+{px + (pw - W)//2}+{py + (ph - H)//2}')

        self._build(livre)

    def _build(self, livre):
        label(self, self.title(), size=14, bold=True).pack(pady=(22, 18))

        form = tk.Frame(self, bg=SIDEBAR)
        form.pack(fill='x', padx=30)

        self.vars = {}
        fields = [
            ('titre',               'Titre *',               'entry',  None),
            ('auteur',              'Auteur *',               'entry',  None),
            ('categorie',           'Catégorie',              'combo',  self.CATEGORIES),
            ('annee_publication',   'Année de publication',   'entry',  None),
            ('quantite_disponible', 'Quantité disponible',    'entry',  None),
            ('statut',              'Statut',                 'combo',  self.STATUTS),
        ]

        for row_i, (key, lbl, kind, opts) in enumerate(fields):
            label(form, lbl, size=9, color=DIM).grid(
                row=row_i, column=0, sticky='w', pady=(10, 2))

            var = tk.StringVar()
            if kind == 'combo':
                w = ttk.Combobox(form, textvariable=var, values=opts,
                                 state='readonly', width=36,
                                 font=('Segoe UI', 11))
                w.set(opts[0])
            else:
                w = entry(form, textvariable=var, width=38)

            w.grid(row=row_i, column=1, sticky='ew', pady=(10, 2), padx=(12, 0))
            self.vars[key] = var

            if livre and livre.get(key) is not None:
                var.set(str(livre[key]))

        # Buttons
        bf = tk.Frame(self, bg=SIDEBAR)
        bf.pack(fill='x', padx=30, pady=24)

        flat_btn(bf, '✕  Annuler', self.destroy,
                 bg=CARD, fg=DIM).pack(side='right', padx=(6, 0))
        flat_btn(bf, '💾  Enregistrer', self._save,
                 bg=ACCENT).pack(side='right')

    def _save(self):
        d = {k: v.get().strip() for k, v in self.vars.items()}
        if not d['titre'] or not d['auteur']:
            messagebox.showwarning('Champs requis',
                                   'Le titre et l\'auteur sont obligatoires.',
                                   parent=self)
            return
        try:
            d['annee_publication']   = int(d['annee_publication'])   if d['annee_publication']   else None
            d['quantite_disponible'] = int(d['quantite_disponible']) if d['quantite_disponible'] else 0
        except ValueError:
            messagebox.showwarning('Valeur invalide',
                                   'L\'année et la quantité doivent être des nombres entiers.',
                                   parent=self)
            return
        self.on_save(d)
        self.destroy()


# ── Tab 1: Gestion des Livres ─────────────────────────────────────────────────
class LivresTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()
        self.refresh()

    def _build(self):
        # ── Search bar ──
        top = tk.Frame(self, bg=BG)
        top.pack(fill='x', padx=18, pady=(18, 8))

        label(top, 'Rechercher :', color=DIM).pack(side='left')
        self.search_var = tk.StringVar()
        e = entry(top, textvariable=self.search_var, width=38)
        e.pack(side='left', padx=(8, 6), ipady=5)
        e.bind('<Return>', lambda _: self.search())

        flat_btn(top, '🔍', self.search, bg=ACCENT).pack(side='left', padx=2)
        flat_btn(top, '↺', self.refresh, bg=CARD, fg=DIM).pack(side='left', padx=2)

        # ── Treeview ──
        tv_frame = tk.Frame(self, bg=BG)
        tv_frame.pack(fill='both', expand=True, padx=18, pady=4)

        style = ttk.Style()
        style.configure('Books.Treeview',
                         background=CARD, foreground=TEXT,
                         fieldbackground=CARD, borderwidth=0, rowheight=30)
        style.configure('Books.Treeview.Heading',
                         background=SIDEBAR, foreground=ACCENT,
                         borderwidth=0, relief='flat',
                         font=('Segoe UI', 10, 'bold'))
        style.map('Books.Treeview',
                  background=[('selected', ACCENT)],
                  foreground=[('selected', 'white')])

        cols = ('ID', 'Titre', 'Auteur', 'Catégorie', 'Année', 'Qté', 'Statut')
        self.tree = ttk.Treeview(tv_frame, columns=cols,
                                  show='headings', style='Books.Treeview')

        col_cfg = [
            ('ID',        60,  'center'),
            ('Titre',    260,  'w'),
            ('Auteur',   190,  'w'),
            ('Catégorie',120,  'w'),
            ('Année',     70,  'center'),
            ('Qté',       55,  'center'),
            ('Statut',   110,  'center'),
        ]
        for col, w, anc in col_cfg:
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, anchor=anc, minwidth=40)

        sb = ttk.Scrollbar(tv_frame, orient='vertical',
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure('dispo',  foreground='#90ee90')
        self.tree.tag_configure('ndispo', foreground='#ff9999')
        self.tree.tag_configure('reserv', foreground=WARNING)

        # ── Action buttons ──
        bot = tk.Frame(self, bg=BG)
        bot.pack(fill='x', padx=18, pady=(6, 16))

        flat_btn(bot, '＋  Ajouter',   self._add,    bg='#1b6b30').pack(side='left', padx=(0, 6))
        flat_btn(bot, '✏  Modifier',   self._edit,   bg='#1c3f85').pack(side='left', padx=6)
        flat_btn(bot, '🗑  Supprimer',  self._delete, bg='#7a1515').pack(side='left', padx=6)

        self.status = tk.StringVar(value='')
        label(bot, '', color=DIM).pack(side='right')
        self._status_lbl = tk.Label(bot, textvariable=self.status,
                                    bg=BG, fg=DIM,
                                    font=('Segoe UI', 9))
        self._status_lbl.pack(side='right', padx=10)

    # ── Data ──────────────────────────────────────────────────────────────────
    def refresh(self):
        try:
            livres = db.get_all_livres()
            self._fill(livres)
            self.status.set(f'{len(livres)} livre(s) chargé(s)')
        except Exception as e:
            messagebox.showerror('Erreur base de données', str(e))

    def search(self):
        q = self.search_var.get().strip()
        if not q:
            self.refresh()
            return
        try:
            livres = db.search_livres(q)
            self._fill(livres)
            self.status.set(f'{len(livres)} résultat(s) pour « {q} »')
        except Exception as e:
            messagebox.showerror('Erreur', str(e))

    def _fill(self, livres):
        self.tree.delete(*self.tree.get_children())
        for l in livres:
            tag = ('dispo'  if l['statut'] == 'disponible' else
                   'reserv' if l['statut'] == 'réservé'    else 'ndispo')
            self.tree.insert('', 'end', values=(
                l['id_livre'], l['titre'], l['auteur'],
                l['categorie'], l['annee_publication'] or '',
                l['quantite_disponible'], l['statut'],
            ), tags=(tag,))

    def _sort(self, col):
        data = [(self.tree.set(c, col), c) for c in self.tree.get_children('')]
        try:
            data.sort(key=lambda t: int(t[0]) if t[0].isdigit() else t[0].lower())
        except Exception:
            data.sort()
        for i, (_, iid) in enumerate(data):
            self.tree.move(iid, '', i)

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Sélection', 'Veuillez sélectionner un livre.')
            return None
        return self.tree.item(sel[0])['values']

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self):
        def save(data):
            try:
                db.add_livre(**data)
                self.refresh()
                self.status.set('Livre ajouté.')
            except Exception as e:
                messagebox.showerror('Erreur', str(e))
        LivreDialog(self.winfo_toplevel(), save, titre_fenetre='Ajouter un Livre')

    def _edit(self):
        row = self._selected()
        if row is None:
            return
        livre = db.get_livre_by_id(row[0])
        if not livre:
            messagebox.showerror('Erreur', 'Livre introuvable.')
            return

        def save(data):
            try:
                db.update_livre(row[0], **data)
                self.refresh()
                self.status.set('Livre modifié.')
            except Exception as e:
                messagebox.showerror('Erreur', str(e))

        LivreDialog(self.winfo_toplevel(), save,
                    titre_fenetre='Modifier le Livre', livre=livre)

    def _delete(self):
        row = self._selected()
        if row is None:
            return
        if messagebox.askyesno('Confirmer la suppression',
                               f'Supprimer « {row[1]} » définitivement ?',
                               parent=self.winfo_toplevel()):
            try:
                db.delete_livre(row[0])
                self.refresh()
                self.status.set('Livre supprimé.')
            except Exception as e:
                messagebox.showerror('Erreur', str(e))


# ── Tab 2: Chatbot IA ─────────────────────────────────────────────────────────
class ChatbotTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.history = []
        self._build()
        self._append('🤖 Assistant',
                     'Bonjour ! Je suis votre assistant bibliothécaire IA.\n'
                     'Posez-moi des questions sur les livres disponibles.\n'
                     'Exemples :\n'
                     '  • « Le livre avec l\'ID 3 existe-t-il ? »\n'
                     '  • « Quels romans sont disponibles ? »\n'
                     '  • « Je cherche un livre de Victor Hugo. »',
                     'bot')

    def _build(self):
        # ── Thinking label (bottom-most, pack first) ──
        self.thinking_var = tk.StringVar(value='')
        tk.Label(self, textvariable=self.thinking_var,
                 bg=BG, fg=DIM, font=('Segoe UI', 9, 'italic')
                 ).pack(side='bottom', pady=(0, 4))

        # ── Input row (pack second so it sits above the label) ──
        inp_frame = tk.Frame(self, bg=SIDEBAR)
        inp_frame.pack(side='bottom', fill='x', padx=18, pady=(4, 10))

        btn_col = tk.Frame(inp_frame, bg=SIDEBAR)
        btn_col.pack(side='right', fill='y', padx=(6, 0))

        self.send_btn = flat_btn(btn_col, '➤ Envoyer', self._send, bg=ACCENT)
        self.send_btn.pack(fill='x', pady=(0, 4))
        flat_btn(btn_col, '🗑 Effacer', self._clear, bg=CARD, fg=DIM).pack(fill='x')

        self.inp = tk.Text(
            inp_frame, bg=CARD, fg=TEXT, insertbackground=TEXT,
            font=('Segoe UI', 11), relief='flat', height=3,
            padx=10, pady=10, wrap='word',
        )
        self.inp.pack(side='left', fill='both', expand=True)
        self.inp.bind('<Return>',       self._on_enter)
        self.inp.bind('<Shift-Return>', lambda _: None)

        # ── Chat history (fills all remaining space) ──
        hist_frame = tk.Frame(self, bg=BG)
        hist_frame.pack(side='top', fill='both', expand=True, padx=18, pady=(18, 8))

        self.chat = tk.Text(
            hist_frame, bg=CARD, fg=TEXT, font=('Segoe UI', 11),
            relief='flat', state='disabled', wrap='word',
            padx=14, pady=12, spacing1=4, spacing3=4,
        )
        sb = ttk.Scrollbar(hist_frame, command=self.chat.yview)
        self.chat.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.chat.pack(fill='both', expand=True)

        self.chat.tag_configure('lbl_user', foreground=USER_CLR,
                                font=('Segoe UI', 9, 'bold'))
        self.chat.tag_configure('lbl_bot',  foreground=BOT_CLR,
                                font=('Segoe UI', 9, 'bold'))
        self.chat.tag_configure('user', foreground=USER_CLR,
                                font=('Segoe UI', 11))
        self.chat.tag_configure('bot',  foreground=TEXT,
                                font=('Segoe UI', 11))

    # ── Chat helpers ──────────────────────────────────────────────────────────
    def _append(self, sender, text, kind):
        self.chat.configure(state='normal')
        self.chat.insert('end', f'\n{sender} :\n', f'lbl_{kind}')
        self.chat.insert('end', text + '\n', kind)
        self.chat.configure(state='disabled')
        self.chat.see('end')

    def _on_enter(self, event):
        if not (event.state & 0x1):   # Enter alone (no Shift)
            self._send()
            return 'break'

    def _send(self):
        msg = self.inp.get('1.0', 'end').strip()
        if not msg:
            return
        self.inp.delete('1.0', 'end')

        self._append('Vous', msg, 'user')
        self.send_btn.configure(state='disabled')
        self.thinking_var.set('🤖  réflexion en cours…')

        def worker():
            try:
                livres = db.get_all_livres()
                reply, self.history = chat.ask_chatbot(msg, livres, self.history)
            except Exception as e:
                reply = f'Erreur : {e}'
            self.after(0, lambda: self._on_reply(reply))

        threading.Thread(target=worker, daemon=True).start()

    def _on_reply(self, text):
        self._append('🤖 Assistant', text, 'bot')
        self.thinking_var.set('')
        self.send_btn.configure(state='normal')

    def _clear(self):
        self.history = []
        self.chat.configure(state='normal')
        self.chat.delete('1.0', 'end')
        self.chat.configure(state='disabled')
        self._append('🤖 Assistant',
                     'Conversation réinitialisée. Comment puis-je vous aider ?', 'bot')


# ── Main Window ───────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Bibliothèque Intelligente – Chatbot IA')
        self.geometry('1150x720')
        self.minsize(900, 600)
        self.configure(bg=BG)

        self._setup_styles()
        self._build()

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use('clam')

        s.configure('TNotebook',
                    background=BG, borderwidth=0, tabmargins=0)
        s.configure('TNotebook.Tab',
                    background=SIDEBAR, foreground=DIM,
                    padding=[22, 11], borderwidth=0,
                    font=('Segoe UI', 11))
        s.map('TNotebook.Tab',
              background=[('selected', ACCENT)],
              foreground=[('selected', 'white')])

        s.configure('Vertical.TScrollbar',
                    background=SIDEBAR, troughcolor=BG,
                    borderwidth=0, arrowcolor=DIM)

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=SIDEBAR, height=56)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)

        tk.Label(hdr,
                 text='📚  Bibliothèque Intelligente avec Chatbot IA',
                 bg=SIDEBAR, fg=TEXT,
                 font=('Segoe UI', 15, 'bold')).pack(side='left', padx=22, pady=14)

        tk.Label(hdr, text='ISET Tozeur  |  2025–2026',
                 bg=SIDEBAR, fg=DIM,
                 font=('Segoe UI', 9)).pack(side='right', padx=22)

        # ── Notebook ──
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=12, pady=10)

        self.livres_tab  = LivresTab(nb)
        self.chatbot_tab = ChatbotTab(nb)

        nb.add(self.livres_tab,  text='  📖  Gestion des Livres  ')
        nb.add(self.chatbot_tab, text='  🤖  Chatbot IA  ')


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    try:
        db.init_db()
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'Connexion MySQL échouée',
            f'Impossible de se connecter à la base de données.\n\n'
            f'{exc}\n\n'
            f'Vérifiez que XAMPP (MySQL) est démarré\n'
            f'et que les paramètres dans .env sont corrects.',
        )
        sys.exit(1)

    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
