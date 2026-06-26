"""AWS Textract service for document text extraction."""
import asyncio
from typing import Dict, List, Optional, Any
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("textract_service")


class TextractService:
    """AWS Textract service for OCR and text extraction."""
    
    def __init__(self):
        self.config = Config(
            region_name=settings.AWS_REGION,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.client = boto3.client(
            'textract',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=self.config
        )
        
        self.enabled = settings.AWS_TEXTRACT_ENABLED
    
    async def extract_text_from_bytes(
        self,
        document_bytes: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Extract text from document bytes using Textract or direct read for text files.
        
        Args:
            document_bytes: Document content as bytes
            filename: Original filename for logging
            
        Returns:
            Dict containing extracted text and metadata
        """
        # For plain text files, just decode directly - no need for Textract
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext in ('txt', 'text', 'md', 'csv', 'json', 'xml', 'html'):
            try:
                text = document_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text = document_bytes.decode('latin-1')
            
            logger.info(
                "text_extracted_direct",
                filename=filename,
                text_length=len(text)
            )
            return {
                "text": text,
                "pages": [{"page": 1, "text": text}],
                "confidence": 100.0
            }
        
        if not self.enabled:
            logger.warning("Textract is disabled, attempting direct text decode")
            try:
                text = document_bytes.decode('utf-8')
                return {"text": text, "pages": [], "confidence": 50.0}
            except:
                return {"text": "", "pages": [], "confidence": 0}
        
        try:
            loop = asyncio.get_event_loop()
            
            # Call Textract detect_document_text
            response = await loop.run_in_executor(
                None,
                lambda: self.client.detect_document_text(
                    Document={'Bytes': document_bytes}
                )
            )
            
            # Parse response
            result = self._parse_textract_response(response)
            
            logger.info(
                "text_extracted",
                filename=filename,
                num_blocks=len(response.get('Blocks', [])),
                confidence=result['confidence']
            )
            
            return result
            
        except ClientError as e:
            logger.error(f"Textract extraction failed: {e}, trying direct decode")
            # Fallback - try to decode as text
            try:
                text = document_bytes.decode('utf-8')
                return {"text": text, "pages": [], "confidence": 50.0}
            except:
                raise
    
    async def extract_text_from_s3(
        self,
        s3_bucket: str,
        s3_key: str
    ) -> Dict[str, Any]:
        """
        Extract text from a document stored in S3.
        
        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 object key
            
        Returns:
            Dict containing extracted text and metadata
        """
        if not self.enabled:
            logger.warning("Textract is disabled, returning empty result")
            return {"text": "", "pages": [], "confidence": 0}
        
        try:
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.detect_document_text(
                    Document={
                        'S3Object': {
                            'Bucket': s3_bucket,
                            'Name': s3_key
                        }
                    }
                )
            )
            
            result = self._parse_textract_response(response)
            
            logger.info(
                "text_extracted_from_s3",
                s3_key=s3_key,
                num_blocks=len(response.get('Blocks', [])),
                confidence=result['confidence']
            )
            
            return result
            
        except ClientError as e:
            logger.error(f"Textract S3 extraction failed: {e}")
            raise
    
    async def analyze_document(
        self,
        document_bytes: bytes,
        feature_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document with advanced features (forms, tables).
        
        Args:
            document_bytes: Document content as bytes
            feature_types: List of features to analyze ['TABLES', 'FORMS']
            
        Returns:
            Dict containing analyzed content
        """
        if not self.enabled:
            return {"text": "", "tables": [], "forms": [], "confidence": 0}
        
        feature_types = feature_types or ['TABLES', 'FORMS']
        
        try:
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.analyze_document(
                    Document={'Bytes': document_bytes},
                    FeatureTypes=feature_types
                )
            )
            
            result = self._parse_analyze_response(response)
            
            logger.info(
                "document_analyzed",
                num_tables=len(result.get('tables', [])),
                num_forms=len(result.get('forms', []))
            )
            
            return result
            
        except ClientError as e:
            logger.error(f"Textract analysis failed: {e}")
            raise
    
    def _parse_textract_response(self, response: Dict) -> Dict[str, Any]:
        """Parse Textract detect_document_text response."""
        blocks = response.get('Blocks', [])
        
        # Extract text from LINE blocks
        lines = []
        total_confidence = 0
        line_count = 0
        
        page_texts = {}
        
        for block in blocks:
            if block['BlockType'] == 'LINE':
                text = block.get('Text', '')
                confidence = block.get('Confidence', 0)
                page = block.get('Page', 1)
                
                lines.append({
                    'text': text,
                    'confidence': confidence,
                    'page': page,
                    'geometry': block.get('Geometry', {})
                })
                
                if page not in page_texts:
                    page_texts[page] = []
                page_texts[page].append(text)
                
                total_confidence += confidence
                line_count += 1
        
        # Build full text
        full_text = '\n'.join([line['text'] for line in lines])
        
        # Build pages
        pages = []
        for page_num in sorted(page_texts.keys()):
            pages.append({
                'page_number': page_num,
                'text': '\n'.join(page_texts[page_num])
            })
        
        avg_confidence = total_confidence / line_count if line_count > 0 else 0
        
        return {
            'text': full_text,
            'lines': lines,
            'pages': pages,
            'confidence': round(avg_confidence, 2),
            'total_lines': line_count
        }
    
    def _parse_analyze_response(self, response: Dict) -> Dict[str, Any]:
        """Parse Textract analyze_document response."""
        blocks = response.get('Blocks', [])
        
        # Build block map for relationship lookup
        block_map = {block['Id']: block for block in blocks}
        
        # Extract tables
        tables = []
        for block in blocks:
            if block['BlockType'] == 'TABLE':
                table = self._extract_table(block, block_map)
                tables.append(table)
        
        # Extract forms (key-value pairs)
        forms = []
        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                form_field = self._extract_form_field(block, block_map)
                if form_field:
                    forms.append(form_field)
        
        # Also get text
        text_result = self._parse_textract_response(response)
        
        return {
            **text_result,
            'tables': tables,
            'forms': forms
        }
    
    def _extract_table(self, table_block: Dict, block_map: Dict) -> Dict:
        """Extract table data from Textract blocks."""
        rows = {}
        
        for relationship in table_block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for cell_id in relationship['Ids']:
                    cell = block_map.get(cell_id)
                    if cell and cell['BlockType'] == 'CELL':
                        row_idx = cell.get('RowIndex', 0)
                        col_idx = cell.get('ColumnIndex', 0)
                        
                        # Get cell text
                        cell_text = self._get_text_from_block(cell, block_map)
                        
                        if row_idx not in rows:
                            rows[row_idx] = {}
                        rows[row_idx][col_idx] = cell_text
        
        # Convert to list of lists
        table_data = []
        for row_idx in sorted(rows.keys()):
            row = rows[row_idx]
            row_data = [row.get(col_idx, '') for col_idx in sorted(row.keys())]
            table_data.append(row_data)
        
        return {
            'rows': table_data,
            'row_count': len(table_data),
            'col_count': len(table_data[0]) if table_data else 0
        }
    
    def _extract_form_field(self, key_block: Dict, block_map: Dict) -> Optional[Dict]:
        """Extract key-value pair from form."""
        key_text = self._get_text_from_block(key_block, block_map)
        value_text = ''
        
        for relationship in key_block.get('Relationships', []):
            if relationship['Type'] == 'VALUE':
                for value_id in relationship['Ids']:
                    value_block = block_map.get(value_id)
                    if value_block:
                        value_text = self._get_text_from_block(value_block, block_map)
        
        if key_text:
            return {
                'key': key_text,
                'value': value_text,
                'confidence': key_block.get('Confidence', 0)
            }
        return None
    
    def _get_text_from_block(self, block: Dict, block_map: Dict) -> str:
        """Get text content from a block, following CHILD relationships."""
        text_parts = []
        
        for relationship in block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child = block_map.get(child_id)
                    if child and child['BlockType'] == 'WORD':
                        text_parts.append(child.get('Text', ''))
        
        return ' '.join(text_parts)


# Singleton instance
textract_service = TextractService()
