import random
import csv
import os
import math
from pathlib import Path
from datetime import datetime
from psychopy import core, data, event, gui, sound, visual
from psychopy.hardware import keyboard
from psychopy.visual import Rect, TextStim

# =========================
# RUTAS BASE
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BART_DIR   = os.path.join(BASE_DIR, "bart_task-main")
SYMBOL_DIR = os.path.join(BASE_DIR, "symbol")
SOUND_DIR  = BART_DIR
INSTR_DIR  = BART_DIR

DATA_DIR = Path(os.path.join(BASE_DIR, "datos"))
DATA_DIR.mkdir(exist_ok=True)

PARTICIPANTS_CSV = DATA_DIR / "participants.csv"
PS_TRIALS_CSV    = DATA_DIR / "processing_speed_trials.csv"
PANAS_ITEMS_CSV  = DATA_DIR / "panas_items.csv"
BART_EVENTS_CSV  = DATA_DIR / "bart_events.csv"

# =========================
# CONFIGURACIÓN GENERAL
# =========================
FULLSCREEN   = True
WIN_SIZE     = [1280, 720]
BG_COLOR   = [0.91, 0.89, 0.82]      # crema claro
TEXT_COLOR = [-0.87, -0.87, -0.87]   # casi negro
 
BTN_FILL       = [-0.35, 0.05, 0.55]  
BTN_FILL_HOVER = [-0.20, 0.18, 0.72]  
BTN_FILL_LOCK  = [0.05, 0.15, 0.28] 
BTN_TEXT_COLOR = [0.95, 0.97, 0.98]  

BOX_FILL       = [0.82, 0.77, 0.65]
BOX_LINE       = [-0.45, -0.45, -0.45]


PANAS_ROW_EVEN = [0.78, 0.75, 0.67]
PANAS_ROW_ODD  = [0.74, 0.71, 0.63]
PANAS_ROW_SEL  = [0.58, 0.66, 0.78]
PANAS_HDR_BG   = [0.68, 0.64, 0.55]
PANAS_DOT_EMPTY = [-0.40, -0.40, -0.40]
PANAS_DOT_FILL  = [-0.35, 0.05, 0.55] 

FONT_TITLE  = 52 
FONT_INSTR  = 36   
FONT_ITEM   = 28   
FONT_FOOT   = 24   
FONT_BTN    = 30  
FONT_NUM    = 34

# =========================
# CONFIGURACIÓN DIGIT SYMBOL
# =========================
DS_SYMBOL_IDS      = list(range(1, 10))   # 1.png ... 9.png
DS_SYMBOL_ORDER    = [1, 2, 3, 4, 5, 6, 7, 8, 9]   # clave fija izquierda -> derecha
IMG_PATH_DS        = {sid: os.path.join(SYMBOL_DIR, f"{sid}.png") for sid in DS_SYMBOL_IDS}
MAPPING_ID_DS      = "DS9_" + "-".join(str(s) for s in DS_SYMBOL_ORDER)

DS_TEST_DURATION_S = 120.0
DS_PRACTICE_TRIALS = 7
DS_QUEUE_LEN       = 7   # 7 símbolos visibles en la fila central

for sid in DS_SYMBOL_ORDER:
    if not os.path.exists(IMG_PATH_DS[sid]):
        print(f"ADVERTENCIA: No se encuentra {IMG_PATH_DS[sid]}")

# =========================
# CONFIGURACIÓN PANAS
# =========================
PANAS_ROW_H       = 62
PANAS_HEADER_H    = 56
PANAS_CROSS_COLOR = "white"

# ORDEN EXACTO DE PRESENTACIÓN SEGÚN TU CUESTIONARIO
PANAS_SPEC = [
    ("Interesado/a por las cosas",   "PA05"),
    ("Angustiado/a",                 "NA03"),
    ("Ilusionado/a o emocionado/a",  "PA02"),
    ("Afectado/a",                   "NA05"),
    ("Fuerte",                       "PA03"),
    ("Culpable",                     "NA06"),
    ("Asustado/a",                   "NA01"),
    ("Agresivo/a",                   "NA08"),
    ("Entusiasmado/a",               "PA04"),
    ("Satisfecho/a consigo mismo/a", "PA09"),
    ("Irritable",                    "NA10"),
    ("Despierto/a",                  "PA08"),
    ("Avergonzado/a",                "NA04"),
    ("Inspirado/a",                  "PA07"),
    ("Nervioso/a",                   "NA07"),
    ("Decidido/a",                   "PA01"),
    ("Concentrado/a",                "PA06"),
    ("Agitado/a",                    "NA09"),
    ("Activo/a",                     "PA10"),
    ("Miedoso/a",                    "NA02"),
]

PANAS_ITEMS     = [txt for txt, _ in PANAS_SPEC]
PANAS_ITEM_IDS  = [iid for _, iid in PANAS_SPEC]
PANAS_TEXT_TO_ID = dict(PANAS_SPEC)

# Si después querés calcular puntajes por valencia, conservá estos grupos aparte
PANAS_POS_IDS = [f"PA{i:02d}" for i in range(1, 11)]
PANAS_NEG_IDS = [f"NA{i:02d}" for i in range(1, 11)]

COL_TITLES = ["Nada o muy ligeramente", "Un poco", "Moderadamente", "Bastante", "Mucho"]

INSTRUCCIONES_ESCALA = (
    "Apretá la opción que refleje mejor cómo te sentís en este momento.\n"
    "Cuando completes la tabla, apretá SIGUIENTE para avanzar.\n"
)

# =========================
# CONFIGURACIÓN BART
# =========================
POP_TEXTURE_SIZE  = (200, 155)
BALL_TEXTURE_SIZE = (596, 720)
INITIAL_BALL_SIZE = (int(BALL_TEXTURE_SIZE[0]*0.2), int(BALL_TEXTURE_SIZE[1]*0.2))

COLOR_LIST  = ['blue']
MAX_PUMPS   = [128]
REPETITIONS = 30
REWARD      = 0.05

KEY_PUMP = 'space'
KEY_NEXT = 'return'
KEY_QUIT = 'escape'
KEY_SKIP = 's'

ABSENT_MESSAGE = '¡Tardaste demasiado! Se desinfló el globo. Perdiste lo que habías ganado.'
FINAL_MESSAGE  = '¡Muy bien! \n Ganaste un total de {:.2f} $.\nGracias por participar.'

COMMON_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")

def find_asset(base_dir, stem_or_filename):
    """
    Busca un archivo por nombre exacto o por stem + extensiones comunes.
    Devuelve la ruta completa si existe; si no, None.
    """
    if not stem_or_filename:
        return None
    candidate = os.path.join(base_dir, stem_or_filename)
    if os.path.exists(candidate):
        return candidate
    root, ext = os.path.splitext(stem_or_filename)
    stems = [stem_or_filename] if ext else [stem_or_filename]
    if ext:
        extra = []
    else:
        extra = [stem_or_filename + e for e in COMMON_IMAGE_EXTS]
    for name in stems + extra:
        candidate = os.path.join(base_dir, name)
        if os.path.exists(candidate):
            return candidate
    return None

def fit_image_to_width(img_path, target_w):
    try:
        from PIL import Image
        with Image.open(img_path) as im:
            w, h = im.size
        if w <= 0 or h <= 0:
            return (target_w, target_w)
        target_h = int(target_w * (h / w))
        return (target_w, target_h)
    except Exception:
        return (target_w, int(target_w * 0.4))

def load_optional_sound(path):
    try:
        if path and os.path.exists(path):
            return sound.Sound(path)
    except Exception:
        pass
    return None

def safe_sound_play(sound_obj):
    if sound_obj is None:
        return
    try:
        sound_obj.stop()
    except Exception:
        pass
    try:
        sound_obj.play()
    except Exception:
        pass

# =========================
# GUARDADO DE DATOS
# =========================
def _ensure_headers():
    if not PARTICIPANTS_CSV.exists():
        with PARTICIPANTS_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["participant_id","group","session_id","date_time_start","date_time_end","experiment_version","bart_money","rifas","panas_pos_sum","panas_neg_sum"])
    if not PS_TRIALS_CSV.exists():
        with PS_TRIALS_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["participant_id","session_id","task","trial_index","stimulus","correct_answer","response","rt_ms","timestamp","stim_onset_time","resp_time","foreperiod_ms","digit","mapping_id"])
    if not PANAS_ITEMS_CSV.exists():
        with PANAS_ITEMS_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["participant_id","session_id","phase","item_id","response"])
    if not BART_EVENTS_CSV.exists():
        with BART_EVENTS_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["participant_id","session_id","phase","balloon_index","event_type","event_index","timestamp","rt_ms","pump_number"])

_ensure_headers()

def save_participant_row(participant_id, group, session_id, date_time_start, date_time_end, experiment_version, bart_money="", rifas="", panas_pos_sum="", panas_neg_sum=""):
    with PARTICIPANTS_CSV.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([participant_id, group, session_id, date_time_start, date_time_end, experiment_version, bart_money, rifas, panas_pos_sum, panas_neg_sum])
        

def save_processing_trial_row(participant_id,session_id,task,trial_index,stimulus,correct_answer,response,rt_ms,stim_onset_time,resp_time,foreperiod_ms="",digit="",mapping_id=""):
    with PS_TRIALS_CSV.open("a",newline="",encoding="utf-8") as f:
        csv.writer(f).writerow([participant_id,session_id,task,trial_index,stimulus,correct_answer,response,
            "" if rt_ms in ["",None] else round(float(rt_ms),2),
            datetime.now().isoformat(timespec="seconds"),
            "" if stim_onset_time in ["",None] else round(float(stim_onset_time),4),
            "" if resp_time in ["",None] else round(float(resp_time),4),
            "" if foreperiod_ms in ["",None] else int(round(float(foreperiod_ms))),
            digit, mapping_id])

