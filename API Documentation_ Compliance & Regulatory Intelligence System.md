# API Documentation: Compliance & Regulatory Intelligence System

**Version:** 1.0  
**Date:** 2026-01-31

---

## 1. Introduction

This document provides a complete reference for the API of the Compliance & Regulatory Intelligence System. The API is built using FastAPI and provides REST endpoints for document submission, review, and retrieval of compliance reports.

### 1.1. Base URL

- **Production:** `https://api.yourdomain.com/v1`
- **Development:** `http://localhost:8000/api/v1`

### 1.2. Authentication

All endpoints are secured using JWT. A valid `Authorization` header with a Bearer token is required.

```http
Authorization: Bearer <your_jwt_token>
```

---

## 2. REST API Endpoints

### 2.1. Documents

#### `POST /documents/upload`

Uploads a new document for compliance review.

- **Request:** `multipart/form-data` with a file field named `file`.
- **Response (202 Accepted):**

```json
{
  "message": "Document uploaded and review process initiated.",
  "document_id": "doc_abc123",
  "review_id": "review_xyz789"
}
```

### 2.2. Reviews

#### `GET /reviews/{review_id}`

Retrieves the status and results of a compliance review.

- **Path Parameters:**
    - `review_id` (string, required): The ID of the review.
- **Response (200 OK):**

```json
{
  "review_id": "review_xyz789",
  "document_id": "doc_abc123",
  "status": "Complete",
  "compliance_score": 32,
  "violations": [
    {
      "regulation": "FINRA Rule 2210(d)(1)(A)",
      "severity": "Critical",
      "explanation": "Financial services firms cannot guarantee investment returns."
    }
  ],
  "corrections": [
    {
      "original_text": "Guaranteed returns of 15% annually!",
      "corrected_text": "Target annual returns of 10-15%."
    }
  ]
}
```

#### `GET /reviews`

Retrieves a list of all compliance reviews.

- **Query Parameters:**
    - `limit` (int, optional): Number of reviews to return. Defaults to 100.
- **Response (200 OK):**

```json
{
  "reviews": [
    {
      "review_id": "review_xyz789",
      "document_id": "doc_abc123",
      "status": "Complete",
      "compliance_score": 32
    }
  ]
}
```

### 2.3. Reports

#### `GET /reports/{review_id}/audit-trail`

Downloads the complete audit trail for a review.

- **Response (200 OK):** A JSON file with the detailed audit log.

#### `GET /reports/{review_id}/annotated-pdf`

Downloads the original document with all violations and corrections annotated.

- **Response (200 OK):** A PDF file.

---

## 3. API Usage Example

1.  **Client:** Authenticates and obtains a JWT.
2.  **Client:** Uploads a document using `POST /documents/upload`.
3.  **Client:** Polls the `GET /reviews/{review_id}` endpoint until the `status` is `Complete`.
4.  **Client:** Retrieves the full review results from `GET /reviews/{review_id}`.
5.  **Client:** Can download the audit trail or annotated PDF using the `/reports` endpoints.
