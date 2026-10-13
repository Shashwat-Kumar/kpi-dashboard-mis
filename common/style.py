"""Shared visual identity for portfolio samples: white, one accent (deep teal), Lato."""
import os
from matplotlib import font_manager as fm, rcParams
FONT_DIR = "/usr/share/fonts/truetype/sand-box/google/Lato"
for f in ("Lato-Regular.ttf","Lato-Bold.ttf","Lato-Black.ttf","Lato-Light.ttf","Lato-Italic.ttf"):
    fm.fontManager.addfont(os.path.join(FONT_DIR, f))

TEAL = "#0B5D63"; TEAL_D = "#073F43"; TEAL_L = "#5E9EA2"; TEAL_XL = "#D7E8E9"; TEAL_XXL = "#EEF5F5"
INK = "#1F2A30"; GREY = "#5B6770"; GREY_L = "#A7B0B6"; RULE = "#E3E7EA"; BG = "#FFFFFF"
# RAG used ONLY where semantically required (muted)
RED = "#B9473D"; AMBER = "#D49A2A"; GREEN = "#3F8F5A"
WATERMARK = "SAMPLE – synthetic data, fictional company"
AUTHOR = "Shashwat Kumar · Illustrative work sample"

def mpl_setup():
    rcParams.update({
        "font.family": "Lato", "font.size": 11, "text.color": INK,
        "axes.edgecolor": RULE, "axes.labelcolor": GREY, "axes.titlesize": 13,
        "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": GREY, "ytick.color": GREY, "axes.grid": True, "grid.color": RULE,
        "grid.linewidth": 0.8, "axes.axisbelow": True, "figure.facecolor": BG,
        "axes.facecolor": BG, "savefig.facecolor": BG, "legend.frameon": False,
    })

def sample_badge(fig, x=0.985, y=0.975, size=11, ha="right", va="top"):
    fig.text(x, y, "  SAMPLE · synthetic data · fictional company  ", ha=ha, va=va,
             fontsize=size, color="white", weight="bold",
             bbox=dict(boxstyle="round,pad=0.45", fc=TEAL, ec="none"))

def footer(fig, left_text="", y=0.018, size=10):
    fig.text(0.02, y, WATERMARK + (" · " + left_text if left_text else ""), fontsize=size, color=GREY, ha="left", va="bottom")
    fig.text(0.98, y, AUTHOR, fontsize=size, color=GREY, ha="right", va="bottom")

def diag_watermark(fig, alpha=0.05, size=64):
    fig.text(0.5, 0.5, "SAMPLE", fontsize=size*2, color=TEAL, alpha=alpha, ha="center", va="center",
             rotation=25, weight="black", zorder=0)

# ---------- reportlab ----------
def rl_setup():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping
    for name, f in (("Lato","Lato-Regular.ttf"),("Lato-Bold","Lato-Bold.ttf"),("Lato-Italic","Lato-Italic.ttf"),
                    ("Lato-BoldItalic","Lato-BoldItalic.ttf"),("Lato-Black","Lato-Black.ttf"),("Lato-Light","Lato-Light.ttf")):
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, f)))
    addMapping("Lato",0,0,"Lato"); addMapping("Lato",1,0,"Lato-Bold"); addMapping("Lato",0,1,"Lato-Italic"); addMapping("Lato",1,1,"Lato-BoldItalic")

def rl_styles():
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    c = colors.HexColor
    s = {}
    s["h1"] = ParagraphStyle("h1", fontName="Lato-Black", fontSize=22, leading=27, textColor=c(INK), spaceAfter=4)
    s["kicker"] = ParagraphStyle("k", fontName="Lato-Bold", fontSize=9, leading=12, textColor=c(TEAL), spaceAfter=2)
    s["h2"] = ParagraphStyle("h2", fontName="Lato-Bold", fontSize=13.5, leading=17, textColor=c(TEAL_D), spaceBefore=8, spaceAfter=4)
    s["body"] = ParagraphStyle("b", fontName="Lato", fontSize=10, leading=14.2, textColor=c(INK), spaceAfter=5)
    s["small"] = ParagraphStyle("s", fontName="Lato", fontSize=8.3, leading=11, textColor=c(GREY))
    s["cell"] = ParagraphStyle("c", fontName="Lato", fontSize=8.4, leading=10.6, textColor=c(INK))
    s["cellb"] = ParagraphStyle("cb", fontName="Lato-Bold", fontSize=8.4, leading=10.6, textColor=c(INK))
    s["cellh"] = ParagraphStyle("ch", fontName="Lato-Bold", fontSize=8.4, leading=10.6, textColor=c("#FFFFFF"))
    s["bullet"] = ParagraphStyle("bl", parent=s["body"], leftIndent=12, bulletIndent=2, spaceAfter=3)
    s["callout"] = ParagraphStyle("co", fontName="Lato", fontSize=10.5, leading=15, textColor=c(TEAL_D), backColor=c(TEAL_XXL),
                                  borderPadding=(8,10,8,10), leftIndent=10, rightIndent=10, spaceBefore=6, spaceAfter=12)
    return s

def rl_page_decor(title):
    """Return onPage callback: diagonal watermark, header rule, footer w/ SAMPLE note and page number."""
    from reportlab.lib import colors
    def _draw(canv, doc):
        w, h = doc.pagesize
        canv.saveState()
        canv.setFillColor(colors.HexColor(TEAL)); canv.setFillAlpha(0.045)
        canv.setFont("Lato-Black", 92); canv.translate(w/2, h/2); canv.rotate(32)
        canv.drawCentredString(0, -30, "SAMPLE"); canv.restoreState()
        canv.saveState()
        canv.setFillColor(colors.HexColor(TEAL)); canv.rect(0, h-10, w, 10, stroke=0, fill=1)
        canv.setFont("Lato-Bold", 8); canv.setFillColor(colors.HexColor(TEAL))
        canv.drawString(40, h-30, title.upper())
        canv.setFillColor(colors.HexColor(GREY)); canv.setFont("Lato", 8)
        canv.drawRightString(w-40, h-30, AUTHOR)
        canv.setStrokeColor(colors.HexColor(RULE)); canv.setLineWidth(0.6); canv.line(40, 42, w-40, 42)
        canv.setFont("Lato-Bold", 8); canv.setFillColor(colors.HexColor(TEAL))
        canv.drawString(40, 29, WATERMARK.upper())
        canv.setFont("Lato", 8); canv.setFillColor(colors.HexColor(GREY))
        canv.drawRightString(w-40, 29, f"Page {doc.page}")
        canv.restoreState()
    return _draw

def rl_table(data, col_widths, header=True, zebra=True, extra=None, font_size=8.4):
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    st = [("FONTNAME",(0,0),(-1,-1),"Lato"),("FONTSIZE",(0,0),(-1,-1),font_size),
          ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor(INK)),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
          ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
          ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
          ("LINEBELOW",(0,0),(-1,-1),0.4,colors.HexColor(RULE))]
    if header:
        st += [("BACKGROUND",(0,0),(-1,0),colors.HexColor(TEAL)),("TEXTCOLOR",(0,0),(-1,0),colors.white),
               ("FONTNAME",(0,0),(-1,0),"Lato-Bold")]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == 0: st.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor(TEAL_XXL)))
    if extra: st += extra
    t.setStyle(TableStyle(st)); return t