def save_panas_items(participant_id,session_id,phase,panas_dict):
    phase = phase.lower()
    with PANAS_ITEMS_CSV.open("a",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        for item_text in PANAS_ITEMS:
            item_id = PANAS_TEXT_TO_ID[item_text]
            key = f"{phase.upper()}_{item_id}"
            rating  = panas_dict.get(key,"")
            w.writerow([participant_id,session_id,phase,item_id,rating])

def save_bart_event(participant_id,session_id,phase,balloon_index,event_type,event_index,rt_ms,pump_number):
    with BART_EVENTS_CSV.open("a",newline="",encoding="utf-8") as f:
        csv.writer(f).writerow([participant_id,session_id,phase.lower(),balloon_index,event_type,event_index,
            datetime.now().isoformat(timespec="seconds"),
            "" if rt_ms in ["",None] else round(float(rt_ms),2),
            pump_number])

# =========================
# PARTICIPANTE
# =========================
exp_info = {"Participante": "", "Grupo": ""}
dlg = gui.DlgFromDict(exp_info, title="Piloto PANAS + BART")
if not dlg.OK:
    core.quit()

start_dt               = datetime.now()
exp_info["start_time"] = start_dt.isoformat(timespec="seconds")
exp_info["fecha_hora"] = start_dt.strftime("%Y-%m-%d_%Hh%Mm%Ss")

PARTICIPANT_ID      = exp_info["Participante"]
SESSION_ID          = exp_info["fecha_hora"]
EXPERIMENT_VERSION  = "3.8"

exp_name = "piloto_panas_bart_listado"
data_dir_str = str(DATA_DIR)


bart_info = {"id": exp_info["Participante"], "start_time": exp_info["start_time"], "end_time": "", "version": 0.1}

# =========================
# VENTANA / ESTÍMULOS GENERALES
# =========================
win = visual.Window(size=WIN_SIZE,fullscr=FULLSCREEN,color=BG_COLOR, colorSpace='rgb', units="pix",allowGUI=False,waitBlanking=True,useFBO=True)
win.setMouseVisible(True)

kb = keyboard.Keyboard()
kb.clearEvents()
try: kb.clock.reset()
except Exception: pass

mouse = event.Mouse(win=win)

default_text = TextStim(win,text="",color=TEXT_COLOR,height=FONT_ITEM,wrapWidth=1100,pos=(0,40))
cont_text    = TextStim(win,text="",color=TEXT_COLOR,height=FONT_FOOT,wrapWidth=1000,pos=(0,-280))
title_text   = TextStim(win,text="",color=TEXT_COLOR,height=FONT_TITLE,wrapWidth=1000,bold=True,pos=(0,200))
instr_text   = TextStim(win,text="",color=TEXT_COLOR,height=FONT_INSTR,wrapWidth=1100,pos=(0,360))
footer_text  = TextStim(win,text="",color=TEXT_COLOR,height=FONT_FOOT,wrapWidth=1100,pos=(0,-380))
help_text    = TextStim(win,text="",color=TEXT_COLOR,height=FONT_FOOT,wrapWidth=1100,pos=(0,-410))
item_text    = TextStim(win,text="",color=TEXT_COLOR,height=FONT_ITEM,wrapWidth=900,alignText="left",anchorHoriz="left")

select_rect = Rect(win,width=1000,height=40,lineColor=None,fillColor=[0.18,0.18,0.18],pos=(0,0))
line_sep    = Rect(win,width=1000,height=2,lineColor=[1,1,1],fillColor=[1,1,1],pos=(0,0))

# =========================
# ESTÍMULOS BART
# =========================
stim = visual.ImageStim(win,pos=(0,0),size=INITIAL_BALL_SIZE,units='pix',interpolate=True)
bart_text = visual.TextStim(
    win,
    color=TEXT_COLOR,
    height=0.10,
    pos=(0.4, -0.9),
    alignText='right',
    units='norm',
    anchorHoriz='center',
    anchorVert='bottom'
)

remind_return = visual.TextStim(
    win,
    color=TEXT_COLOR,
    height=0.08,
    pos=(-0.23, -0.9),
    alignText='center',
    units='norm',
    anchorHoriz='center',
    anchorVert='bottom'
)

remind_enter = visual.TextStim(
    win,
    color=TEXT_COLOR,
    height=0.08,
    pos=(0.23, -0.9),
    alignText='center',
    units='norm',
    anchorHoriz='center',
    anchorVert='bottom'
)
slot_machine = load_optional_sound(os.path.join(SOUND_DIR, "slot_machine.ogg"))
pop_sound    = load_optional_sound(os.path.join(SOUND_DIR, "pop.ogg"))
INSTRUCCIONES_BART_IMG = (
    find_asset(BART_DIR, "instrucciones_bart")
    or find_asset(BART_DIR, "instrucciones_bart.png")
    or find_asset(BASE_DIR, "instrucciones_bart")
    or find_asset(BASE_DIR, "instrucciones_bart.png")
)
core.wait(0.5)

# =========================
# UTILIDADES GENERALES
# =========================
def wipe(n_flips=2):
    for _ in range(n_flips): win.flip()

def get_last_key(allowed=None):
    keys = kb.getKeys(waitRelease=False,clear=True)
    if not keys: return None
    if 's' in [k.name for k in keys]: return 's'
    if allowed:
        for k in reversed(keys):
            if k.name in allowed: return k.name
        return None
    return keys[-1].name

def cerrar():
    win.close()
    core.quit()
    
def draw_button(rect,label): rect.draw(); label.draw()

def point_in_rect(mx,my,rect_obj):
    cx,cy = rect_obj.pos
    return (abs(mx-cx) <= rect_obj.width/2.0) and (abs(my-cy) <= rect_obj.height/2.0)

def mostrar_mensaje(titulo="",cuerpo=None,mostrar_continuar=True):
    if cuerpo is None: cuerpo,titulo = titulo,""
    wipe(1)
    title_text.text   = titulo
    default_text.text = cuerpo
    cont_text.text    = "Presioná ENTER o ESPACIO para continuar" if mostrar_continuar else ""
    kb.clearEvents(); event.clearEvents()
    if titulo: title_text.draw()
    default_text.draw(); cont_text.draw(); win.flip()
    if mostrar_continuar:
        while True:
            k = get_last_key(["return","enter","space","escape","s"])
            if k == "escape": cerrar()
            if k in ["s","return","enter","space"]: break
            core.wait(0.01)
    wipe(2)

def make_rounded_vertices(width,height,radius=0.05,segments=16):
    max_r  = min(width,height)/2.0
    radius = min(radius,max_r)
    w_inner,h_inner = (width/2.0)-radius,(height/2.0)-radius
    vertices = []
    corners      = [(w_inner,h_inner),(-w_inner,h_inner),(-w_inner,-h_inner),(w_inner,-h_inner)]
    start_angles = [0,math.pi/2,math.pi,3*math.pi/2]
    for i,(cx,cy) in enumerate(corners):
        ba = start_angles[i]
        for j in range(segments+1):
            theta = ba+(math.pi/2)*(j/segments)
            vertices.append((cx+radius*math.cos(theta),cy+radius*math.sin(theta)))
    return vertices

BTN_W = 380
BTN_H = 72

def mostrar_instruccion_con_boton(
    win, mouse, cuerpo, boton_texto="SIGUIENTE >", font_height=None,
    btn_width=None, btn_height=None, btn_text_height=34,
    align_text="center", texto_pos=(0, 60),
    imagen_abajo=None, imagen_abajo_size=None, imagen_abajo_pos=(0, -165),
    btn_pos=(0, -310)
):
    wipe(1)
    fh = font_height if font_height is not None else FONT_INSTR
    bw = btn_width if btn_width is not None else BTN_W
    bh = btn_height if btn_height is not None else BTN_H

    t_cuerpo = visual.TextStim(
    win,
    text=cuerpo,
    color=TEXT_COLOR,
    height=fh,
    wrapWidth=1220,
    pos=texto_pos,
    alignText=align_text
    )
    try:
        t_cuerpo.lineSpacing = 1.6
    except AttributeError:
        pass
    

    img_stim = None
    if imagen_abajo:
        try:
            img_stim = visual.ImageStim(
                win,
                image=imagen_abajo,
                pos=imagen_abajo_pos,
                size=imagen_abajo_size if imagen_abajo_size is not None else (520, 200),
                units="pix",
                interpolate=True
            )
        except Exception:
            img_stim = None

    btn_box = visual.Rect(
        win, width=bw, height=bh, pos=btn_pos,
        fillColor=BTN_FILL, lineColor=BTN_FILL, lineWidth=3
    )
    btn_txt = visual.TextStim(
        win, text=boton_texto, color=BTN_TEXT_COLOR,
        height=btn_text_height, pos=btn_pos, bold=True
    )

    event.clearEvents()
    mouse.clickReset()
    core.wait(0.2)
    CHARS_PER_SEC = 45.0
    LOCK_SECS = max(0.8, len(cuerpo) / CHARS_PER_SEC)
    lock_clock = core.Clock()
    while True:
        elapsed = lock_clock.getTime()
        locked  = elapsed < LOCK_SECS
        t_cuerpo.draw()
        if img_stim is not None:
            img_stim.draw()
        if locked:
            btn_box.fillColor = BTN_FILL_LOCK
            btn_box.lineColor = BTN_FILL_LOCK
            btn_txt.color     = BTN_TEXT_COLOR
        else:
            btn_box.fillColor = BTN_FILL_HOVER if btn_box.contains(mouse) else BTN_FILL
            btn_box.lineColor = BTN_FILL
            btn_txt.color     = BTN_TEXT_COLOR
        btn_box.draw()
        btn_txt.draw()
        win.flip()
        if not locked and mouse.getPressed()[0] and btn_box.contains(mouse):
            btn_box.fillColor = BTN_FILL_HOVER
            btn_box.lineColor = BTN_FILL
            btn_txt.color     = BTN_TEXT_COLOR
            btn_box.draw()
            btn_txt.draw()
            win.flip()
            while mouse.getPressed()[0]:
                pass
            break
        keys = kb.getKeys(["escape", "s"], clear=True)
        if keys:
            if "escape" in [k.name for k in keys]:
                cerrar()
            if "s" in [k.name for k in keys]:
                break
    wipe(2)
    
def calcular_rifas(monto):
    try: m = float(monto)
    except Exception: m = 0.0
    if m < 10:  return 1
    elif m < 20: return 2
    elif m < 35: return 3
    elif m < 50: return 4
    elif m < 60: return 5
    else:        return 6

# =========================
# TAREAS PROCESSING SPEED
# =========================
FP_VALUES_MS = [1000,1200,1400,1600,1800]

def make_fp_sequence(n_trials, fp_values_ms=FP_VALUES_MS, rng=random):
    k = len(fp_values_ms); base = n_trials // k; rem = n_trials % k
    seq_ms = fp_values_ms * base
    if rem > 0: seq_ms += rng.sample(fp_values_ms, rem)
    for _ in range(200):
        rng.shuffle(seq_ms)
        if all(seq_ms[i] != seq_ms[i+1] for i in range(len(seq_ms)-1)):
            break
    return [ms / 1000.0 for ms in seq_ms]

def _clear_all_kb(kb_local):
    kb_local.clearEvents(); event.clearEvents()

def run_srt(win, participant_id, n_practice=8, n_test=20, max_rt=1.5, iti=0.2):
    stim_fix    = TextStim(win, text="+", color=TEXT_COLOR, height=FONT_TITLE, pos=(0,0))
    stim_target = visual.Circle(win, radius=40, fillColor=TEXT_COLOR, lineColor=TEXT_COLOR, units="pix")
    kb_local    = keyboard.Keyboard()

    mostrar_instruccion_con_boton(win, mouse,
        "En esta tarea la consigna es simple:\n\n"
        "Cada vez que aparezca un círculo en pantalla,\n"
        "apretá la barra ESPACIADORA lo más rápido que puedas.\n\n"
        "Cuando estés listo, apretá SIGUIENTE.")

    fp_practice = make_fp_sequence(n_practice)
    fp_test     = make_fp_sequence(n_test)

    mostrar_instruccion_con_boton(win, mouse,
        "Primero vas a hacer 8 rondas de práctica.\n\n"
        "Acordate de responder lo más rápido que puedas.\n\n"
        "Cuando estés listo, apretá SIGUIENTE para comenzar.")

    win.setMouseVisible(False)
    try:
        for t in range(1, n_practice+1):
            fix_dur = fp_practice[t-1]
            fix_clock = core.Clock()
            _clear_all_kb(kb_local)

            while fix_clock.getTime() < fix_dur:
                stim_fix.draw()
                win.flip()
                keys = kb_local.getKeys(["escape","s"], waitRelease=False, clear=True)
                if keys:
                    for k in keys:
                        if k.name == "escape":
                            cerrar()
                        if k.name == "s":
                            return {"SRT_mean_rt":"","SRT_acc":""}

            _clear_all_kb(kb_local)
            stim_target.draw()
            stim_onset_time = win.flip()

            resp_time = ""
            rt_ms = ""
            response_key = ""
            rt_clock = core.Clock()
            rt_clock.reset()

            while rt_clock.getTime() < max_rt:
                keys = kb_local.getKeys(["escape","space","s"], clear=True)
                if keys:
                    k = keys[0].name
                    if k == "escape":
                        cerrar()
                    if k == "s":
                        return {"SRT_mean_rt":"","SRT_acc":""}
                    if k == "space":
                        response_key = "space"
                        resp_time = core.getTime()
                        rt_ms = (resp_time - stim_onset_time) * 1000.0
                        win.flip()
                        break

                stim_target.draw()
                win.flip()

            core.wait(iti)
            save_processing_trial_row(
                participant_id=participant_id,
                session_id=SESSION_ID,
                task="SRT_PRACTICE",
                trial_index=t,
                stimulus="circle",
                correct_answer="space",
                response=response_key,
                rt_ms=rt_ms,
                stim_onset_time=stim_onset_time,
                resp_time=resp_time,
                digit="",
                mapping_id=""
            )
        win.setMouseVisible(True)
        mostrar_instruccion_con_boton(win, mouse,
            "Ahora un círculo va a aparecer 20 veces. De la misma forma que en la práctica, "
            "apretá la barra ESPACIADORA lo más rápido que puedas.\n\nApretá SIGUIENTE para comenzar.")

        win.setMouseVisible(False)

        rts_test_sec = []
        for t in range(1, n_test+1):
            fix_dur = fp_test[t-1]
            fix_clock = core.Clock()
            _clear_all_kb(kb_local)

            while fix_clock.getTime() < fix_dur:
                stim_fix.draw()
                win.flip()
                keys = kb_local.getKeys(["escape","s"], waitRelease=False, clear=True)
                if keys:
                    for k in keys:
                        if k.name == "escape":
                            cerrar()
                        if k.name == "s":
                            return {"SRT_mean_rt":"","SRT_acc":""}

            _clear_all_kb(kb_local)
            stim_target.draw()
            stim_onset_time = win.flip()

            resp_time = ""
            rt_ms = ""
            response_key = ""
            rt_clock = core.Clock()
            rt_clock.reset()

            while rt_clock.getTime() < max_rt:
                keys = kb_local.getKeys(["escape","space","s"], clear=True)
                if keys:
                    k = keys[0].name
                    if k == "escape":
                        cerrar()
                    if k == "s":
                        return {"SRT_mean_rt":"","SRT_acc":""}
                    if k == "space":
                        response_key = "space"
                        resp_time = core.getTime()
                        rt_ms = (resp_time - stim_onset_time) * 1000.0
                        rts_test_sec.append(rt_ms / 1000.0)
                        win.flip()
                        break

                stim_target.draw()
                win.flip()

            core.wait(iti)
            save_processing_trial_row(
                participant_id=participant_id,
                session_id=SESSION_ID,
                task="SRT_TEST",
                trial_index=t,
                stimulus="circle",
                correct_answer="space",
                response=response_key,
                rt_ms=rt_ms,
                stim_onset_time=stim_onset_time,
                resp_time=resp_time,
                digit="",
                mapping_id=""
            )

        mean_rt = (sum(rts_test_sec) / len(rts_test_sec)) if rts_test_sec else ""
        acc     = (len(rts_test_sec) / n_test) if n_test > 0 else ""
        return {"SRT_mean_rt": mean_rt, "SRT_acc": acc}

    finally:
        win.setMouseVisible(True)

def run_crt(win, participant_id, n_practice=8, n_test=40, max_rt=1.8, iti=0.2):
    stim_fix   = TextStim(win, text="+",  color=TEXT_COLOR, height=FONT_TITLE, pos=(0,0))
    left_stim  = TextStim(win, text="<-", color=TEXT_COLOR, height=FONT_TITLE, pos=(0,0))
    right_stim = TextStim(win, text="->", color=TEXT_COLOR, height=FONT_TITLE, pos=(0,0))
    kb_local   = keyboard.Keyboard()

    mostrar_instruccion_con_boton(win, mouse,
        "La siguiente tarea es similar a la anterior, pero con una diferencia:\n\n"
        "ahora vas a tener que decidir qué tecla apretar según lo que aparezca en pantalla.\n\n"
        "Apretá SIGUIENTE para ver cómo funciona.",
        font_height=42)

    mostrar_instruccion_con_boton(win, mouse,
        "Van a aparecer flechas en pantalla.\n\n"
        "Si ves (<-), apretá la flecha <- (izquierda) del teclado.\n"
        "Si ves (->), apretá la flecha -> (derecha) del teclado.\n\n"
        "Respondé lo más rápido que puedas.\n\n"
        "Cuando estés listo, apretá SIGUIENTE.",
        font_height=42)

    fp_practice = make_fp_sequence(n_practice)
    fp_test = make_fp_sequence(n_test)
    mostrar_instruccion_con_boton(win, mouse,
        "Apoyá el dedo índice en la flecha que apunta a tu izquierda (<-) "
        "y el dedo medio en la flecha que apunta a tu derecha (->).\n\n"
        "Como antes, vas a empezar con 8 rondas de práctica.\n\nApretá SIGUIENTE para comenzar.",
        font_height=42)

    win.setMouseVisible(False)
    try:
        stims_practice = (["left"]*(n_practice//2)) + (["right"]*(n_practice - n_practice//2))
        random.shuffle(stims_practice)

        for t, stim_dir in enumerate(stims_practice, start=1):
            fix_dur = fp_practice[t-1]
            fp_ms = fix_dur * 1000.0
            fix_clock = core.Clock()
            _clear_all_kb(kb_local)

            while fix_clock.getTime() < fix_dur:
                stim_fix.draw()
                win.flip()
                keys = kb_local.getKeys(["escape","s"], clear=True)
                if keys:
                    for k in keys:
                        if k.name == "escape":
                            cerrar()
                        if k.name == "s":
                            return {"CRT_mean_rt_correct":"","CRT_acc":""}

            correct_key = "left" if stim_dir == "left" else "right"
            target = left_stim if stim_dir == "left" else right_stim
            response_key = ""
            resp_time = ""
            rt_ms = ""

            _clear_all_kb(kb_local)
            target.draw()
            stim_onset_time = win.flip()

            rt_clock = core.Clock()
            rt_clock.reset()

            while rt_clock.getTime() < max_rt:
                keys = kb_local.getKeys(["escape","left","right","s"], clear=True)
                if keys:
                    k = keys[0].name
                    if k == "escape":
                        cerrar()
                    if k == "s":
                        return {"CRT_mean_rt_correct":"","CRT_acc":""}
                    if k in ["left","right"]:
                        response_key = k
                        resp_time = core.getTime()
                        rt_ms = (resp_time - stim_onset_time) * 1000.0
                        win.flip()
                        break

                target.draw()
                win.flip()

            core.wait(iti)
            save_processing_trial_row(
                participant_id=participant_id,
                session_id=SESSION_ID,
                task="CRT_PRACTICE",
                trial_index=t,
                stimulus=stim_dir,
                correct_answer=correct_key,
                response=response_key,
                rt_ms=rt_ms,
                stim_onset_time=stim_onset_time,
                resp_time=resp_time,
                digit="",
                foreperiod_ms=fp_ms,
                mapping_id=""
            )
        win.setMouseVisible(True)
        mostrar_instruccion_con_boton(win, mouse,
            "Ahora van a aparecer 40 flechas. De la misma forma que en la práctica, "
            "tenés que responder correctamente lo más rápido que puedas.\n\nApretá SIGUIENTE para comenzar.")

        win.setMouseVisible(False)

        stims_test = (["left"]*(n_test//2)) + (["right"]*(n_test - n_test//2))
        random.shuffle(stims_test)
        correct_rts_test_sec = []
        correct_count = 0

        for t, stim_dir in enumerate(stims_test, start=1):
            fix_dur = fp_test[t-1]
            fix_clock = core.Clock()
            _clear_all_kb(kb_local)

            while fix_clock.getTime() < fix_dur:
                stim_fix.draw()
                win.flip()
                keys = kb_local.getKeys(["escape","s"], clear=True)
                if keys:
                    for k in keys:
                        if k.name == "escape":
                            cerrar()
                        if k.name == "s":
                            return {"CRT_mean_rt_correct":"","CRT_acc":""}

            correct_key = "left" if stim_dir == "left" else "right"
            target = left_stim if stim_dir == "left" else right_stim
            response_key = ""
            resp_time = ""
            rt_ms = ""

            _clear_all_kb(kb_local)
            target.draw()
            stim_onset_time = win.flip()

            rt_clock = core.Clock()
            rt_clock.reset()

            while rt_clock.getTime() < max_rt:
                keys = kb_local.getKeys(["escape","left","right","s"], clear=True)
                if keys:
                    k = keys[0].name
                    if k == "escape":
                        cerrar()
                    if k == "s":
                        return {"CRT_mean_rt_correct":"","CRT_acc":""}
                    if k in ["left","right"]:
                        response_key = k
                        resp_time = core.getTime()
                        rt_ms = (resp_time - stim_onset_time) * 1000.0
                        win.flip()
                        break

                target.draw()
                win.flip()

            correct = int(response_key == correct_key and response_key != "")
            if correct:
                correct_count += 1
                correct_rts_test_sec.append(rt_ms / 1000.0)

            core.wait(iti)
            save_processing_trial_row(
                participant_id=participant_id,
                session_id=SESSION_ID,
                task="CRT_TEST",
                trial_index=t,
                stimulus=stim_dir,
                correct_answer=correct_key,
                response=response_key,
                rt_ms=rt_ms,
                stim_onset_time=stim_onset_time,
                resp_time=resp_time,
                digit="",
                mapping_id=""
            )

        mean_rt = (sum(correct_rts_test_sec) / len(correct_rts_test_sec)) if correct_rts_test_sec else ""
        acc     = (correct_count / n_test) if n_test > 0 else ""
        return {"CRT_mean_rt_correct": mean_rt, "CRT_acc": acc}

    finally:
        win.setMouseVisible(True)

# =====================================
# DIGIT SYMBOL SUBSTITUTION TEST (DSST)
# =====================================
def run_digit_symbol(win, participant_id="TEST001"):
    import statistics
    try:
        from PIL import Image
    except Exception:
        Image = None

    kb_local = keyboard.Keyboard()
    mouse_local = event.Mouse(win=win)
    win.setMouseVisible(True)

    symbol_order = DS_SYMBOL_ORDER[:]
    n_symbols    = len(symbol_order)
    queue_len    = min(DS_QUEUE_LEN, n_symbols)
    active_pos   = queue_len // 2
    practice_n   = DS_PRACTICE_TRIALS
    test_secs    = DS_TEST_DURATION_S

    digit_for_symbol = {sid: i + 1 for i, sid in enumerate(symbol_order)}
    allowed_keys = [str(i) for i in range(1, n_symbols + 1)]
    keypad_keys  = [f"num_{i}" for i in range(1, n_symbols + 1)]
    key_list     = allowed_keys + keypad_keys + ["escape", "s"]

    # =========================
    # HELPERS
    # =========================
    def _aspect_size(path, target_h):
        if Image is None:
            return (target_h, target_h)
        try:
            with Image.open(path) as im:
                w, h = im.size
            if h == 0:
                return (target_h, target_h)
            return (int(target_h * (w / h)), int(target_h))
        except Exception:
            return (target_h, target_h)

    def _x_positions(n, total_w):
        if n == 1:
            return [0]
        left = -total_w / 2.0
        step = total_w / (n - 1)
        return [left + i * step for i in range(n)]

    def wait_response(max_wait=None):
        kb_local.clearEvents()
        rt_clock = core.Clock()
        rt_clock.reset()
        while True:
            if max_wait is not None and rt_clock.getTime() >= max_wait:
                return None, None, None

            keys = kb_local.getKeys(key_list, waitRelease=False, clear=True)
            if keys:
                k = keys[0].name
                if k == "escape":
                    cerrar()
                if k == "s":
                    return "SKIP", None, None
                if k in allowed_keys:
                    return int(k), rt_clock.getTime(), k
                if k in keypad_keys:
                    return int(k.split("_")[-1]), rt_clock.getTime(), k

            core.wait(0.001)

    def wait_next_button(draw_fn, screen_text, button_text="SIGUIENTE >"):
        btn_pos = (470, -350)

        btn_box = visual.Rect(
            win, width=260, height=52, pos=btn_pos,
            fillColor=None, lineColor=TEXT_COLOR, lineWidth=3, units="pix"
        )
        btn_txt = visual.TextStim(
            win, text=button_text, color=TEXT_COLOR,
            height=26, pos=btn_pos, units="pix", bold=True
        )

        CHARS_PER_SEC = 45.0
        LOCK_SECS = max(0.8, len(screen_text) / CHARS_PER_SEC)

        mouse_local.clickReset()
        kb_local.clearEvents()
        event.clearEvents()
        core.wait(0.10)
        lock_clock = core.Clock()

        while True:
            elapsed = lock_clock.getTime()
            locked = elapsed < LOCK_SECS

            draw_fn()

            if locked:
                btn_box.fillColor = BTN_FILL_LOCK
                btn_box.lineColor = BTN_FILL_LOCK
                btn_txt.color     = BTN_TEXT_COLOR
            else:
                btn_box.fillColor = BTN_FILL_HOVER if btn_box.contains(mouse_local) else BTN_FILL
                btn_box.lineColor = BTN_FILL
                btn_txt.color     = BTN_TEXT_COLOR
            btn_box.draw()
            btn_txt.draw()
            win.flip()

            if not locked and mouse_local.getPressed()[0] and btn_box.contains(mouse_local):
                while mouse_local.getPressed()[0]:
                    pass
                wipe(1)
                return

            keys = kb_local.getKeys(["return", "enter", "space", "escape", "s"], clear=True)
            if keys:
                k = keys[0].name
                if k == "escape":
                    cerrar()
                if not locked and k in ["return", "enter", "space", "s"]:
                    wipe(1)
                    return

            core.wait(0.01)

    # =========================
    # LAYOUTS
    # =========================
    x_key   = _x_positions(n_symbols, 980)
    x_queue = _x_positions(queue_len, 820)

    # Primer ejemplo
    instr_key_layout = {
        "box_w": 1320,
        "box_h": 210,
        "box_y": 225,
        "digit_y": 272,
        "symbol_y": 189,
        "digit_h": 42,
        "symbol_h": 102,
    }

    # Segundo ejemplo: más arriba
    instr3_key_layout = {
        "box_w": 1260,
        "box_h": 190,
        "box_y": 305,      # subir bastante
        "digit_y": 347,
        "symbol_y": 263,
        "digit_h": 38,
        "symbol_h": 94,
    }

    instr_queue_layout = {
    "box_w": 1000,
    "box_h": 175,
    "box_y": 115,
    "symbol_y": 131,
    "marks_y": 43,
    "symbol_h": 92,
    "active_w": 108,
    "active_h": 108,
    }

    task_key_layout = {
        "box_w": 1220,
        "box_h": 185,
        "box_y": 135,
        "digit_y": 180,
        "symbol_y": 95,
        "digit_h": 36,
        "symbol_h": 92,
    }
   

    # Rectángulo amarillo algo más contenido para quedar centrado sobre el símbolo
    task_queue_layout = {
    "box_w": 1100,
    "box_h": 230,
    "box_y": -95,
    "symbol_y": -65,
    "marks_y": -176,
    "symbol_h": 104,
    "active_w": 118,
    "active_h": 118,
    }

    start_key_layout = {
        "digit_y": 170,
        "symbol_y": 105,
        "digit_h": 34,
        "symbol_h": 88,
    }

    start_queue_layout = {
        "symbol_y": -10,
        "marks_y": -80,
        "symbol_h": 94,
        "active_w": 110,
        "active_h": 110,
    }

    body_y_instr1 = 70
    body_y_instr2 = -130
    body_y_instr3 = -205   # instrucción un poco más arriba
    body_y_start  = -165

    timer_pos = (510, 310)

    # =========================
    # STIMS
    # =========================
    body = visual.TextStim(
        win, text="", color=TEXT_COLOR, height=FONT_INSTR,
        pos=(0, 0), wrapWidth=1140, units="pix"
    )

    timer_txt = visual.TextStim(
        win, text="", color=TEXT_COLOR, height=30,
        pos=timer_pos, units="pix", bold=True
    )

    key_box_instr = visual.Rect(
        win, width=instr_key_layout["box_w"], height=instr_key_layout["box_h"],
        pos=(0, instr_key_layout["box_y"]),
        fillColor=BOX_FILL,
        lineColor=BOX_LINE,
        units="pix"
    )
    key_box_instr3 = visual.Rect(
        win, width=instr3_key_layout["box_w"], height=instr3_key_layout["box_h"],
        pos=(0, instr3_key_layout["box_y"]),
        fillColor=BOX_FILL,
        lineColor=BOX_LINE, lineWidth=3,
        units="pix"
    )

    queue_box_instr = visual.Rect(
        win, width=instr_queue_layout["box_w"], height=instr_queue_layout["box_h"],
        pos=(0, instr_queue_layout["box_y"]),
        fillColor=BOX_FILL,
        lineColor=BOX_LINE, lineWidth=3,
        units="pix"
    )

    key_box_task = visual.Rect(
        win, width=task_key_layout["box_w"], height=task_key_layout["box_h"],
        pos=(0, task_key_layout["box_y"]),
        fillColor=BOX_FILL,
        lineColor=BOX_LINE,lineWidth=3,
        units="pix"
    )

    queue_box_task = visual.Rect(
        win, width=task_queue_layout["box_w"], height=task_queue_layout["box_h"],
        pos=(0, task_queue_layout["box_y"]),
        fillColor=BOX_FILL,
        lineColor=BOX_LINE,lineWidth=3,
        units="pix"
    )

    active_rect_instr = visual.Rect(
        win,
        width=instr_queue_layout["active_w"], height=instr_queue_layout["active_h"],
        pos=(0, instr_queue_layout["symbol_y"]),
        fillColor=None,
        lineColor=[255, 122, 0],
        colorSpace="rgb255",
        lineWidth=8,
        units="pix",
        opacity=1.0
    )

    active_rect_task = visual.Rect(
        win,
        width=task_queue_layout["active_w"], height=task_queue_layout["active_h"],
        pos=(0, task_queue_layout["symbol_y"]),
        fillColor=None,
        lineColor=[255, 122, 0],
        colorSpace="rgb255",
        lineWidth=8,
        units="pix",
        opacity=1.0
    )

    active_rect_start = visual.Rect(
        win,
        width=start_queue_layout["active_w"], height=start_queue_layout["active_h"],
        pos=(0, start_queue_layout["symbol_y"]),
        fillColor=None,
        lineColor=[255, 122, 0],
        colorSpace="rgb255",
        lineWidth=8,
        units="pix",
        opacity=1.0
    )

    key_digit_stims = [
        visual.TextStim(
            win, text=str(i + 1), color=TEXT_COLOR, height=36,
            pos=(0, 0), units="pix", bold=True
        )
        for i in range(n_symbols)
    ]

    key_symbols = {}
    for sid in symbol_order:
        key_symbols[sid] = visual.ImageStim(
            win,
            image=IMG_PATH_DS[sid],
            pos=(0, 0),
            size=_aspect_size(IMG_PATH_DS[sid], 90),
            units="pix",
            interpolate=True
        )

    queue_symbols = {}
    for sid in symbol_order:
        queue_symbols[sid] = visual.ImageStim(
            win,
            image=IMG_PATH_DS[sid],
            pos=(0, 0),
            size=_aspect_size(IMG_PATH_DS[sid], 98),
            units="pix",
            interpolate=True
        )

    mark_stims = [
    visual.TextStim(
        win, text="", color=TEXT_COLOR, height=40,
        pos=(0, 0), units="pix", bold=True
    )
    for _ in range(queue_len)
    ]

    feedback = visual.TextStim(
    win, text="", color=TEXT_COLOR, height=34,
    pos=(0, -290), units="pix", wrapWidth=1060, bold=True
    )

    # =========================
    # DRAW FUNCTIONS
    # =========================
    def draw_key_contents(layout):
        for i, sid in enumerate(symbol_order):
            key_digit_stims[i].height = layout["digit_h"]
            key_digit_stims[i].pos = (x_key[i], layout["digit_y"])
            key_digit_stims[i].draw()

            stim = key_symbols[sid]
            stim.pos = (x_key[i], layout["symbol_y"])
            stim.size = _aspect_size(IMG_PATH_DS[sid], layout["symbol_h"])
            stim.draw()

    def draw_key(layout, boxed=True):
        if boxed:
            if layout is instr_key_layout:
                key_box_instr.draw()
            elif layout is instr3_key_layout:
                key_box_instr3.draw()
            elif layout is task_key_layout:
                key_box_task.draw()
        draw_key_contents(layout)

    def draw_queue_contents(batch, response_marks, layout, mode="task"):
        for j, sid in enumerate(batch):
            stim = queue_symbols[sid]
            stim.pos = (x_queue[j], layout["symbol_y"])
            stim.size = _aspect_size(IMG_PATH_DS[sid], layout["symbol_h"])
            stim.draw()

            if j < len(mark_stims):
                mark_stims[j].pos = (x_queue[j], layout["marks_y"])
                mark_stims[j].text = str(response_marks[j]) if response_marks[j] not in ["", None] else ""
                if mark_stims[j].text != "":
                    mark_stims[j].draw()

        active_x = x_queue[active_pos]

        if mode == "instr":
            active_rect_instr.pos = (active_x, layout["symbol_y"])
            active_rect_instr.draw()
        elif mode == "start":
            active_rect_start.pos = (active_x, layout["symbol_y"])
            active_rect_start.draw()
        else:
            active_rect_task.pos = (active_x, layout["symbol_y"])
            active_rect_task.draw()

    def draw_queue(batch, response_marks, layout, boxed=True, mode="task"):
        if boxed:
            if layout is instr_queue_layout:
                queue_box_instr.draw()
            elif layout is task_queue_layout:
                queue_box_task.draw()
        draw_queue_contents(batch, response_marks, layout, mode=mode)

    # =========================
    # PREVIEW DATA
    # =========================
    preview_rng = random.Random("preview_ds")
    preview_batch = [preview_rng.choice(symbol_order) for _ in range(queue_len)]
    preview_marks = [""] * queue_len
    preview_marks[active_pos] = str(digit_for_symbol[preview_batch[active_pos]])

    # =========================
    # INSTRUCCIONES
    # =========================
    screen1_text = (
        "En esta tarea vas a ver una clave con símbolos y números.\n\n"
        "Tu tarea es apretar el número que corresponde a cada símbolo según la clave que va a aparecer arriba.\n\n"
        "Respondé lo más rápido y mejor que puedas."
    )

    def draw_instr_1():
        body.text = screen1_text
        body.pos = (0, body_y_instr1)
        body.draw()

    wait_next_button(draw_instr_1, screen1_text, "SIGUIENTE >")

    screen2_text = (
        "La clave muestra qué número corresponde a cada símbolo.\n\n"
        "No tenés que memorizar nada: la clave va a quedar siempre en la pantalla.\n\n"
        "Cada vez que aparezca un símbolo resaltado, presioná la tecla del número correspondiente al símbolo resaltado.\n\n"
    )

    def draw_instr_2():
        draw_key(instr_key_layout, boxed=True)
        body.text = screen2_text
        body.pos = (0, body_y_instr2)
        body.draw()

    wait_next_button(draw_instr_2, screen2_text, "SIGUIENTE >")

    screen3_text = (
        "En el centro vas a ver una fila de símbolos.\n\n"
        "El símbolo resaltado es el que tenés que responder en ese momento.\n\n"
        "Presioná la tecla del número correspondiente al símbolo resaltado.\n\n"
        "Primero vas a hacer una práctica corta.\n"
        "Después harás la tarea real.\n"
        "La tarea real dura 2 minutos."
    )
    
    def draw_instr_3():
        draw_key(instr3_key_layout, boxed=True)
        draw_queue(preview_batch, preview_marks, instr_queue_layout, boxed=True, mode="instr")
        body.text = screen3_text
        body.pos = (0, body_y_instr3)
        body.draw()

    wait_next_button(draw_instr_3, screen3_text, "SIGUIENTE >")

    # =========================
    # PRÁCTICA
    # =========================
    win.setMouseVisible(False)

    practice_rng = random.Random(SESSION_ID + "_DS_PRACTICE")
    practice_queue = [practice_rng.choice(symbol_order) for _ in range(queue_len)]
    practice_marks = [""] * queue_len

    for t in range(practice_n):
        sid = practice_queue[active_pos]
        correct_digit = digit_for_symbol[sid]

        draw_key(task_key_layout, boxed=True)
        draw_queue(practice_queue, practice_marks, task_queue_layout, boxed=True, mode="task")
        timer_txt.text = ""
        timer_txt.draw()
        win.flip()
        stim_onset_time = core.getTime()

        resp_digit, rt_s, raw_key = wait_response(max_wait=8.0)

        if resp_digit == "SKIP":
            win.setMouseVisible(True)
            return {"DS_score": 0, "DS_total": 0, "DS_acc": 0, "DS_medianRTc": ""}

        rt_ms = "" if rt_s is None else rt_s * 1000.0
        is_correct = int(resp_digit == correct_digit)

        if resp_digit is not None:
            practice_marks[active_pos] = str(resp_digit)

        flash_clock = core.Clock()
        while flash_clock.getTime() < 0.18:
            draw_key(task_key_layout, boxed=True)
            draw_queue(practice_queue, practice_marks, task_queue_layout, boxed=True, mode="task")
            win.flip()

        if resp_digit is None:
            feedback.text = f"Sin respuesta. La respuesta correcta era {correct_digit}."
            feedback.color = [0.95, 0.55, 0.55]
        elif is_correct:
            feedback.text = "Correcto"
            feedback.color = [-0.80, 0.20, -0.80]
        else:
            feedback.text = f"Incorrecto. La respuesta correcta era {correct_digit}."
            feedback.color = [0.65, -0.80, -0.80]

        fb_clock = core.Clock()
        while fb_clock.getTime() < 0.45:
            draw_key(task_key_layout, boxed=True)
            draw_queue(practice_queue, practice_marks, task_queue_layout, boxed=True, mode="task")
            feedback.draw()
            win.flip()

        save_processing_trial_row(
            participant_id=participant_id,
            session_id=SESSION_ID,
            task="DIGIT_SYMBOL_PRACTICE",
            trial_index=t + 1,
            stimulus=str(sid),
            correct_answer=str(correct_digit),
            response="" if resp_digit is None else str(resp_digit),
            rt_ms=rt_ms,
            stim_onset_time=stim_onset_time,
            resp_time="" if rt_s is None else (stim_onset_time + rt_s),
            foreperiod_ms="",
            digit=str(correct_digit),
            mapping_id=MAPPING_ID_DS
        )

        practice_queue = practice_queue[1:] + [practice_rng.choice(symbol_order)]
        practice_marks = practice_marks[1:] + [""]

    # =========================
    # INICIO TAREA REAL
    # =========================
    start_text = (
        "Ahora empieza la tarea real.\n\n"
        "Vas a tener 2 minutos para hacer la mayor cantidad posible.\n\n"
        "Respondé lo más rápido y correctamente posible."
    )

    def draw_start():
        body.text = start_text
        body.pos = (0, 40)
        body.draw()

    win.setMouseVisible(True)
    wait_next_button(draw_start, start_text, "SIGUIENTE >")

    # =========================
    # TAREA REAL
    # =========================
    win.setMouseVisible(False)

    rng = random.Random(SESSION_ID + "_DS_TEST")
    test_queue = [rng.choice(symbol_order) for _ in range(queue_len)]
    response_marks = [""] * queue_len

    test_clock = core.Clock()
    test_clock.reset()

    score = 0
    total = 0
    trial_idx = 0
    correct_rts = []

    while test_clock.getTime() < test_secs:
        sid = test_queue[active_pos]
        correct_digit = digit_for_symbol[sid]
        time_left = max(0.0, test_secs - test_clock.getTime())

        draw_key(task_key_layout, boxed=True)
        draw_queue(test_queue, response_marks, task_queue_layout, boxed=True, mode="task")
        win.flip()
        stim_onset_time = core.getTime()

        resp_digit, rt_s, raw_key = wait_response(max_wait=time_left)

        if resp_digit in [None, "SKIP"]:
            break

        rt_ms = rt_s * 1000.0
        trial_idx += 1
        total += 1

        response_marks[active_pos] = str(resp_digit)

        flash_clock = core.Clock()
        while flash_clock.getTime() < 0.12:
            draw_key(task_key_layout, boxed=True)
            draw_queue(test_queue, response_marks, task_queue_layout, boxed=True, mode="task")
            win.flip()

        if resp_digit == correct_digit:
            score += 1
            correct_rts.append(rt_ms)

        save_processing_trial_row(
            participant_id=participant_id,
            session_id=SESSION_ID,
            task="DIGIT_SYMBOL",
            trial_index=trial_idx,
            stimulus=str(sid),
            correct_answer=str(correct_digit),
            response=str(resp_digit),
            rt_ms=rt_ms,
            stim_onset_time=stim_onset_time,
            resp_time=stim_onset_time + rt_s,
            foreperiod_ms="",
            digit=str(correct_digit),
            mapping_id=MAPPING_ID_DS
        )

        test_queue = test_queue[1:] + [rng.choice(symbol_order)]
        response_marks = response_marks[1:] + [""]

    acc = (score / total) if total > 0 else 0
    medianRTc = statistics.median(correct_rts) if correct_rts else ""

    win.setMouseVisible(True)
    wipe(2)

    return {
        "DS_score": score,
        "DS_total": total,
        "DS_acc": acc,
        "DS_medianRTc": medianRTc
    }
def run_processing_speed_battery(win, participant_id):
    out_srt = run_srt(win, participant_id, n_practice=8, n_test=20)
    out_crt = run_crt(win, participant_id, n_practice=8, n_test=40)
    out_ds  = run_digit_symbol(win, participant_id)
    results = {}; results.update(out_srt); results.update(out_crt); results.update(out_ds)
    return results


# =========================
# LISTADO PANAS EN TABLA
# =========================
def pasar_panas_lista(etiqueta_momento="PANAS"):

    mostrar_instruccion_con_boton(win, mouse,
        "A continuación vas a responder un cuestionario.\n\n"
        "No hay respuestas correctas o incorrectas, sólo nos interesa tu opinión honesta.",
        font_height=46)
    wipe(1)

    # ── Dimensiones ───────────────────────────────────────────────────
    CONTENT_WIDTH = 1240
    CONTENT_LEFT  = -CONTENT_WIDTH / 2.0
    ITEM_COL_W    = 360
    RESP_COLS     = 5
    RESP_COL_W    = (CONTENT_WIDTH - ITEM_COL_W) / RESP_COLS   # ~158 px

    ROW_H      = 60
    HEADER_H   = 92
    LIST_TOP_Y = 300

    col_centers_x = [
        CONTENT_LEFT + ITEM_COL_W + RESP_COL_W * (i + 0.5)
        for i in range(RESP_COLS)
    ]

    # ── Colores ───────────────────────────────────────────────────────
    C_ROW_EVEN   = PANAS_ROW_EVEN
    C_ROW_ODD    = PANAS_ROW_ODD
    C_ROW_SEL    = PANAS_ROW_SEL
    C_HEADER_BG  = PANAS_HDR_BG
    C_DOT_EMPTY  = PANAS_DOT_EMPTY
    C_DOT_FILL   = PANAS_DOT_FILL
    C_BTN_OFF    = BTN_FILL
    C_BTN_HOVER  = BTN_FILL_HOVER
    C_BTN_ACTIVE = BTN_FILL_HOVER

    # ── Estímulos ─────────────────────────────────────────────────────
    row_bg    = visual.Rect(win, width=CONTENT_WIDTH, height=ROW_H,
                            lineColor=None, units="pix")
    hdr_bg    = visual.Rect(win, width=CONTENT_WIDTH, height=HEADER_H,
                            fillColor=C_HEADER_BG, lineColor=None, units="pix")
    dot_empty = visual.Circle(
        win,
        radius=10,
        fillColor=BG_COLOR,
        lineColor=[-0.20, -0.20, -0.20],
        lineWidth=2,
        units="pix"
    )
    dot_fill  = visual.Circle(win, radius=10, fillColor=C_DOT_FILL,
                              lineColor=C_DOT_FILL, units="pix")
    sep_line  = visual.Rect(win, width=CONTENT_WIDTH, height=1,
                            fillColor=[-0.30,-0.30,-0.30],
                            lineColor=[-0.30,-0.30,-0.30], units="pix")

    # Header — misma altura de letra que los ítems (26 px)
    hdr_labels = [
        visual.TextStim(win, text=COL_TITLES[i], color=TEXT_COLOR,
                        height=26, wrapWidth=RESP_COL_W - 12,
                        pos=(col_centers_x[i], 0), alignText="center", units="pix")
        for i in range(RESP_COLS)
    ]

    item_lbl = visual.TextStim(win, text="", color=TEXT_COLOR, height=26,
                               wrapWidth=ITEM_COL_W - 22,
                               alignText="left", anchorHoriz="left",
                               anchorVert="center", units="pix")

    BTN_POS = (0.80, -0.95)
    BTN_W_N = 0.32
    BTN_H_N = 0.10
    btn_box = visual.Rect(
        win, width=BTN_W_N, height=BTN_H_N, pos=BTN_POS,
        units="norm", fillColor=None, lineColor=[0.55, 0.55, 0.55], lineWidth=2
    )
    btn_lbl = visual.TextStim(
        win, text="SIGUIENTE", color=[0.45, 0.45, 0.45],
        height=0.042, pos=BTN_POS, units="norm", bold=True
    )

    n_items = len(PANAS_ITEMS)
    ratings = [None] * n_items

    def mouse_on_row(mx, my, row_y):
        return (abs(mx) <= CONTENT_WIDTH / 2.0) and (abs(my - row_y) <= ROW_H / 2.0)

    def col_clicked(mx):
        for ci, cx in enumerate(col_centers_x):
            if abs(mx - cx) <= RESP_COL_W / 2.0:
                return ci
        return None

    # ── Lógica de selección inteligente ───────────────────────────────
    def next_incomplete(desde, start, end):
        """Busca el próximo ítem sin responder.
        Primero busca hacia abajo desde `desde`, luego vuelve al inicio.
        Devuelve None si todos están completos."""
        for i in range(desde, end):
            if ratings[i] is None:
                return i
        for i in range(start, desde):
            if ratings[i] is None:
                return i
        return None  # todos completos

    # ── Función de página ─────────────────────────────────────────────
    def run_page(start, end, is_last_page=False):
        nonlocal ratings
        n_page = end - start

        # El foco arranca en el primer ítem incompleto de la página
        sel = next_incomplete(start, start, end)

        mouse.clickReset(); event.clearEvents(); kb.clearEvents()

        while True:
            done_count = sum(1 for i in range(start, end) if ratings[i] is not None)
            all_done   = (done_count == n_page)

            # instrucción superior — 
            instr_text.height = 36
            instr_text.pos    = (0, 360)
            instr_text.text   = INSTRUCCIONES_ESCALA
            instr_text.draw()

            # header
            hdr_y = LIST_TOP_Y - HEADER_H / 2.0
            hdr_bg.pos = (0, hdr_y); hdr_bg.draw()
            for lbl in hdr_labels:
                lbl.pos = (lbl.pos[0], hdr_y); lbl.draw()
            sep_line.pos = (0, LIST_TOP_Y - HEADER_H); sep_line.draw()

            # filas
            grid_top = LIST_TOP_Y - HEADER_H
            for ri in range(n_page):
                gi    = start + ri
                row_y = grid_top - (ri + 0.5) * ROW_H

                # resaltar solo si sel no es None
                if sel is not None and gi == sel:
                    row_bg.fillColor = C_ROW_SEL
                elif ri % 2 == 0:
                    row_bg.fillColor = C_ROW_EVEN
                else:
                    row_bg.fillColor = C_ROW_ODD
                row_bg.pos = (0, row_y); row_bg.draw()

                item_lbl.text = PANAS_ITEMS[gi]
                item_lbl.pos  = (CONTENT_LEFT + 12, row_y)
                item_lbl.draw()

                for ci, cx in enumerate(col_centers_x):
                    if ratings[gi] is not None and ratings[gi] - 1 == ci:
                        dot_fill.pos = (cx, row_y); dot_fill.draw()
                    else:
                        dot_empty.pos = (cx, row_y); dot_empty.draw()

                if ri < n_page - 1:
                    sep_line.pos = (0, row_y - ROW_H / 2.0); sep_line.draw()

            sep_line.pos = (0, grid_top - n_page * ROW_H); sep_line.draw()

            # botón — resaltado especial cuando all_done
            is_hovering = btn_box.contains(mouse)
            if all_done:
                btn_box.fillColor = BTN_FILL_HOVER if is_hovering else BTN_FILL
                btn_box.lineColor = BTN_FILL
                btn_lbl.color     = BTN_TEXT_COLOR
            else:
                btn_box.fillColor = None
                btn_box.lineColor = [0.55, 0.55, 0.55]
                btn_lbl.color     = [0.45, 0.45, 0.45]
            btn_lbl.text  = "SIGUIENTE"
            btn_lbl.color = BTN_TEXT_COLOR if all_done else [0.55, 0.53, 0.47]
            btn_box.draw(); btn_lbl.draw()

            win.flip()

            # ── teclado ──
            k = get_last_key(["up","down","1","2","3","4","5","return","enter","escape","s"])
            if k == "escape": cerrar()
            elif k == "s": return True
            elif k == "up":
                if sel is not None: sel = max(start, sel - 1)
            elif k == "down":
                if sel is not None: sel = min(end - 1, sel + 1)
                
            elif k in ["1","2","3","4","5"]:
                if sel is not None:
                    ratings[sel] = int(k)
                    sel = next_incomplete(sel + 1, start, end)
            elif k in ["return","enter"]:
                if all_done: return True

            # ── mouse ──
            if mouse.getPressed()[0]:
                mx, my = mouse.getPos()
                if btn_box.contains(mouse) and all_done:
                    btn_box.fillColor = C_BTN_ACTIVE
                    btn_box.draw(); btn_lbl.draw(); win.flip()
                    while mouse.getPressed()[0]: pass
                    return True
                grid_top_local = LIST_TOP_Y - HEADER_H
                for ri in range(n_page):
                    gi    = start + ri
                    row_y = grid_top_local - (ri + 0.5) * ROW_H
                    if mouse_on_row(mx, my, row_y):
                        ci = col_clicked(mx)
                        if ci is not None:
                            ratings[gi] = ci + 1
                            sel = next_incomplete(gi + 1, start, end)
                        else:
                            sel = gi   # click en texto: solo mover foco
                        while mouse.getPressed()[0]: pass
                        break

            core.wait(0.008)

    run_page(0, 10, is_last_page=False); wipe(1)
    run_page(10, n_items, is_last_page=True)
    wipe(2)
    return {
    f"{etiqueta_momento}_{iid}": (int(ratings[i]) if ratings[i] is not None else "")
    for i, iid in enumerate(PANAS_ITEM_IDS)
    }
# =========================
# BART
# =========================
def createTrialHandler(colorList, maxPumps, n_trials, REWARD):
    trialList = []
    for _ in range(n_trials):
        idx = random.randrange(len(colorList))
        trialList.append({'balloon_img': os.path.join(BART_DIR, colorList[idx]+'Balloon.png'),
                          'pop_img':     os.path.join(BART_DIR, colorList[idx]+'Pop.png'),
                          'maxPumps':    maxPumps[idx], 'reward': REWARD})
    random.shuffle(trialList)
    return data.TrialHandler(trialList, nReps=1, method='sequential')

def drawText(TextStimObj, pos, txt, alignment='right'):
    TextStimObj.pos = pos
    TextStimObj.text = txt
    TextStimObj.alignText = alignment
    TextStimObj.draw()

def showImg(img, size, wait=1):
    stim.setImage(img); stim.size = size; stim.draw(); win.flip(); core.wait(wait)

def drawTrial(ballSize, ballImage, lastMoney, totalMoney):
    stim.size = ballSize; stim.setImage(ballImage); stim.draw()
    drawText(remind_return, (-0.23,-0.9), 'Apretá ENTER\npara cobrar', 'center')
    drawText(remind_enter,  (0.23,-0.9),  'Apretá ESPACIO\npara inflar', 'center')
    drawText(bart_text, (0.4,-0.6), f'Último Globo: \n{lastMoney:.2f} $')
    drawText(bart_text, (0.4,-0.9), f'Total: \n{round(totalMoney,2):.2f} $')
    win.flip()

def showInstruction(img, texto_boton="SIGUIENTE >"):
    instruction = visual.ImageStim(win, image=img, pos=(0, 0), size=(2, 2), units='norm')

    mask_rect = visual.Rect(
        win,
        width=1.6,
        height=0.40,
        pos=(0, -0.85),
        units='norm',
        fillColor=BG_COLOR,
        lineColor=None
    )

    btn_w, btn_h = 0.25, 0.10
    btn_pos = (0.75, -0.85)

    btn_box = visual.Rect(
        win,
        width=btn_w,
        height=btn_h,
        pos=btn_pos,
        units='norm',
        fillColor=BTN_FILL,
        lineColor=BTN_FILL,
        lineWidth=3
    )

    btn_txt = visual.TextStim(
        win,
        text=texto_boton,
        color=BTN_TEXT_COLOR,
        units='norm',
        height=0.05,
        pos=btn_pos,
        bold=True
    )

    core.wait(0.5)
    event.clearEvents()
    mouse.clickReset()

    while True:
        instruction.draw()
        mask_rect.draw()

        btn_box.fillColor = BTN_FILL_HOVER if btn_box.contains(mouse) else BTN_FILL
        btn_box.lineColor = BTN_FILL
        btn_box.draw()
        btn_txt.draw()
        win.flip()

        if mouse.getPressed()[0] and btn_box.contains(mouse):
            btn_box.fillColor = BTN_FILL_HOVER
            btn_box.lineColor = BTN_FILL
            btn_box.draw()
            btn_txt.draw()
            win.flip()
            while mouse.getPressed()[0]:
                pass
            return 'next'

        keys = event.getKeys(keyList=['space', 'return', 'enter', 'escape', 's'])
        if keys:
            if 'escape' in keys:
                cerrar()
                return KEY_QUIT
            return 'next'

def bart(info, phase, custom_intro_text=None):
    trials = createTrialHandler(COLOR_LIST, MAX_PUMPS, REPETITIONS, REWARD)

    BART_BTN_POS = (470, -370)
    BART_BTN_W = 260
    BART_BTN_H = 52
    BART_BTN_TEXT_H = 26

    texto_intro = custom_intro_text or (
        "A continuación vas a participar de un juego.\n"
        "Hacé clic en SIGUIENTE para ver cómo funciona."
    )

    mostrar_instruccion_con_boton(
        win, mouse, texto_intro,
        font_height=42,
        btn_width=BART_BTN_W,
        btn_height=BART_BTN_H,
        btn_text_height=BART_BTN_TEXT_H,
        align_text="left",
        btn_pos=BART_BTN_POS
    )

    mostrar_instruccion_con_boton(
        win, mouse,
        "El juego consiste en optimizar las ganancias en una competencia de inflar globos.\n\n"
        "Durante la tarea se te presentarán 30 globos, uno a la vez.\n\n"
        "Vas a ganar plata por cada globo que lográs inflar sin que explote.\n\n"
        "El punto de explosión varía entre globos, desde el primer bombeo hasta suficientes bombeos como para llenar toda la pantalla.\n\n"
        "Tené en cuenta que los globos que exploten no afectan a la plata que ya ganaste.\n\n"
        "Apretá SIGUIENTE para continuar.",
        boton_texto="SIGUIENTE >",
        font_height=36,
        btn_width=BART_BTN_W,
        btn_height=BART_BTN_H,
        btn_text_height=BART_BTN_TEXT_H,
        align_text="left",
        btn_pos=BART_BTN_POS
    )

    mostrar_instruccion_con_boton(
        win, mouse,
        "Apretá la barra espaciadora para inflar el globo.\n\n"
        "En cualquier momento podés dejar de inflar el globo y apretar ENTER para cobrar.\n\n"
        "Por cada bombeo vas a acumular 5 centavos en un banco temporal. Plata que no vas a poder ver hasta que cobres.\n\n"
        "La plata que acumulaste se va a guardar en tu \"Total Ganado\" y pasás al siguiente globo.\n\n"
        "En la casilla \"Último Globo\" te va a decir cuánto ganaste en el globo anterior.\n\n"
        "Si el globo explota antes de que cobres, pasás al siguiente globo ganando nada.\n\n"
        "Apretá SIGUIENTE para continuar.",
        boton_texto="SIGUIENTE >",
        font_height=34,
        btn_width=BART_BTN_W,
        btn_height=BART_BTN_H,
        btn_text_height=BART_BTN_TEXT_H,
        align_text="left",
        texto_pos=(0, 160),
        imagen_abajo=INSTRUCCIONES_BART_IMG,
        imagen_abajo_size=fit_image_to_width(INSTRUCCIONES_BART_IMG, 760),
        imagen_abajo_pos=(0, -270),
        btn_pos=BART_BTN_POS
    )

    mostrar_instruccion_con_boton(
        win, mouse,
        "La plata que juntes en el juego define cuántos números obtenés para la rifa.\n\n"
        "Intentá ganar la mayor cantidad posible.\n\n"
        "Apretá SIGUIENTE para continuar.",
        boton_texto="SIGUIENTE >",
        font_height=36,
        btn_width=BART_BTN_W,
        btn_height=BART_BTN_H,
        btn_text_height=FONT_BTN,
        align_text="left",
        btn_pos=BART_BTN_POS
    )

    win.setMouseVisible(False)
    try:
        permBank = 0
        lastTempBank = 0

        for trialNumber, trial in enumerate(trials, start=1):
            tempBank = 0
            pop = False
            nPumps = 0
            continuePumping = True
            increase = 0
            ballSize = INITIAL_BALL_SIZE
            stim.size = ballSize
            event_index = 0
            balloon_end_logged = False

            save_bart_event(
                PARTICIPANT_ID, SESSION_ID, phase, trialNumber,
                "balloon_start", event_index, rt_ms="", pump_number=0
            )

            while continuePumping and not pop:
                ballSize = (
                    INITIAL_BALL_SIZE[0] + BALL_TEXTURE_SIZE[0] * increase,
                    INITIAL_BALL_SIZE[1] + BALL_TEXTURE_SIZE[1] * increase
                )
                drawTrial(ballSize, trial['balloon_img'], lastTempBank, permBank)

                resp_clock = core.Clock()
                resp_clock.reset()
                respond = event.waitKeys(
                    keyList=[KEY_PUMP, KEY_NEXT, KEY_QUIT, KEY_SKIP],
                    maxWait=15,
                    timeStamped=resp_clock
                )

                if not respond:
                    drawText(bart_text, (0, 0), ABSENT_MESSAGE, 'center')
                    win.flip()
                    core.wait(5)
                    continuePumping = False
                    event_index += 1
                    save_bart_event(
                        PARTICIPANT_ID, SESSION_ID, phase, trialNumber,
                        "balloon_end", event_index, rt_ms="", pump_number=nPumps
                    )
                    balloon_end_logged = True
                    break

                key, rt_s = respond[0]

                if key == KEY_QUIT:
                    return permBank
                elif key == KEY_SKIP:
                    return permBank

                rt_ms = rt_s * 1000.0

                if key == KEY_NEXT:
                    event_index += 1
                    save_bart_event(
                        PARTICIPANT_ID, SESSION_ID, phase, trialNumber,
                        "cashout", event_index, rt_ms=rt_ms, pump_number=nPumps
                    )
                    lastTempBank = tempBank
                    safe_sound_play(slot_machine)
                    newBalance = permBank + tempBank
                    while round(permBank, 2) < round(newBalance, 2):
                        permBank += 0.01
                        drawText(bart_text, (0.4, -0.9), 'Total ganado:\n{:.2f} $'.format(permBank))
                        win.flip()
                    permBank = newBalance
                    continuePumping = False

                elif key == KEY_PUMP:
                    nPumps += 1
                    event_index += 1
                    save_bart_event(
                        PARTICIPANT_ID, SESSION_ID, phase, trialNumber,
                        "pump", event_index, rt_ms=rt_ms, pump_number=nPumps
                    )

                    if random.random() < 1.0 / (trial['maxPumps'] - nPumps):
                        safe_sound_play(pop_sound)
                        showImg(trial['pop_img'], POP_TEXTURE_SIZE)
                        lastTempBank = 0
                        pop = True
                        event_index += 1
                        save_bart_event(
                            PARTICIPANT_ID, SESSION_ID, phase, trialNumber,
                            "explosion", event_index, rt_ms="", pump_number=nPumps
                        )
                    else:
                        tempBank += REWARD
                        increase += 0.8 / max(MAX_PUMPS)

            if not balloon_end_logged:
                event_index += 1
                save_bart_event(
                    PARTICIPANT_ID, SESSION_ID, phase, trialNumber,
                    "balloon_end", event_index, rt_ms="", pump_number=nPumps
                )

        drawText(bart_text, (0, 0), FINAL_MESSAGE.format(permBank), 'center')
        win.flip()
        core.wait(5)
        return permBank

    finally:
        win.setMouseVisible(True)

# =========================
# FLUJO EXPERIMENTO
# =========================
try:
    mostrar_instruccion_con_boton(win, mouse,
        "¡Bienvenido/a!\n\n"
        "El siguiente estudio tiene como objetivo evaluar la toma de decisiones.\n\n"
        "Vas a realizar diferentes ejercicios y completar un cuestionario.\n\n"
        "Una vez finalizado el estudio se rifará un premio entre todos los participantes.\n\n"
        "Tus respuestas son anónimas y se utilizarán únicamente con fines académicos.\n\n"
        "Podés interrumpir tu participación en cualquier momento presionando la tecla Esc.",
        font_height=34)
    mostrar_instruccion_con_boton(
    win, mouse,
    "IMPORTANTE\n\nLeé con atención las instrucciones antes de cada tarea.",
    boton_texto="SIGUIENTE >",
    font_height=42,
    align_text="center"
    )

    # 1. PANAS
    panas_dict = pasar_panas_lista("PANAS")

    # 2. BART (90 globos)
    bart_money = bart(bart_info, phase="bart", custom_intro_text=(
        "A continuación vas a jugar un juego de apuestas.\n\n"
        "Tu objetivo es acumular la mayor cantidad de plata posible.\n\n"
        "Hacé clic en SIGUIENTE para ver cómo funciona el juego."))

    # 3. Batería processing speed
    proc_res = run_processing_speed_battery(win, exp_info["Participante"])

    # Cálculo de rifas
    bart_money_float = float(bart_money or 0)
    rifas = calcular_rifas(bart_money_float)
    rifa_word = "número" if rifas == 1 else "números"

    # Guardar PANAS
    save_panas_items(PARTICIPANT_ID, SESSION_ID, "panas", panas_dict)

    # Resumen
    panas_pos = sum(int(panas_dict[f"PANAS_{it}"]) for it in PANAS_POS_IDS if panas_dict.get(f"PANAS_{it}", "") != "")
    panas_neg = sum(int(panas_dict[f"PANAS_{it}"]) for it in PANAS_NEG_IDS if panas_dict.get(f"PANAS_{it}", "") != "")
    resumen = {
        "PANAS_POS_sum": panas_pos,
        "PANAS_NEG_sum": panas_neg,
        "BART_money":    bart_money,
    }
    
    # Pantalla final
    mostrar_instruccion_con_boton(win, mouse,
        f"¡Felicitaciones, terminaste!\n\n"
        f"En el juego de los globos ganaste ${bart_money_float:.2f}.\n\n"
        f"Eso te da {rifas} {rifa_word} para el sorteo.\n\n"
        f"¡Muchas gracias por participar!",
        boton_texto="FINALIZAR",
        font_height=28)
        
except Exception as e:
    mostrar_mensaje("Error", f"Ocurrió un error:\n{e}")
finally:
    bart_info["end_time"] = datetime.now().isoformat(timespec="seconds")
    save_participant_row(
        participant_id=PARTICIPANT_ID,
        group=exp_info.get("Grupo", ""),
        session_id=SESSION_ID,
        date_time_start=exp_info.get("start_time", ""),
        date_time_end=bart_info["end_time"],
        experiment_version=EXPERIMENT_VERSION,
        bart_money=bart_money_float if 'bart_money_float' in dir() else "",
        rifas=rifas if 'rifas' in dir() else "",
        panas_pos_sum=panas_pos if 'panas_pos' in dir() else "",
        panas_neg_sum=panas_neg if 'panas_neg' in dir() else ""
    )
    cerrar()