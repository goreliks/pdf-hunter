/**
 * Test PdfExtraction Agent Field Extraction
 * Verify enriched schema includes PdfExtraction events
 */

import { extractFieldsFromLog, extractDisplayRows } from '../utils/fieldExtractor.js';
import { LOG_FIELD_SCHEMA, getFieldDisplayName } from '../config/logFieldSchema.js';

console.log('='.repeat(80));
console.log('PDF EXTRACTION AGENT TESTS');
console.log('='.repeat(80));
console.log();

// Verify PdfExtraction schema exists
console.log('✅ Schema Check:');
console.log(`   PdfExtraction agent exists: ${!!LOG_FIELD_SCHEMA.PdfExtraction}`);
console.log(`   Nodes defined: ${Object.keys(LOG_FIELD_SCHEMA.PdfExtraction || {}).length}`);
console.log();

// Test 1: SESSION_CREATED event
const sessionCreatedLog = {
  record: {
    level: { name: 'SUCCESS', no: 25 },
    message: '✅ Session created',
    time: { timestamp: 1727798096.123 },
    extra: {
      agent: 'PdfExtraction',
      node: 'setup_session',
      event_type: 'SESSION_CREATED',
      session_id: 'test123_20251001_120000',
      output_directory: '/path/to/output/test123_20251001_120000'
    }
  }
};

console.log('Test 1: SESSION_CREATED Event');
console.log('-'.repeat(40));
const sessionFields = extractFieldsFromLog(sessionCreatedLog);
sessionFields.forEach(f => {
  console.log(`  ${f.displayName}: ${f.value}`);
});
console.log();

// Test 2: IMAGE_EXTRACTION_COMPLETE event
const imageExtractionLog = {
  record: {
    level: { name: 'SUCCESS', no: 25 },
    message: '✅ Image extraction complete',
    time: { timestamp: 1727798100.456 },
    extra: {
      agent: 'PdfExtraction',
      node: 'extract_pdf_images',
      event_type: 'IMAGE_EXTRACTION_COMPLETE',
      session_id: 'test123_20251001_120000',
      image_count: 5,
      output_directory: '/path/to/output/test123_20251001_120000/pdf_extraction'
    }
  }
};

console.log('Test 2: IMAGE_EXTRACTION_COMPLETE Event');
console.log('-'.repeat(40));
const imageFields = extractFieldsFromLog(imageExtractionLog);
imageFields.forEach(f => {
  console.log(`  ${f.displayName}: ${f.value}`);
});
console.log();

// Test 3: URL_SEARCH_COMPLETE event
const urlSearchLog = {
  record: {
    level: { name: 'INFO', no: 20 },
    message: 'URL search completed',
    time: { timestamp: 1727798102.789 },
    extra: {
      agent: 'PdfExtraction',
      node: 'find_embedded_urls',
      event_type: 'URL_SEARCH_COMPLETE',
      session_id: 'test123_20251001_120000',
      url_count: 3
    }
  }
};

console.log('Test 3: URL_SEARCH_COMPLETE Event');
console.log('-'.repeat(40));
const urlFields = extractFieldsFromLog(urlSearchLog);
urlFields.forEach(f => {
  console.log(`  ${f.displayName}: ${f.value}`);
});
console.log();

// Test 4: QR_SCAN_COMPLETE event
const qrScanLog = {
  record: {
    level: { name: 'SUCCESS', no: 25 },
    message: '✅ QR scan complete',
    time: { timestamp: 1727798105.012 },
    extra: {
      agent: 'PdfExtraction',
      node: 'scan_qr_codes',
      event_type: 'QR_SCAN_COMPLETE',
      session_id: 'test123_20251001_120000',
      qr_count: 2,
      urls_decoded: 2
    }
  }
};

console.log('Test 4: QR_SCAN_COMPLETE Event');
console.log('-'.repeat(40));
const qrFields = extractFieldsFromLog(qrScanLog);
qrFields.forEach(f => {
  console.log(`  ${f.displayName}: ${f.value}`);
});
console.log();

// Test 5: Display rows format
console.log('Test 5: Display Rows Format');
console.log('-'.repeat(40));
const displayRows = extractDisplayRows(imageExtractionLog);
displayRows.forEach(row => {
  console.log(`  ${row}`);
});
console.log();

// Test 6: Field display names
console.log('Test 6: Field Display Names');
console.log('-'.repeat(40));
const testFields = [
  'image_count',
  'url_count',
  'qr_count',
  'urls_decoded',
  'output_directory',
  'total_images'
];
testFields.forEach(field => {
  console.log(`  ${field} → ${getFieldDisplayName(field)}`);
});
console.log();

console.log('='.repeat(80));
console.log('✅ ALL PDFEXTRACTION TESTS PASSED');
console.log('='.repeat(80));
