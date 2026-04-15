import tkinter as tk
from tkinter import font as tkfont
import time

# MORSE LEGEND ---------------------------------------------------------
CHAR_TO_MORSE = {
    ## Letters
    'A': '.-',       'B': '-...',    'C': '-.-.',     'D': '-..',
    'E': '.',        'F': '..-.',    'G': '--.',      'H': '....',
    'I': '..',       'J': '.---',    'K': '-.-',      'L': '.-..',
    'M': '--',       'N': '-.',      'O': '---',      'P': '.--.',
    'Q': '--.-',     'R': '.-.',     'S': '...',      'T': '-',
    'U': '..-',      'V': '...-',    'W': '.--',      'X': '-..-',
    'Y': '-.--',     'Z': '--..',
    ## Numbers
    '0': '-----',    '1': '.----',   '2': '..---',    '3': '...--',
    '4': '....-',    '5': '.....',   '6': '-....',    '7': '--...',
    '8': '---..',    '9': '----.',
    ## Symbols
    '.': '.-.-.-',   ',': '--..--',  '?': '..--..',   "'": '.----.',
    '!': '-.-.--',   '/': '-..-.',   '(': '-.--.',    ')': '-.--.-',
    '&': '.-...',    ':': '---...',  ';': '-.-.-.',   '=': '-...-',
    '+': '.-.-.',    '-': '-....-',  '_': '..--.-',   '"': '.-..-.',
    '$': '...-..-',  '@': '.--.-.',  ' ': '/',
}
MORSE_TO_CHAR = {v: k for k, v in CHAR_TO_MORSE.items() if k != ' '}

# Palette --------------------------------------------------------------
BG        = '#0a0a0a'
PANEL     = '#111111'
CARD      = '#181818'
CARD2     = '#1d1d1d'
BORDER    = '#252525'
AMBER     = '#fbbf24'
AMBER_MID = '#fcd34d'
GREEN     = '#34d399'
BLUE      = '#7dd3fc'
RED       = '#f87171'
TEXT_PRI  = '#ffffff'
TEXT_SEC  = '#a8956e'
TEXT_MID  = '#d4b896'
BTN_BG    = '#1c1c1c'
BTN_HOV   = '#282828'
BTN_ACT   = '#323232'

KEY_W, KEY_H   = 54, 50
LONG_PRESS_MS  = 400

KB_ROWS = [
    list('1234567890'),
    list('QWERTYUIOP'),
    list('ASDFGHJKL'),
    list('ZXCVBNM'),
]


class MorseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('· — · MORSE TRANSLATOR — · ·')
        self.configure(bg=BG)
        self.resizable(True, False)
        self.minsize(700, 100)
        self._build_fonts()

        # encode state
        self.enc_tokens: list[tuple[str, str]] = []
        # decode state
        self.dec_current    = ''
        self.dec_symbols: list[str] = []
        self._press_start   = 0.0
        self._long_job      = None

        self._build_ui()
        self.update_idletasks()
        self.minsize(self.winfo_width(), self.winfo_height())

    # fonts ------------------------------------------------------------
    def _build_fonts(self):
        self.f_title   = tkfont.Font(family='Courier New', size=13, weight='bold')
        self.f_tab     = tkfont.Font(family='Courier New', size=11, weight='bold')
        self.f_display = tkfont.Font(family='Courier New', size=21, weight='bold')
        self.f_morse   = tkfont.Font(family='Courier New', size=12)
        self.f_key     = tkfont.Font(family='Courier New', size=12, weight='bold')
        self.f_msm     = tkfont.Font(family='Courier New', size=8)
        self.f_label   = tkfont.Font(family='Courier New', size=9)
        self.f_lg_h    = tkfont.Font(family='Courier New', size=10, weight='bold')
        self.f_big_sym = tkfont.Font(family='Courier New', size=40, weight='bold')
        self.f_hint    = tkfont.Font(family='Courier New', size=9)

    # MAIN LAYOUT ------------------------------------------------------
    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill='x', padx=18, pady=(14, 0))
        tk.Label(hdr, text='⬡  MORSE TRANSLATOR', bg=BG,
                    fg=AMBER, font=self.f_title).pack(side='left')
        tk.Label(hdr, text='· · · — — — · · ·', bg=BG,
                    fg=TEXT_SEC, font=self.f_label).pack(side='right')
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', padx=18, pady=(8, 0))

        # tab bar
        tab_bar = tk.Frame(self, bg=BG)
        tab_bar.pack(fill='x', padx=18, pady=(10, 0))
        self.btn_dec = self._tab_btn(tab_bar, 'MORSE  →  TEXT', 'decode')
        tk.Frame(tab_bar, bg=BG, width=6).pack(side='left')
        self.btn_enc = self._tab_btn(tab_bar, 'TEXT  →  MORSE', 'encode')

        # page container
        self.pages = tk.Frame(self, bg=BG)
        self.pages.pack(fill='both', expand=True)
        self.pages.columnconfigure(0, weight=1)
        self.pg_enc = tk.Frame(self.pages, bg=BG)
        self.pg_dec = tk.Frame(self.pages, bg=BG)
        self._build_encode_page(self.pg_enc)
        self._build_decode_page(self.pg_dec)
        self._switch_tab('decode')

    def _tab_btn(self, parent, label, tab_id):
        btn = tk.Button(parent, text=label, relief='flat', bd=0,
                        cursor='hand2', font=self.f_tab, padx=16, pady=7,
                        command=lambda: self._switch_tab(tab_id))
        btn.pack(side='left')
        return btn

    def _switch_tab(self, tab_id):
        if tab_id == 'encode':
            self.pg_dec.pack_forget()
            self.pg_enc.pack(fill='both', expand=True)
            self.btn_enc.config(bg=AMBER, fg=BG)
            self.btn_dec.config(bg=BTN_BG, fg=TEXT_MID)
        else:
            self.pg_enc.pack_forget()
            self.pg_dec.pack(fill='both', expand=True)
            self.btn_dec.config(bg=BLUE, fg=BG)
            self.btn_enc.config(bg=BTN_BG, fg=TEXT_MID)

    # DECODE PAGE  (Morse → Text) --------------------------------------
    def _build_decode_page(self, parent):
        outer = tk.Frame(parent, bg=BORDER)
        outer.pack(fill='x', padx=18, pady=(12, 0))
        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill='x', padx=1, pady=1)
        tr = tk.Frame(inner, bg=PANEL)
        tr.pack(fill='x')
        tk.Label(tr, text='  TEXT:', bg=PANEL, fg=TEXT_SEC,
                    font=self.f_label).pack(side='left', padx=(8, 4), pady=6)
        self.dec_tvar = tk.StringVar()
        tk.Label(tr, textvariable=self.dec_tvar, bg=PANEL, fg=BLUE,
                    font=self.f_display, anchor='w').pack(side='left', fill='x',
                    expand=True, pady=6)
        mr = tk.Frame(inner, bg=CARD)
        mr.pack(fill='x')
        tk.Label(mr, text='  INPUT:', bg=CARD, fg=TEXT_SEC,
                    font=self.f_label).pack(side='left', padx=(8, 4), pady=4)
        self.dec_mvar = tk.StringVar()
        tk.Label(mr, textvariable=self.dec_mvar, bg=CARD, fg=AMBER,
                    font=self.f_morse, anchor='w').pack(side='left', fill='x',
                    expand=True, pady=4)
        btn_wrap = tk.Frame(parent, bg=BG)
        btn_wrap.pack(fill='x', padx=18, pady=(18, 0))
        btn_outer = tk.Frame(btn_wrap, bg=BORDER)
        btn_outer.pack(fill='x')
        self._input_body = tk.Frame(btn_outer, bg=CARD2, cursor='hand2')
        self._input_body.pack(fill='x', padx=1, pady=1)
        self._input_sym_var = tk.StringVar(value='· —')
        self._input_sym_lbl = tk.Label(
            self._input_body, textvariable=self._input_sym_var,
            bg=CARD2, fg=AMBER, font=self.f_big_sym, height=2)
        self._input_sym_lbl.pack(fill='x', pady=(10, 4))
        instr = tk.Frame(self._input_body, bg=CARD2)
        instr.pack(pady=(0, 12))
        tk.Label(instr,
                    text='CLICK  →  dot  ·',
                    bg=CARD2, fg=TEXT_MID, font=self.f_hint).pack()
        tk.Label(instr,
                    text=f'HOLD  ({LONG_PRESS_MS} ms)  →  dash  —',
                    bg=CARD2, fg=TEXT_MID, font=self.f_hint).pack()
        for w in self._all_ch(self._input_body) + [self._input_body]:
            w.bind('<Enter>',           self._inp_enter)
            w.bind('<Leave>',           self._inp_leave)
            w.bind('<Button-1>',        self._inp_press)
            w.bind('<ButtonRelease-1>', self._inp_release)
        bld = tk.Frame(parent, bg=PANEL)
        bld.pack(fill='x', padx=18, pady=(12, 0))
        tk.Label(bld, text='  BUILDING:', bg=PANEL, fg=TEXT_SEC,
                    font=self.f_label).pack(side='left', padx=(8, 4), pady=5)
        self.dec_bvar = tk.StringVar(value='—')
        tk.Label(bld, textvariable=self.dec_bvar, bg=PANEL, fg=GREEN,
                    font=self.f_morse, anchor='w').pack(side='left', fill='x',
                    expand=True, pady=5)
        act = tk.Frame(parent, bg=BG)
        act.pack(fill='x', padx=18, pady=(10, 0))
        act_inner = tk.Frame(act, bg=BG)
        act_inner.pack(anchor='center')
        for label, cmd, color, w in [
            ('✓  CONFIRM LETTER', self._dec_confirm, GREEN, 18),
            ('⎵  WORD SPACE',     self._dec_space,   BLUE,  14),
            ('⌫  BACK',           self._dec_back,    AMBER,  8),
            ('↺  RESET',          self._dec_reset,   RED,    8),
        ]:
            self._spec_btn(act_inner, label, cmd, color, w)
            tk.Frame(act_inner, bg=BG, width=10).pack(side='left')
        tk.Frame(parent, bg=BORDER, height=1).pack(fill='x', padx=18, pady=(14, 0))
        self._legend(parent)

    # ENCODE PAGE  (Text → Morse) --------------------------------------
    def _build_encode_page(self, parent):
        outer = tk.Frame(parent, bg=BORDER)
        outer.pack(fill='x', padx=18, pady=(12, 0))
        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill='x', padx=1, pady=1)
        self.enc_canvas = tk.Canvas(inner, bg=PANEL, height=88, highlightthickness=0)
        self.enc_canvas.pack(fill='x', expand=True)
        self.enc_tf = tk.Frame(self.enc_canvas, bg=PANEL)
        self.enc_canvas.create_window((0, 0), window=self.enc_tf, anchor='nw')
        self.enc_tf.bind('<Configure>',
            lambda e: self.enc_canvas.configure(scrollregion=self.enc_canvas.bbox('all')))
        mr = tk.Frame(inner, bg=CARD)
        mr.pack(fill='x')
        tk.Label(mr, text='  MORSE:', bg=CARD, fg=TEXT_SEC,
                    font=self.f_label).pack(side='left', padx=(8, 4), pady=4)
        self.enc_mvar = tk.StringVar()
        tk.Label(mr, textvariable=self.enc_mvar, bg=CARD, fg=AMBER,
                    font=self.f_morse, anchor='w').pack(side='left', fill='x',
                    expand=True, pady=4)
        kb_wrap = tk.Frame(parent, bg=BG)
        kb_wrap.pack(fill='x', padx=18, pady=(12, 0))
        for row_chars in KB_ROWS:
            rf = tk.Frame(kb_wrap, bg=BG)
            rf.pack(anchor='center', pady=3)
            for ch in row_chars:
                self._enc_key(rf, ch)
        spec = tk.Frame(kb_wrap, bg=BG)
        spec.pack(anchor='center', pady=3)
        self._spec_btn(spec, '⎵  SPACE', lambda: self._enc_type(' '), GREEN, 12)
        tk.Frame(spec, bg=BG, width=14).pack(side='left')
        self._spec_btn(spec, '⌫  BACK',  self._enc_back,  AMBER, 10)
        tk.Frame(spec, bg=BG, width=14).pack(side='left')
        self._spec_btn(spec, '↺  RESET', self._enc_reset, RED,   10)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill='x', padx=18, pady=(12, 0))
        self._legend(parent)

    def _enc_key(self, parent, ch):
        mc = CHAR_TO_MORSE.get(ch, '')
        f = tk.Frame(parent, bg=BTN_BG, width=KEY_W, height=KEY_H)
        f.pack_propagate(False)
        f.pack(side='left', padx=2)
        l = tk.Label(f, text=ch, bg=BTN_BG, fg=TEXT_PRI, font=self.f_key)
        l.place(relx=.5, rely=.34, anchor='center')
        m = tk.Label(f, text=mc, bg=BTN_BG, fg=AMBER_MID, font=self.f_msm)
        m.place(relx=.5, rely=.74, anchor='center')

        def hover(on, _f=f, _l=l, _m=m):
            bg = BTN_HOV if on else BTN_BG
            _f.config(bg=bg); _l.config(bg=bg)
            _m.config(bg=bg, fg=AMBER if on else AMBER_MID)

        for w in (f, l, m):
            w.bind('<Enter>',    lambda e: hover(True))
            w.bind('<Leave>',    lambda e: hover(False))
            w.bind('<Button-1>', lambda e, c=ch: (self._enc_type(c), hover(False)))

    def _spec_btn(self, parent, label, cmd, color, width):
        btn = tk.Button(parent, text=label, command=cmd, bg=BTN_BG, fg=color,
                        activebackground=BTN_ACT, activeforeground=color,
                        relief='flat', cursor='hand2', font=self.f_key,
                        padx=12, pady=8, width=width, bd=0, highlightthickness=0)
        btn.pack(side='left')
        btn.bind('<Enter>', lambda e: btn.config(bg=BTN_HOV))
        btn.bind('<Leave>', lambda e: btn.config(bg=BTN_BG))

    # Encode logic -----------------------------------------------------
    def _enc_type(self, ch):
        ch_up = ch.upper()
        self.enc_tokens.append((ch_up, CHAR_TO_MORSE.get(ch_up, '')))
        self._enc_rebuild()
    def _enc_back(self):
        if self.enc_tokens:
            self.enc_tokens.pop()
            self._enc_rebuild()
    def _enc_reset(self):
        self.enc_tokens.clear()
        self._enc_rebuild()
    def _enc_rebuild(self):
        for w in self.enc_tf.winfo_children():
            w.destroy()
        for ch, mc in self.enc_tokens:
            cell = tk.Frame(self.enc_tf, bg=CARD)
            cell.pack(side='left', padx=3, pady=5)
            if ch == ' ':
                tk.Label(cell, text='·', bg=CARD, fg=TEXT_SEC,
                            font=self.f_display, width=2).pack()
                tk.Label(cell, text='/', bg=CARD, fg=AMBER_MID,
                            font=self.f_msm).pack()
            else:
                tk.Label(cell, text=ch, bg=CARD, fg=TEXT_PRI,
                            font=self.f_display, width=2).pack()
                tk.Label(cell, text=mc, bg=CARD, fg=AMBER,
                            font=self.f_msm).pack()
        self.enc_tf.update_idletasks()
        self.enc_canvas.xview_moveto(1.0)
        self.enc_mvar.set('  '.join(mc for _, mc in self.enc_tokens))

    def _inp_enter(self, e):
        self._input_body.config(bg=BTN_HOV)
        self._input_sym_lbl.config(bg=BTN_HOV)
        for c in self._all_ch(self._input_body):
            try: c.config(bg=BTN_HOV)
            except: pass
    def _inp_leave(self, e):
        self._input_body.config(bg=CARD2)
        self._input_sym_lbl.config(bg=CARD2)
        for c in self._all_ch(self._input_body):
            try: c.config(bg=CARD2)
            except: pass
    def _inp_press(self, e):
        self._press_start = time.time()
        self._long_job = self.after(
            LONG_PRESS_MS,
            lambda: self._input_sym_lbl.config(fg=RED))
    def _inp_release(self, e):
        held_ms = (time.time() - self._press_start) * 1000
        if self._long_job:
            self.after_cancel(self._long_job)
            self._long_job = None
        self._input_sym_lbl.config(fg=AMBER)
        if held_ms >= LONG_PRESS_MS:
            self._dec_add('-')
        else:
            self._dec_add('.')

    # Decode logic -----------------------------------------------------
    def _dec_add(self, sym):
        self.dec_current += sym
        self.dec_bvar.set(self.dec_current or '—')
        self._dec_refresh()
    def _dec_confirm(self):
        if not self.dec_current:
            return
        self.dec_symbols.append(self.dec_current)
        self.dec_current = ''
        self.dec_bvar.set('—')
        self._dec_refresh()
    def _dec_space(self):
        if self.dec_current:
            self._dec_confirm()
        self.dec_symbols.append('/')
        self._dec_refresh()
    def _dec_back(self):
        if self.dec_current:
            self.dec_current = self.dec_current[:-1]
            self.dec_bvar.set(self.dec_current or '—')
        elif self.dec_symbols:
            self.dec_symbols.pop()
        self._dec_refresh()
    def _dec_reset(self):
        self.dec_current = ''
        self.dec_symbols.clear()
        self.dec_bvar.set('—')
        self._dec_refresh()
    def _dec_refresh(self):
        parts = list(self.dec_symbols)
        if self.dec_current:
            parts.append(f'[{self.dec_current}]')
        self.dec_mvar.set('  '.join(parts))
        text = ''
        for s in self.dec_symbols:
            text += ' ' if s == '/' else MORSE_TO_CHAR.get(s, '?')
        self.dec_tvar.set(text)

    # SHARED LEGEND ----------------------------------------------------
    def _legend(self, parent):
        leg = tk.Frame(parent, bg=PANEL)
        leg.pack(fill='x', padx=18, pady=(10, 18))
        tk.Label(leg, text='  MORSE CODE LEGEND', bg=PANEL, fg=AMBER,
                    font=self.f_lg_h, anchor='w').pack(fill='x', pady=(8, 3))
        tk.Frame(leg, bg=BORDER, height=1).pack(fill='x', padx=8)

        grid = tk.Frame(leg, bg=PANEL)
        grid.pack(fill='x', padx=8, pady=(5, 8))
        f_ch = tkfont.Font(family='Courier New', size=9, weight='bold')
        f_mc = tkfont.Font(family='Courier New', size=8)
        items = [(k, v) for k, v in CHAR_TO_MORSE.items() if k != ' ']
        cols = 9
        for idx, (ch, mc) in enumerate(items):
            r, c = divmod(idx, cols)
            cell = tk.Frame(grid, bg=CARD)
            cell.grid(row=r, column=c, padx=2, pady=2, sticky='nsew')
            tk.Label(cell, text=ch, bg=CARD, fg=TEXT_PRI, font=f_ch,
                        width=2).pack(side='left', padx=(3, 0))
            tk.Label(cell, text=mc, bg=CARD, fg=AMBER, font=f_mc,
                        anchor='w', width=8).pack(side='left', padx=(2, 3))
        for c in range(cols):
            grid.columnconfigure(c, weight=1)

    def _all_ch(self, widget):
        kids = list(widget.winfo_children())
        for k in widget.winfo_children():
            kids += self._all_ch(k)
        return kids

if __name__ == '__main__':
    MorseApp().mainloop()