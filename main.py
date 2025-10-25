from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from pathlib import Path

# PDF libraries
try:
    from pdf2docx import Converter
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
except ImportError:
    pass

# Image libraries
try:
    from PIL import Image
    import io
except ImportError:
    pass

app = FastAPI(title="DiviPDF Toolkit API")

# CORS - Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/")
def root():
    return {
        "message": "DiviPDF Toolkit API is running!",
        "docs": "/docs",
        "tools": [
            "pdf-to-word", "word-to-pdf", "merge-pdf", "compress-pdf",
            "image-compress", "image-resize", "image-to-pdf", "convert-image-format"
        ]
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "DiviPDF API"}


# ========== PDF TOOLS ==========

@app.post("/pdf-to-word/")
async def pdf_to_word(file: UploadFile = File(...)):
    """Convert PDF to Word (.docx)"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files allowed")
    
    input_path = UPLOAD_DIR / f"{uuid.uuid4()}.pdf"
    output_path = OUTPUT_DIR / f"{uuid.uuid4()}.docx"
    
    with open(input_path, "wb") as f:
        f.write(await file.read())
    
    try:
        cv = Converter(str(input_path))
        cv.convert(str(output_path))
        cv.close()
    except Exception as e:
        raise HTTPException(500, f"Conversion failed: {str(e)}")
    finally:
        input_path.unlink(missing_ok=True)
    
    return FileResponse(
        output_path,
        filename=f"{Path(file.filename).stem}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.post("/merge-pdf/")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    """Merge multiple PDFs"""
    if len(files) < 2:
        raise HTTPException(400, "At least 2 PDF files required")
    
    merger = PdfMerger()
    temp_files = []
    
    try:
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(400, "All files must be PDFs")
            
            temp_path = UPLOAD_DIR / f"{uuid.uuid4()}.pdf"
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            
            merger.append(str(temp_path))
            temp_files.append(temp_path)
        
        output_path = OUTPUT_DIR / f"{uuid.uuid4()}_merged.pdf"
        merger.write(str(output_path))
        merger.close()
        
    finally:
        for temp in temp_files:
            temp.unlink(missing_ok=True)
    
    return FileResponse(output_path, filename="merged.pdf", media_type="application/pdf")


@app.post("/compress-pdf/")
async def compress_pdf(file: UploadFile = File(...)):
    """Compress PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files allowed")
    
    input_path = UPLOAD_DIR / f"{uuid.uuid4()}.pdf"
    output_path = OUTPUT_DIR / f"{uuid.uuid4()}_compressed.pdf"
    
    with open(input_path, "wb") as f:
        f.write(await file.read())
    
    try:
        reader = PdfReader(str(input_path))
        writer = PdfWriter()
        
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise HTTPException(500, f"Compression failed: {str(e)}")
    finally:
        input_path.unlink(missing_ok=True)
    
    return FileResponse(
        output_path,
        filename=f"{Path(file.filename).stem}_compressed.pdf",
        media_type="application/pdf"
    )


# ========== IMAGE TOOLS ==========

@app.post("/image-compress/")
async def compress_image(file: UploadFile = File(...), quality: int = 85):
    """Compress JPG/PNG/WEBP images"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "Only image files allowed")
    
    input_bytes = await file.read()
    img = Image.open(io.BytesIO(input_bytes))
    
    output_path = OUTPUT_DIR / f"{uuid.uuid4()}.jpg"
    img = img.convert('RGB')
    img.save(output_path, "JPEG", quality=quality, optimize=True)
    
    return FileResponse(
        output_path,
        filename=f"{Path(file.filename).stem}_compressed.jpg",
        media_type="image/jpeg"
    )


@app.post("/image-resize/")
async def resize_image(file: UploadFile = File(...), width: int = 800, height: int = 600):
    """Resize image to custom dimensions"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "Only image files allowed")
    
    input_bytes = await file.read()
    img = Image.open(io.BytesIO(input_bytes))
    
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    output_path = OUTPUT_DIR / f"{uuid.uuid4()}.png"
    img.save(output_path, "PNG")
    
    return FileResponse(
        output_path,
        filename=f"{Path(file.filename).stem}_resized.png",
        media_type="image/png"
    )


@app.post("/image-to-pdf/")
async def image_to_pdf(file: UploadFile = File(...)):
    """Convert image to PDF"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "Only image files allowed")
    
    input_bytes = await file.read()
    img = Image.open(io.BytesIO(input_bytes))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    output_path = OUTPUT_DIR / f"{uuid.uuid4()}.pdf"
    img.save(output_path, "PDF")
    
    return FileResponse(
        output_path,
        filename=f"{Path(file.filename).stem}.pdf",
        media_type="application/pdf"
    )


@app.post("/convert-image-format/")
async def convert_image_format(file: UploadFile = File(...), format: str = "PNG"):
    """Convert image format (JPEG/PNG/WEBP)"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "Only image files allowed")
    
    format = format.upper()
    if format not in ['JPEG', 'PNG', 'WEBP']:
        raise HTTPException(400, "Format must be JPEG, PNG, or WEBP")
    
    input_bytes = await file.read()
    img = Image.open(io.BytesIO(input_bytes))
    
    if format == 'JPEG' and img.mode != 'RGB':
        img = img.convert('RGB')
    
    output_path = OUTPUT_DIR / f"{uuid.uuid4()}.{format.lower()}"
    img.save(output_path, format)
    
    return FileResponse(
        output_path,
        filename=f"{Path(file.filename).stem}.{format.lower()}",
        media_type=f"image/{format.lower()}"
    )
