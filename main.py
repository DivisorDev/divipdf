from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid, io, fitz, os
from pathlib import Path
from PIL import Image
from rembg import remove
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from pdf2docx import Converter
from docx2pdf import convert as word_to_pdf_convert

app = FastAPI(title="DiviPDF Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

BASE_PATH = Path(__file__).resolve().parent
UPLOADS, OUTPUTS = BASE_PATH / "uploads", BASE_PATH / "outputs"
UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

# ---------- PDF Tools ----------
@app.post("/pdf-to-word/")
async def pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")
    pdf = UPLOADS / f"{uuid.uuid4()}.pdf"
    doc = OUTPUTS / f"{uuid.uuid4()}.docx"
    with open(pdf, "wb") as f: f.write(await file.read())
    cv = Converter(str(pdf))
    cv.convert(str(doc))
    cv.close()
    pdf.unlink(missing_ok=True)
    return FileResponse(doc, filename=f"{Path(file.filename).stem}.docx")

@app.post("/word-to-pdf/")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith((".docx", ".doc")):
        raise HTTPException(400, "Only Word file allowed")
    input_path = UPLOADS / f"{uuid.uuid4()}.docx"
    output_path = OUTPUTS / f"{uuid.uuid4()}.pdf"
    with open(input_path, "wb") as f: f.write(await file.read())
    word_to_pdf_convert(str(input_path), str(output_path))
    input_path.unlink(missing_ok=True)
    return FileResponse(output_path, filename=f"{Path(file.filename).stem}.pdf")

@app.post("/merge-pdf/")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(400, "Upload at least 2 PDFs")
    merger = PdfMerger()
    temp = []
    for f in files:
        tmp = UPLOADS / f"{uuid.uuid4()}.pdf"
        with open(tmp, "wb") as out: out.write(await f.read())
        merger.append(str(tmp)); temp.append(tmp)
    merged = OUTPUTS / f"{uuid.uuid4()}_merged.pdf"
    merger.write(merged); merger.close()
    for t in temp: t.unlink(missing_ok=True)
    return FileResponse(merged, filename="merged.pdf")

@app.post("/compress-pdf/")
async def compress_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Upload PDF only")
    pdf = UPLOADS / f"{uuid.uuid4()}.pdf"
    out = OUTPUTS / f"{uuid.uuid4()}_compressed.pdf"
    with open(pdf, "wb") as f: f.write(await file.read())
    reader = PdfReader(str(pdf)); writer = PdfWriter()
    for p in reader.pages: p.compress_content_streams(); writer.add_page(p)
    with open(out, "wb") as f: writer.write(f)
    pdf.unlink(missing_ok=True)
    return FileResponse(out, filename=f"{Path(file.filename).stem}_compressed.pdf")

# ---------- Image Tools ----------
@app.post("/image-to-pdf/")
async def image_to_pdf(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read()))
    if img.mode != "RGB": img = img.convert("RGB")
    out = OUTPUTS / f"{uuid.uuid4()}.pdf"
    img.save(out, "PDF")
    return FileResponse(out, filename=f"{Path(file.filename).stem}.pdf")

@app.post("/convert-image-format/")
async def convert_image_format(file: UploadFile = File(...), format: str = "PNG"):
    img = Image.open(io.BytesIO(await file.read()))
    if format.lower() == "jpeg": img = img.convert("RGB")
    out = OUTPUTS / f"{uuid.uuid4()}.{format.lower()}"
    img.save(out, format.upper())
    return FileResponse(out, filename=f"{Path(file.filename).stem}.{format.lower()}")

@app.post("/image-compress/")
async def compress_image(file: UploadFile = File(...), quality: int = 85):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    out = OUTPUTS / f"{uuid.uuid4()}.jpg"
    img.save(out, "JPEG", optimize=True, quality=quality)
    return FileResponse(out, filename=f"{Path(file.filename).stem}_compressed.jpg")

@app.post("/image-resize/")
async def resize_image(file: UploadFile = File(...), width: int = 800, height: int = 600):
    img = Image.open(io.BytesIO(await file.read())).resize((width, height))
    out = OUTPUTS / f"{uuid.uuid4()}_resized.png"
    img.save(out, "PNG")
    return FileResponse(out, filename=f"{Path(file.filename).stem}_resized.png")

@app.post("/remove-bg/")
async def remove_bg(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read()))
    result = remove(img)
    out = OUTPUTS / f"{uuid.uuid4()}_nobg.png"
    result.save(out)
    return FileResponse(out, filename=f"{Path(file.filename).stem}_nobg.png")

@app.post("/remove-watermark/")
async def remove_watermark(file: UploadFile = File(...)):
    pdf = UPLOADS / f"{uuid.uuid4()}.pdf"
    out = OUTPUTS / f"{uuid.uuid4()}_clean.pdf"
    with open(pdf, "wb") as f: f.write(await file.read())
    doc = fitz.open(str(pdf))
    for page in doc:
        for annot in page.annots() or []: page.delete_annot(annot)
    doc.save(out); doc.close(); pdf.unlink(missing_ok=True)
    return FileResponse(out, filename=f"{Path(file.filename).stem}_clean.pdf")

@app.get("/")
def root():
    return {"message": "DiviPDF Backend running!", "docs": "/docs"}
