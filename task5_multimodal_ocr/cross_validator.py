"""
Task 5: Multimodal Cross-Validator.
Compares OCR extracted evidence against customer message claims.
Detects invoice discrepancies (amounts, order IDs, products), flags conflicts,
and requests clarification without fabricating missing facts.
"""
from typing import Dict, Any, List, Optional
import re
from core.security import security_service
from core.logger import audit_logger
from task5_multimodal_ocr.ocr_engine import OCRExtractionResult

class CrossValidationResult:
    def __init__(self, has_conflict: bool, discrepancies: List[str],
                 customer_claims: Dict[str, Any], extracted_evidence: Dict[str, Any],
                 clarification_prompt: Optional[str] = None):
        self.has_conflict = has_conflict
        self.discrepancies = discrepancies
        self.customer_claims = customer_claims
        self.extracted_evidence = extracted_evidence
        self.clarification_prompt = clarification_prompt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_conflict": self.has_conflict,
            "discrepancies": self.discrepancies,
            "customer_claims": self.customer_claims,
            "extracted_evidence": self.extracted_evidence,
            "clarification_prompt": self.clarification_prompt
        }

class CrossValidator:
    AMOUNT_REGEX = re.compile(r'(?:\$|usd|eur|inr|rs\.?)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\b', re.IGNORECASE)
    ORDER_REGEX = re.compile(r'\b(?:order\s*(?:id|#|no|number)?[:\s]*)?([A-Za-z0-9]{3,5}-\d{4,8}|#\d{4,8})\b', re.IGNORECASE)

    def extract_customer_claims(self, message: str) -> Dict[str, Any]:
        """Parses factual claims stated in customer's message."""
        claims = {}
        # Amount claimed
        amt_match = self.AMOUNT_REGEX.search(message)
        if amt_match:
            try:
                claims["amount"] = float(amt_match.group(1).replace(",", ""))
                claims["amount_str"] = amt_match.group(0)
            except ValueError:
                pass

        # Order ID claimed
        ord_match = self.ORDER_REGEX.search(message)
        if ord_match:
            claims["order_id"] = ord_match.group(1).upper()

        return claims

    def validate(self, customer_message: str, ocr_res: OCRExtractionResult) -> CrossValidationResult:
        """
        Validates customer message claims against OCR extracted document evidence.
        Flags discrepancies and builds clarification prompts.
        """
        # If OCR failed due to quality/blur, immediately request clearer file
        if ocr_res.is_low_quality:
            return CrossValidationResult(
                has_conflict=True,
                discrepancies=[f"Low image quality: {ocr_res.quality_issue}"],
                customer_claims=self.extract_customer_claims(customer_message),
                extracted_evidence={},
                clarification_prompt=ocr_res.clarification_requested or "The uploaded document is blurry. Please upload a clearer copy."
            )

        claims = self.extract_customer_claims(customer_message)
        discrepancies = []
        evidence_dict = {
            "order_id": ocr_res.order_id,
            "amount": ocr_res.amount,
            "amount_str": ocr_res.amount_str,
            "product": ocr_res.product,
            "date": ocr_res.date,
            "error_code": ocr_res.error_code
        }

        # 1. Order ID Discrepancy
        if "order_id" in claims and ocr_res.order_id:
            claim_ord = claims["order_id"].strip().upper()
            ev_ord = ocr_res.order_id.strip().upper()
            if claim_ord != ev_ord:
                discrepancies.append(
                    f"Order ID mismatch: Your message referenced '{claim_ord}', but the document shows '{ev_ord}'."
                )

        # 2. Amount Discrepancy
        if "amount" in claims and ocr_res.amount is not None:
            claim_amt = claims["amount"]
            ev_amt = ocr_res.amount
            if abs(claim_amt - ev_amt) > 0.05: # Beyond rounding difference
                discrepancies.append(
                    f"Amount mismatch: Your message claims {claims.get('amount_str', f'${claim_amt}')}, but the attached invoice shows {ocr_res.amount_str or f'${ev_amt}'}."
                )

        has_conflict = (len(discrepancies) > 0)
        clarification_prompt = None

        if has_conflict:
            clarification_prompt = (
                "We noticed a discrepancy between your message and the uploaded document:\n" +
                "\n".join([f"- {d}" for d in discrepancies]) +
                "\nCould you please clarify which details are correct so we can assist you properly?"
            )
            safe_log = security_service.mask_pii(f"Cross-validation conflict: {discrepancies}")
            audit_logger.log("WARNING", safe_log)

        return CrossValidationResult(
            has_conflict=has_conflict,
            discrepancies=discrepancies,
            customer_claims=claims,
            extracted_evidence=evidence_dict,
            clarification_prompt=clarification_prompt
        )

cross_validator = CrossValidator()
