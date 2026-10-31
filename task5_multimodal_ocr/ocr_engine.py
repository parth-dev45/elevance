"""
Task 5: Multimodal OCR & Document Analysis Engine.
Extracts order IDs, dates, amounts, products, and error codes from images and PDFs.
Detects low-quality/blurry images and requests clearer files without inventing values.
"""
import re
import os
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel
from PIL import Image, ImageFilter, ImageStat
from pypdf import PdfReader
from core.logger import audit_logger
from core.security import security_service

class OCRExtractionResult(BaseModel):
    is_success: bool = True
    order_id: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    amount_str: Optional[str] = None
    product: Optional[str] = None
    error_code: Optional[str] = None
    raw_text: str = ""
    is_low_quality: bool = False
    quality_issue: Optional[str] = None
    clarification_requested: Optional[str] = None

class OCREngine:
    ORDER_REGEX = re.compile(r'\b(?:order\s*(?:id|#|no|number)?[:\s]*)?([A-Z0-9]{3,5}-\d{4,8}|#\d{4,8})\b', re.IGNORECASE)
    AMOUNT_REGEX = re.compile(r'(?:\$|usd|eur|inr|rs\.?)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\b', re.IGNORECASE)
    DATE_REGEX = re.compile(r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b')
    ERROR_CODE_REGEX = re.compile(r'(?:error\s*(?:code)?|code|http\s*(?:status)?)[:\s]+([A-Za-z0-9_\-]+)|\b(ERR-[A-Za-z0-9_\-]+)\b', re.IGNORECASE)
    PRODUCT_KEYWORDS = ["laptop", "macbook", "phone", "iphone", "headphones", "keyboard", "monitor", "charger", "t-shirt", "watch", "camera"]

    def assess_image_quality(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Assesses image quality for blurriness, extreme low resolution, or degradation.
        Returns: (is_low_quality: bool, reason: Optional[str])
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width < 80 or height < 80:
                    return True, "Image resolution is too low (< 80x80px) to reliably extract text."

                # Convert to grayscale to test variance / blur
                gray = img.convert("L")
                stat = ImageStat.Stat(gray)
                variance = stat.var[0] if stat.var else 0.0

                # Low contrast / washed out image check
                if variance < 8.0:
                    return True, "Image contrast is severely washed out or blank."

                # Check edge contrast (Laplacian surrogate via FIND_EDGES)
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_stat = ImageStat.Stat(edges)
                edge_var = edge_stat.var[0] if edge_stat.var else 0.0
                if edge_var < 5.0 and (width * height > 5000):
                    return True, "Image appears severely blurry or unfocused."

        except Exception as e:
            return True, f"Corrupted image file: {str(e)}"

        return False, None

    def extract_from_pdf(self, pdf_path: str) -> str:
        """Extracts text content from PDF file."""
        text = ""
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            audit_logger.log("ERROR", f"PDF Extraction failure: {str(e)}")
        return text

    def extract_from_image(self, image_path: str) -> str:
        """
        Performs OCR on image. Uses pytesseract if available,
        with metadata / visual fallback.
        """
        try:
            import pytesseract
            img = Image.open(image_path)
            return pytesseract.image_to_string(img)
        except Exception:
            # Fallback: check file metadata or text comments in file
            try:
                with Image.open(image_path) as img:
                    info_text = str(img.info or "")
                    return info_text
            except Exception:
                return ""

    def process_file(self, file_path: str, simulated_ocr_text: Optional[str] = None) -> OCRExtractionResult:
        """
        Performs OCR analysis on invoice/screenshot/receipt/PDF.
        Never invents missing values.
        """
        if not os.path.exists(file_path) and not simulated_ocr_text:
            return OCRExtractionResult(is_success=False, raw_text="", quality_issue="File not found")

        ext = os.path.splitext(file_path)[1].lower()
        raw_text = ""

        # 1. Quality & Blur check for images
        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            is_low_quality, reason = self.assess_image_quality(file_path)
            if is_low_quality:
                audit_logger.log("WARNING", f"Low quality file rejected: {file_path}. Reason: {reason}")
                return OCRExtractionResult(
                    is_success=False,
                    is_low_quality=True,
                    quality_issue=reason,
                    clarification_requested="The uploaded image appears blurry or illegible. Could you please provide a clearer photo or PDF of your document?"
                )

        # 2. Extract text (PDF or Image)
        if simulated_ocr_text is not None:
            raw_text = simulated_ocr_text
        elif ext == ".pdf":
            raw_text = self.extract_from_pdf(file_path)
        else:
            raw_text = self.extract_from_image(file_path)

        # 3. Parse fields (never invent missing values)
        # Order ID
        order_id = None
        ord_match = self.ORDER_REGEX.search(raw_text)
        if ord_match:
            order_id = ord_match.group(1)

        # Amount
        amount = None
        amt_str = None
        amt_match = self.AMOUNT_REGEX.search(raw_text)
        if amt_match:
            amt_str = amt_match.group(0)
            try:
                amount = float(amt_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # Date
        extracted_date = None
        date_match = self.DATE_REGEX.search(raw_text)
        if date_match:
            extracted_date = date_match.group(1)

        # Error Code
        error_code = None
        err_match = self.ERROR_CODE_REGEX.search(raw_text)
        if err_match:
            val = err_match.group(1) or err_match.group(2)
            if val:
                error_code = val.strip()

        # Product
        product = None
        raw_lower = raw_text.lower()
        sorted_kw = sorted(self.PRODUCT_KEYWORDS, key=len, reverse=True)
        for kw in sorted_kw:
            if re.search(rf"\b{re.escape(kw)}\b", raw_lower):
                product = kw.title()
                break

        # Log extraction with PII masking
        safe_log = security_service.mask_pii(f"OCR extracted from {os.path.basename(file_path)}: Order={order_id}, Amount={amt_str}, Date={extracted_date}")
        audit_logger.log("INFO", safe_log)

        return OCRExtractionResult(
            is_success=True,
            order_id=order_id,
            date=extracted_date,
            amount=amount,
            amount_str=amt_str,
            product=product,
            error_code=error_code,
            raw_text=raw_text,
            is_low_quality=False
        )

ocr_engine = OCREngine()
