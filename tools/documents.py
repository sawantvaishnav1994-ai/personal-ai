from __future__ import annotations
import re
from pathlib import Path
from tools.registry import Tool,Risk

def _safe_name(value:str,extension:str)->str:
    name=Path(str(value or 'untitled')).name
    stem=Path(name).stem
    stem=re.sub(r'[^A-Za-z0-9._ -]+','_',stem).strip(' .')[:120] or 'untitled'
    return stem+extension

def register(reg,workspace_root:Path|None=None):
    root=Path(workspace_root or (Path.home()/'.personal_ai'/'workspace')).expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    def path_for(p,extension):
        path=(root/_safe_name(p.get('name') or p.get('path') or 'untitled',extension)).resolve()
        if root not in path.parents:raise ValueError('output must remain inside Personal AI workspace')
        return path
    def docx_create(p):
        from docx import Document
        path=path_for(p,'.docx');doc=Document()
        if p.get('title'):doc.add_heading(str(p['title']),0)
        for section in p.get('sections',[]):
            if section.get('heading'):doc.add_heading(str(section['heading']),level=min(max(int(section.get('level',1)),1),3))
            for para in section.get('paragraphs',[]):doc.add_paragraph(str(para))
        for para in p.get('paragraphs',[]):doc.add_paragraph(str(para))
        doc.save(path);return {'ok':True,'path':str(path),'workspace':str(root)}
    def xlsx_create(p):
        from openpyxl import Workbook
        path=path_for(p,'.xlsx');wb=Workbook();ws=wb.active;ws.title=str(p.get('sheet','Sheet1'))[:31]
        for row in p.get('rows',[]):ws.append(list(row))
        for sheet in p.get('sheets',[]):
            target=wb.create_sheet(str(sheet.get('name','Sheet'))[:31]);[target.append(list(row)) for row in sheet.get('rows',[])]
        wb.save(path);return {'ok':True,'path':str(path),'workspace':str(root)}
    def pptx_create(p):
        from pptx import Presentation
        path=path_for(p,'.pptx');prs=Presentation()
        for item in p.get('slides',[]):
            slide=prs.slides.add_slide(prs.slide_layouts[1]);slide.shapes.title.text=str(item.get('title',''));slide.placeholders[1].text='\n'.join(map(str,item.get('bullets',[]))) if item.get('bullets') else str(item.get('body',''))
        prs.save(path);return {'ok':True,'path':str(path),'workspace':str(root)}
    def pdf_create(p):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        path=path_for(p,'.pdf');styles=getSampleStyleSheet();story=[]
        if p.get('title'):story.extend([Paragraph(str(p['title']),styles['Title']),Spacer(1,12)])
        for section in p.get('sections',[]):
            if section.get('heading'):story.extend([Paragraph(str(section['heading']),styles['Heading2']),Spacer(1,6)])
            for para in section.get('paragraphs',[]):story.extend([Paragraph(str(para),styles['BodyText']),Spacer(1,7)])
        for para in p.get('paragraphs',[]):story.extend([Paragraph(str(para),styles['BodyText']),Spacer(1,7)])
        SimpleDocTemplate(str(path),pagesize=A4,title=str(p.get('title','Personal AI document'))).build(story);return {'ok':True,'path':str(path),'workspace':str(root)}
    def list_workspace(p):
        return {'workspace':str(root),'files':[{'name':x.name,'size':x.stat().st_size,'modified':x.stat().st_mtime} for x in sorted(root.iterdir(),key=lambda x:x.stat().st_mtime,reverse=True) if x.is_file()][:100]}
    reg.register(Tool('create_docx','Create a Word document inside the protected Personal AI workspace; params: name,title,paragraphs,sections',docx_create,Risk.REVERSIBLE))
    reg.register(Tool('create_xlsx','Create a spreadsheet inside the protected Personal AI workspace; params: name,rows,sheets',xlsx_create,Risk.REVERSIBLE))
    reg.register(Tool('create_pptx','Create a presentation inside the protected Personal AI workspace; params: name,slides',pptx_create,Risk.REVERSIBLE))
    reg.register(Tool('create_pdf','Create a PDF inside the protected Personal AI workspace; params: name,title,paragraphs,sections',pdf_create,Risk.REVERSIBLE))
    reg.register(Tool('workspace_files','List generated Personal AI workspace files',list_workspace,Risk.READ_ONLY))
