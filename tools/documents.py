from pathlib import Path
from tools.registry import Tool, Risk

def register(reg):
    def docx_create(p):
        from docx import Document
        path=Path(p["path"]).expanduser(); path.parent.mkdir(parents=True,exist_ok=True)
        doc=Document()
        if p.get("title"): doc.add_heading(str(p["title"]),0)
        for para in p.get("paragraphs",[]): doc.add_paragraph(str(para))
        doc.save(path); return {"ok":True,"path":str(path)}
    def xlsx_create(p):
        from openpyxl import Workbook
        path=Path(p["path"]).expanduser(); path.parent.mkdir(parents=True,exist_ok=True)
        wb=Workbook(); ws=wb.active
        for row in p.get("rows",[]): ws.append(list(row))
        wb.save(path); return {"ok":True,"path":str(path)}
    def pptx_create(p):
        from pptx import Presentation
        path=Path(p["path"]).expanduser(); path.parent.mkdir(parents=True,exist_ok=True)
        prs=Presentation()
        for item in p.get("slides",[]):
            slide=prs.slides.add_slide(prs.slide_layouts[1]); slide.shapes.title.text=str(item.get("title","")); slide.placeholders[1].text=str(item.get("body",""))
        prs.save(path); return {"ok":True,"path":str(path)}
    reg.register(Tool("create_docx","Create DOCX; params: path,title,paragraphs",docx_create,Risk.REVERSIBLE))
    reg.register(Tool("create_xlsx","Create XLSX; params: path,rows",xlsx_create,Risk.REVERSIBLE))
    reg.register(Tool("create_pptx","Create PPTX; params: path,slides",pptx_create,Risk.REVERSIBLE))
